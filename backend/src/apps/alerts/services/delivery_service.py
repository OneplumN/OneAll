from __future__ import annotations

import json
import logging
import os
import smtplib
import subprocess
import sys
import tempfile
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from typing import Mapping, Sequence

import requests
from django.conf import settings

from apps.core.outbound import validate_outbound_hook_url
from apps.alerts.models import AlertEvent
from apps.settings.models import AlertChannel, AlertTemplate
from apps.settings.services.template_renderer import AlertTemplateError, render_alert_template
from apps.settings.services.system_settings_service import get_system_settings
from apps.tools.models import CodeRepository, CodeRepositoryVersion

logger = logging.getLogger(__name__)
DEFAULT_SCRIPT_TIMEOUT_SECONDS = 15
MAX_SCRIPT_TIMEOUT_SECONDS = 300

DEFAULT_TEMPLATE_BODY = (
    "【${title}】\n"
    "状态：${status}\n"
    "时间：${timestamp}\n"
    "任务：${task_name}\n"
    "探针：${probe_name}\n"
    "详情：${message}\n"
    "${result_url}"
)


def deliver_alert_event(event: AlertEvent) -> list[str]:
    context = _build_template_context(event)
    requested_channels = context.get("alert_channels") or []
    channels = _resolve_channels(requested_channels)
    if not channels:
        raise RuntimeError("没有可用的告警通道")

    contacts = _resolve_contacts(context)
    succeeded: list[str] = []
    failures: list[str] = []

    for channel in channels:
        try:
            subject, body = _render_for_channel(channel.channel_type, context)
            _dispatch_to_channel(channel, subject, body, contacts, context)
        except Exception as exc:
            failures.append(f"{channel.channel_type}: {exc}")
            logger.exception("Failed to dispatch alert event %s via %s", event.id, channel.channel_type)
            continue
        succeeded.append(channel.channel_type)

    if not succeeded:
        raise RuntimeError("; ".join(failures) if failures else "告警发送失败")

    return succeeded


def _build_template_context(event: AlertEvent) -> dict[str, str | list[str]]:
    context = dict(event.context or {})
    result_url = str(context.get("result_url") or "")
    probe_name = str(context.get("probe_name") or "")
    task_name = (
        str(context.get("task_name") or "")
        or str(context.get("schedule_name") or "")
        or str(context.get("target") or "")
        or event.title
    )
    alert_channels_raw = context.get("alert_channels") or []
    if isinstance(alert_channels_raw, str):
        alert_channels = [alert_channels_raw]
    else:
        alert_channels = [str(item).strip() for item in alert_channels_raw if str(item).strip()]
    alert_contacts_raw = context.get("alert_contacts") or []
    if isinstance(alert_contacts_raw, str):
        alert_contacts = [alert_contacts_raw]
    else:
        alert_contacts = [str(item).strip() for item in alert_contacts_raw if str(item).strip()]

    return {
        "title": event.title,
        "severity": event.severity,
        "status": str(context.get("status") or event.status),
        "timestamp": str(context.get("timestamp") or event.created_at.isoformat()),
        "task_name": task_name,
        "probe_name": probe_name,
        "message": event.message,
        "result_url": result_url,
        "alert_channels": alert_channels,
        "alert_contacts": alert_contacts,
    }


def _resolve_channels(requested_channels: Sequence[str]) -> list[AlertChannel]:
    queryset = AlertChannel.objects.filter(enabled=True)
    if requested_channels:
        queryset = queryset.filter(channel_type__in=list(requested_channels))
    return list(queryset.order_by("channel_type"))


def _resolve_contacts(context: Mapping[str, object]) -> list[str]:
    raw_contacts = context.get("alert_contacts") or []
    if isinstance(raw_contacts, str):
        contacts = [raw_contacts]
    else:
        contacts = [str(item).strip() for item in raw_contacts if str(item).strip()]
    if contacts:
        return contacts

    defaults = get_system_settings().notification_channels or {}
    default_email = str(defaults.get("email") or "").strip()
    return [default_email] if default_email else []


def _render_for_channel(channel_type: str, context: Mapping[str, object]) -> tuple[str, str]:
    template = (
        AlertTemplate.objects.filter(channel_type=channel_type)
        .order_by("-is_default", "-updated_at")
        .first()
    )
    subject_template = template.subject if template and template.subject else str(context.get("title") or "")
    body_template = template.body if template and template.body else DEFAULT_TEMPLATE_BODY

    try:
        subject = render_alert_template(subject_template, context)
    except AlertTemplateError:
        subject = str(context.get("title") or "")

    try:
        body = render_alert_template(body_template, context)
    except AlertTemplateError:
        body = (
            f"{context.get('title', '')}\n"
            f"状态：{context.get('status', '')}\n"
            f"时间：{context.get('timestamp', '')}\n"
            f"任务：{context.get('task_name', '')}\n"
            f"探针：{context.get('probe_name', '')}\n"
            f"详情：{context.get('message', '')}\n"
            f"{context.get('result_url', '')}"
        )

    return subject or str(context.get("title") or ""), body


def _dispatch_to_channel(
    channel: AlertChannel,
    subject: str,
    body: str,
    contacts: Sequence[str],
    context: Mapping[str, object],
) -> None:
    channel_type = channel.channel_type
    if channel_type == "email":
        _send_email(channel, subject, body, contacts)
        return
    if channel_type == "wecom":
        _send_wecom(channel, subject, body, contacts)
        return
    if channel_type == "dingtalk":
        _send_dingtalk(channel, subject, body, contacts)
        return
    if channel_type == "lark":
        _send_lark(channel, subject, body)
        return
    if channel_type == "http":
        _send_http_callback(channel, subject, body, context)
        return
    if channel_type == "script":
        _send_script(channel, subject, body, contacts, context)
        return
    raise ValueError(f"暂不支持的告警通道: {channel_type}")


def _send_email(channel: AlertChannel, subject: str, body: str, contacts: Sequence[str]) -> None:
    if not contacts:
        raise ValueError("邮件通道缺少收件人")

    config = channel.config or {}
    host = config.get("smtp_host")
    port = int(config.get("smtp_port") or 25)
    use_tls = bool(config.get("use_tls", True))
    username = config.get("username")
    password = config.get("password")
    from_email = config.get("from_email") or username
    from_name = config.get("from_name") or from_email
    if not host or not from_email:
        raise ValueError("SMTP 配置不完整")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((from_name or "", from_email))
    message["To"] = ", ".join(contacts)
    message.set_content(body)

    if use_tls and port == 465:
        smtp = smtplib.SMTP_SSL(host, port, timeout=10)
    else:
        smtp = smtplib.SMTP(host, port, timeout=10)
        if use_tls:
            smtp.starttls()
    try:
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)
    finally:
        smtp.quit()


def _send_wecom(channel: AlertChannel, subject: str, body: str, contacts: Sequence[str]) -> None:
    config = channel.config or {}
    webhook = config.get("webhook_url")
    if not webhook:
        raise ValueError("企业微信 webhook 未配置")
    validate_outbound_hook_url(str(webhook), resolve_dns=True)
    payload = {
        "msgtype": "text",
        "text": {
            "content": f"{subject}\n{body}",
            "mentioned_mobile_list": list(contacts) or _split_csv_values(config.get("mentions")),
        },
    }
    response = requests.post(webhook, json=payload, timeout=5)
    response.raise_for_status()


def _send_dingtalk(channel: AlertChannel, subject: str, body: str, contacts: Sequence[str]) -> None:
    config = channel.config or {}
    webhook = config.get("webhook_url")
    if not webhook:
        raise ValueError("钉钉 webhook 未配置")
    validate_outbound_hook_url(str(webhook), resolve_dns=True)
    payload = {
        "msgtype": "text",
        "text": {"content": f"{subject}\n{body}"},
        "at": {
            "atMobiles": list(contacts) or _split_csv_values(config.get("at_mobiles")),
            "isAtAll": False,
        },
    }
    response = requests.post(webhook, json=payload, timeout=5)
    response.raise_for_status()


def _send_lark(channel: AlertChannel, subject: str, body: str) -> None:
    config = channel.config or {}
    webhook = config.get("webhook_url")
    if not webhook:
        raise ValueError("飞书 webhook 未配置")
    validate_outbound_hook_url(str(webhook), resolve_dns=True)
    payload = {
        "msg_type": "text",
        "content": {"text": f"{subject}\n{body}"},
    }
    response = requests.post(webhook, json=payload, timeout=5)
    response.raise_for_status()


def _send_http_callback(
    channel: AlertChannel,
    subject: str,
    body: str,
    context: Mapping[str, object],
) -> None:
    config = channel.config or {}
    url = config.get("url")
    method = str(config.get("method") or "POST").upper()
    if not url:
        raise ValueError("HTTP 回调 URL 未配置")
    if method not in {"POST", "GET", "PUT"}:
        raise ValueError("HTTP 回调仅支持 GET / POST / PUT")
    validate_outbound_hook_url(str(url), resolve_dns=True)

    headers: dict[str, str] = {}
    raw_headers = config.get("headers")
    if raw_headers:
        parsed_headers = json.loads(raw_headers)
        if isinstance(parsed_headers, dict):
            headers = {str(key): str(value) for key, value in parsed_headers.items()}

    data = None
    json_payload = None
    body_template = config.get("body_template")
    if body_template:
        rendered = render_alert_template(str(body_template), context)
        try:
            json_payload = json.loads(rendered)
        except json.JSONDecodeError:
            data = rendered
    if json_payload is None and data is None:
        json_payload = {
            "subject": subject,
            "message": body,
            "status": context.get("status"),
            "severity": context.get("severity"),
            "timestamp": context.get("timestamp"),
        }

    response = requests.request(method, url, headers=headers, json=json_payload, data=data, timeout=5)
    response.raise_for_status()


def _send_script(
    channel: AlertChannel,
    subject: str,
    body: str,
    contacts: Sequence[str],
    context: Mapping[str, object],
) -> None:
    script_version = _resolve_script_version(channel)
    script_content = (script_version.content or "").strip()
    if not script_content:
        raise ValueError("脚本内容为空")

    script_context: dict[str, object] = {
        "subject": subject,
        "body": body,
        "contacts": list(contacts),
        "channel": {
            "id": str(channel.id),
            "type": channel.channel_type,
            "name": channel.name,
            "config": channel.config or {},
        },
        "alert": dict(context),
    }

    try:
        result = _execute_script_in_subprocess(channel=channel, script_content=script_content, script_context=script_context)
    except subprocess.TimeoutExpired as exc:
        timeout_seconds = _resolve_script_timeout(channel)
        raise RuntimeError(f"脚本执行超时（{timeout_seconds} 秒）") from exc

    _raise_if_script_failed(result)


def _resolve_script_version(channel: AlertChannel) -> CodeRepositoryVersion:
    config = channel.config or {}
    repository_id = config.get("repository_id")
    if not repository_id:
        raise ValueError("脚本通道未配置 repository_id")

    try:
        repository = CodeRepository.objects.select_related("latest_version").get(id=repository_id)
    except CodeRepository.DoesNotExist as exc:
        raise ValueError("脚本仓库不存在或已删除") from exc

    version_id = config.get("version_id")
    if version_id:
        try:
            return CodeRepositoryVersion.objects.get(id=version_id, repository=repository)
        except CodeRepositoryVersion.DoesNotExist as exc:
            raise ValueError("选择的脚本版本不存在") from exc

    if repository.latest_version is None:
        raise ValueError("脚本仓库暂无可用版本")
    return repository.latest_version


def _raise_if_script_failed(result: object) -> None:
    if result is False:
        raise ValueError("脚本返回失败结果")
    if not isinstance(result, Mapping):
        return

    if result.get("success") is False:
        raise ValueError(str(result.get("message") or "脚本返回失败结果"))

    status = str(result.get("status") or "").strip().lower()
    if status in {"failed", "error"}:
        raise ValueError(str(result.get("message") or "脚本返回失败状态"))


def _execute_script_in_subprocess(
    *,
    channel: AlertChannel,
    script_content: str,
    script_context: Mapping[str, object],
) -> object:
    runner_path = Path(__file__).with_name("script_channel_runner.py")
    timeout_seconds = _resolve_script_timeout(channel)
    env = os.environ.copy()
    src_root = Path(__file__).resolve().parents[3]
    existing_pythonpath = env.get("PYTHONPATH", "").strip()
    env["PYTHONPATH"] = str(src_root) if not existing_pythonpath else f"{src_root}{os.pathsep}{existing_pythonpath}"

    with tempfile.TemporaryDirectory(prefix="alert-script-") as temp_dir:
        temp_path = Path(temp_dir)
        script_file = temp_path / "channel_script.py"
        context_file = temp_path / "context.json"
        result_file = temp_path / "result.json"

        script_file.write_text(script_content, encoding="utf-8")
        context_file.write_text(json.dumps(script_context, ensure_ascii=False, default=str), encoding="utf-8")

        completed = subprocess.run(
            [sys.executable, str(runner_path), str(script_file), str(context_file), str(result_file)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(src_root.parent),
            env=env,
            check=False,
        )

        payload = _load_script_result_payload(result_file)
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        if completed.returncode != 0:
            if isinstance(payload, Mapping) and payload.get("error"):
                detail = str(payload["error"])
                if stderr:
                    detail = f"{detail}; stderr: {stderr[:500]}"
                raise RuntimeError(f"脚本执行失败: {detail}")
            diagnostic = stderr or stdout or f"exit code {completed.returncode}"
            raise RuntimeError(f"脚本执行失败: {diagnostic[:500]}")

        if isinstance(payload, Mapping):
            if payload.get("ok") is False:
                raise RuntimeError(f"脚本执行失败: {payload.get('error') or '未知错误'}")
            if "result" in payload:
                return payload["result"]
        return None


def _load_script_result_payload(result_file: Path) -> object:
    if not result_file.exists():
        return None
    try:
        return json.loads(result_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _resolve_script_timeout(channel: AlertChannel) -> int:
    config = channel.config or {}
    raw_value = config.get("timeout_seconds", getattr(settings, "ALERT_SCRIPT_TIMEOUT_SECONDS", DEFAULT_SCRIPT_TIMEOUT_SECONDS))
    try:
        timeout_seconds = int(raw_value)
    except (TypeError, ValueError):
        timeout_seconds = DEFAULT_SCRIPT_TIMEOUT_SECONDS
    return max(1, min(timeout_seconds, MAX_SCRIPT_TIMEOUT_SECONDS))


def _split_csv_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]
