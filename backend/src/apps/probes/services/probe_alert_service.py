from __future__ import annotations

import json
import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Iterable, Sequence

import requests
from django.conf import settings
from django.utils import timezone

from apps.core.models import AuditLog
from apps.probes.models import ProbeScheduleExecution
from apps.settings.models import AlertChannel, AlertTemplate
from apps.settings.services.template_renderer import AlertTemplateError, render_alert_template
from apps.settings.services.system_settings_service import get_system_settings

logger = logging.getLogger(__name__)

FAILURE_STATUSES = {
    ProbeScheduleExecution.Status.FAILED,
    ProbeScheduleExecution.Status.MISSED,
}
ALERT_LOG_ACTION = "probes.alert"
DEFAULT_TEMPLATE_BODY = (
    "【${title}】\n"
    "任务：${task_name}\n"
    "探针：${probe_name}\n"
    "状态：${status}\n"
    "时间：${timestamp}\n"
    "详情：${message}\n"
    "${result_url}"
)


def evaluate_probe_alert(execution: ProbeScheduleExecution) -> None:
    """Evaluate whether the given execution should trigger an alert."""

    if execution.status not in FAILURE_STATUSES:
        return

    threshold = _resolve_threshold(execution)
    if threshold <= 0:
        return

    failures = _collect_failure_window(execution, threshold)
    if len(failures) < threshold:
        return

    if failures[0].id != execution.id:
        # Only the most recent execution should fan out the alert.
        return

    if any(item.status not in FAILURE_STATUSES for item in failures):
        return

    if _alert_already_recorded(execution):
        return

    contacts = _resolve_contacts(execution)
    context = _build_context(execution, contacts, threshold)

    _record_alert(execution, failures, threshold, contacts, context)
    _send_alert_notifications(context, contacts)


def _resolve_threshold(execution: ProbeScheduleExecution) -> int:
    metadata = execution.schedule.metadata or {}
    value = metadata.get("alert_threshold")
    try:
        threshold = int(value)
    except (TypeError, ValueError):
        threshold = 1
    return max(threshold, 1)


def _collect_failure_window(execution: ProbeScheduleExecution, threshold: int) -> list[ProbeScheduleExecution]:
    return list(
        ProbeScheduleExecution.objects.filter(
            schedule=execution.schedule,
            probe=execution.probe,
            scheduled_at__lte=execution.scheduled_at,
        )
        .order_by("-scheduled_at")[:threshold]
    )


def _alert_already_recorded(execution: ProbeScheduleExecution) -> bool:
    return AuditLog.objects.filter(
        action=ALERT_LOG_ACTION,
        metadata__execution_id=str(execution.id),
    ).exists()


def _resolve_contacts(execution: ProbeScheduleExecution) -> list[str]:
    metadata = execution.schedule.metadata or {}
    contacts = metadata.get("alert_contacts") or []
    if isinstance(contacts, str):
        contacts = [contacts]
    cleaned = [str(contact).strip() for contact in contacts if str(contact).strip()]
    if cleaned:
        return cleaned
    system_settings = get_system_settings()
    defaults = system_settings.notification_channels or {}
    default_email = defaults.get("email")
    if default_email:
        return [str(default_email)]
    return []


def _build_context(execution: ProbeScheduleExecution, contacts: Sequence[str], threshold: int) -> dict[str, str]:
    schedule = execution.schedule
    probe = execution.probe
    finished_at = execution.finished_at or timezone.now()
    severity = _detect_severity(execution.status)
    system_settings = get_system_settings()
    platform_name = system_settings.platform_name
    title = f"{platform_name} | {schedule.name} 探针告警"
    detail_lines = []
    if execution.message:
        detail_lines.append(execution.message.strip())
    detail_lines.append(f"目标：{schedule.target}")
    if execution.status_code:
        detail_lines.append(f"状态码：{execution.status_code}")
    if execution.response_time_ms:
        detail_lines.append(f"响应耗时：{execution.response_time_ms} ms")
    detail_lines.append(f"连续失败次数：{threshold}")
    detail_lines.append(f"调度时间：{execution.scheduled_at.isoformat()}")
    if contacts:
        detail_lines.append(f"通知联系人：{', '.join(contacts)}")
    message = "\n".join(detail_lines)
    return {
        "title": title,
        "severity": severity,
        "status": execution.status,
        "timestamp": finished_at.isoformat(),
        "task_name": schedule.name,
        "probe_name": probe.name if probe else "",
        "message": message,
        "result_url": _build_result_url(execution),
    }


def _build_result_url(execution: ProbeScheduleExecution) -> str:
    base = getattr(settings, "CONSOLE_BASE_URL", "") or ""
    path = f"/#/probes/schedules?scheduleId={execution.schedule_id}&executionId={execution.id}"
    return f"{base.rstrip('/')}{path}" if base else path


def _detect_severity(status: str) -> str:
    normalized = status.lower()
    if normalized == ProbeScheduleExecution.Status.FAILED:
        return "critical"
    if normalized == ProbeScheduleExecution.Status.MISSED:
        return "warning"
    return "info"


def _record_alert(
    execution: ProbeScheduleExecution,
    failures: Sequence[ProbeScheduleExecution],
    threshold: int,
    contacts: Sequence[str],
    context: dict[str, str],
) -> None:
    AuditLog.objects.create(
        action=ALERT_LOG_ACTION,
        target_type="ProbeSchedule",
        target_id=str(execution.schedule_id),
        result="failed",
        metadata={
            "execution_id": str(execution.id),
            "execution_ids": [str(item.id) for item in failures],
            "schedule_id": str(execution.schedule_id),
            "probe_id": str(execution.probe_id),
            "status": execution.status,
            "threshold": threshold,
            "alert_contacts": list(contacts),
            "message": context.get("message", ""),
        },
    )


def _send_alert_notifications(context: dict[str, str], contacts: Sequence[str]) -> None:
    channels = list(AlertChannel.objects.filter(enabled=True))
    if not channels:
        logger.warning("探针告警已触发但没有启用的告警通道，跳过发送")
        return

    for channel in channels:
        try:
            subject, body = _render_for_channel(channel.channel_type, context)
            _dispatch_to_channel(channel, subject, body, contacts, context)
        except Exception:
            logger.exception("Failed to dispatch alert via channel %s", channel.channel_type)


def _render_for_channel(channel_type: str, context: dict[str, str]) -> tuple[str, str]:
    template = (
        AlertTemplate.objects.filter(channel_type=channel_type)
        .order_by("-is_default", "-updated_at")
        .first()
    )
    subject_template = template.subject if template and template.subject else context["title"]
    body_template = template.body if template else DEFAULT_TEMPLATE_BODY
    try:
        subject = render_alert_template(subject_template, context)
    except AlertTemplateError:
        subject = context["title"]
    try:
        body = render_alert_template(body_template, context)
    except AlertTemplateError:
        body = (
            f"{context['title']}\n"
            f"任务：{context['task_name']}\n"
            f"探针：{context['probe_name']}\n"
            f"状态：{context['status']}\n"
            f"时间：{context['timestamp']}\n"
            f"详情：{context['message']}\n"
            f"{context['result_url']}"
        )
    if not subject:
        subject = context["title"]
    return subject, body


def _dispatch_to_channel(
    channel: AlertChannel,
    subject: str,
    body: str,
    contacts: Sequence[str],
    context: dict[str, str],
) -> None:
    channel_type = channel.channel_type
    if channel_type == "email":
        _send_email(channel, subject, body, contacts)
    elif channel_type == "wecom":
        _send_wecom(channel, subject, body, contacts)
    elif channel_type == "dingtalk":
        _send_dingtalk(channel, subject, body, contacts)
    elif channel_type == "lark":
        _send_lark(channel, subject, body)
    elif channel_type == "http":
        _send_http_callback(channel, subject, body, context)
    else:
        logger.info("Channel %s is not supported for automatic alerts", channel_type)


def _send_email(channel: AlertChannel, subject: str, body: str, contacts: Sequence[str]) -> None:
    if not contacts:
        logger.warning("Email channel %s skipped due to empty recipients", channel.channel_type)
        return
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
    if username and password:
        smtp.login(username, password)
    smtp.send_message(message)
    smtp.quit()


def _send_wecom(channel: AlertChannel, subject: str, body: str, contacts: Sequence[str]) -> None:
    config = channel.config or {}
    webhook = config.get("webhook_url")
    if not webhook:
        raise ValueError("企业微信 webhook 未配置")
    payload = {
        "msgtype": "text",
        "text": {
            "content": f"{subject}\n{body}",
            "mentioned_mobile_list": list(contacts) or config.get("mentions") or [],
        },
    }
    requests.post(webhook, json=payload, timeout=5)


def _send_dingtalk(channel: AlertChannel, subject: str, body: str, contacts: Sequence[str]) -> None:
    config = channel.config or {}
    webhook = config.get("webhook_url")
    if not webhook:
        raise ValueError("钉钉 webhook 未配置")
    payload = {
        "msgtype": "text",
        "text": {"content": f"{subject}\n{body}"},
        "at": {
            "atMobiles": list(contacts) or config.get("at_mobiles") or [],
            "isAtAll": False,
        },
    }
    requests.post(webhook, json=payload, timeout=5)


def _send_lark(channel: AlertChannel, subject: str, body: str) -> None:
    config = channel.config or {}
    webhook = config.get("webhook_url")
    if not webhook:
        raise ValueError("飞书 webhook 未配置")
    payload = {
        "msg_type": "text",
        "content": {"text": f"{subject}\n{body}"},
    }
    requests.post(webhook, json=payload, timeout=5)


def _send_http_callback(
    channel: AlertChannel,
    subject: str,
    body: str,
    context: dict[str, str],
) -> None:
    config = channel.config or {}
    url = config.get("url")
    method = (config.get("method") or "POST").upper()
    if not url:
        raise ValueError("HTTP 回调 URL 未配置")
    headers = {}
    if config.get("headers"):
        try:
            headers = json.loads(config["headers"])
        except json.JSONDecodeError:
            logger.warning("HTTP channel headers 配置不是合法 JSON，已忽略")
    data = None
    json_payload = None
    body_template = config.get("body_template")
    if body_template:
        try:
            rendered = render_alert_template(body_template, context)
            json_payload = json.loads(rendered)
        except (AlertTemplateError, json.JSONDecodeError):
            data = rendered if "rendered" in locals() else body
    if json_payload is None and data is None:
        json_payload = {
            "subject": subject,
            "message": body,
            "status": context.get("status"),
            "severity": context.get("severity"),
        }
    requests.request(method, url, headers=headers, json=json_payload, data=data, timeout=5)
