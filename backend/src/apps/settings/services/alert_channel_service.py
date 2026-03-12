from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from django.utils import timezone

from apps.core.models import AuditLog, User
from apps.settings.models import AlertChannel
from apps.tools.models import CodeRepository


CHANNEL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "email",
        "name": "邮件",
        "description": "通过 SMTP 推送告警邮件。",
        "fields": [
            {"key": "smtp_host", "label": "SMTP 服务器", "type": "text", "placeholder": "smtp.example.com"},
            {"key": "smtp_port", "label": "端口", "type": "number", "placeholder": "465"},
            {"key": "use_tls", "label": "启用 TLS", "type": "switch"},
            {"key": "username", "label": "用户名", "type": "text"},
            {"key": "password", "label": "密码/授权码", "type": "secret"},
            {"key": "from_name", "label": "发件人名称", "type": "text", "placeholder": "OneAll 告警中心"},
            {"key": "from_email", "label": "发件邮箱", "type": "text", "placeholder": "alerts@example.com"},
        ],
    },
    {
        "type": "wecom",
        "name": "企业微信机器人",
        "description": "通过企业微信群机器人推送。",
        "fields": [
            {"key": "webhook_url", "label": "Webhook 地址", "type": "text", "placeholder": "https://qyapi.weixin.qq.com/..."},
            {"key": "secret", "label": "加签密钥", "type": "secret", "placeholder": "可选"},
            {"key": "mentions", "label": "@手机号(逗号分隔)", "type": "text"},
        ],
    },
    {
        "type": "dingtalk",
        "name": "钉钉机器人",
        "description": "适配钉钉自定义机器人。",
        "fields": [
            {"key": "webhook_url", "label": "Webhook 地址", "type": "text", "placeholder": "https://oapi.dingtalk.com/..."},
            {"key": "secret", "label": "加签密钥", "type": "secret", "placeholder": "如需签名可填写"},
            {"key": "at_mobiles", "label": "@手机号", "type": "text"},
        ],
    },
    {
        "type": "lark",
        "name": "飞书机器人",
        "description": "推送至飞书群机器人。",
        "fields": [
            {"key": "webhook_url", "label": "Webhook 地址", "type": "text"},
            {"key": "secret", "label": "签名密钥", "type": "secret", "placeholder": "可选"},
        ],
    },
    {
        "type": "http",
        "name": "HTTP 回调",
        "description": "调用第三方 HTTP 接口通知。",
        "fields": [
            {"key": "method", "label": "请求方法", "type": "select", "options": ["POST", "GET", "PUT"]},
            {"key": "url", "label": "URL", "type": "text", "placeholder": "https://example.com/alert"},
            {"key": "headers", "label": "Headers(JSON)", "type": "textarea", "placeholder": '{"Authorization": "Bearer"}'},
            {"key": "body_template", "label": "Body 模板(JSON)", "type": "textarea"},
        ],
    },
    {
        "type": "script",
        "name": "脚本执行",
        "description": "引用代码管理中的脚本并由平台执行。",
        "fields": [],
    },
]


def _get_definition(channel_type: str) -> Dict[str, Any]:
    for definition in CHANNEL_DEFINITIONS:
        if definition["type"] == channel_type:
            return definition
    raise ValueError(f"Unsupported channel type: {channel_type}")


def ensure_channels() -> None:
    for definition in CHANNEL_DEFINITIONS:
        AlertChannel.objects.get_or_create(
            channel_type=definition["type"],
            defaults={
                "name": definition["name"],
                "config": {},
            },
        )


def list_channels() -> List[Dict[str, Any]]:
    ensure_channels()
    entries = []
    for definition in CHANNEL_DEFINITIONS:
        channel = AlertChannel.objects.get(channel_type=definition["type"])
        entries.append(_serialize_channel(channel, definition))
    return entries


def update_channel(
    *,
    channel_type: str,
    enabled: bool,
    config: Dict[str, Any],
    actor: User,
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    definition = _get_definition(channel_type)
    channel, _ = AlertChannel.objects.get_or_create(
        channel_type=channel_type,
        defaults={"name": definition["name"]},
    )
    channel.enabled = bool(enabled)
    channel.name = definition["name"]
    channel.config = config or {}
    channel.updated_by = actor
    channel.save()
    AuditLog.objects.create(
        actor=actor,
        action="alert_channel.update",
        target_type="AlertChannel",
        target_id=str(channel.id),
        metadata={"channel_type": channel_type, "enabled": channel.enabled},
        ip_address=meta.get("ip"),
        user_agent=meta.get("ua", ""),
    )
    return _serialize_channel(channel, definition)


def test_channel(*, channel_type: str, actor: User | None, meta: Dict[str, Any]) -> Dict[str, str]:
    definition = _get_definition(channel_type)
    ensure_channels()
    channel = AlertChannel.objects.get(channel_type=channel_type)
    result = _evaluate_channel(channel)
    channel.last_test_status = result["status"]
    channel.last_test_message = result["message"]
    channel.last_test_at = timezone.now()
    channel.save(update_fields=["last_test_status", "last_test_message", "last_test_at", "updated_at"])
    AuditLog.objects.create(
        actor=actor,
        action="alert_channel.test",
        target_type="AlertChannel",
        target_id=str(channel.id),
        metadata={"channel_type": channel_type, "status": result["status"]},
        ip_address=meta.get("ip"),
        user_agent=meta.get("ua", ""),
    )
    return {"detail": result["message"], "status": result["status"]}


def _serialize_channel(channel: AlertChannel, definition: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(channel.id),
        "type": channel.channel_type,
        "name": definition["name"],
        "description": definition.get("description", ""),
        "enabled": channel.enabled,
        "config": channel.config or {},
        "config_schema": definition.get("fields", []),
        "last_test_status": channel.last_test_status,
        "last_test_at": channel.last_test_at.isoformat() if channel.last_test_at else None,
        "last_test_message": channel.last_test_message,
    }


def _evaluate_channel(channel: AlertChannel) -> Dict[str, str]:
    config = channel.config or {}
    required_map = {
        "email": ["smtp_host", "smtp_port", "from_email"],
        "wecom": ["webhook_url"],
        "dingtalk": ["webhook_url"],
        "lark": ["webhook_url"],
        "http": ["url"],
    }
    missing = [key for key in required_map.get(channel.channel_type, []) if not config.get(key)]
    if missing:
        return {"status": "failed", "message": f"缺少必填字段: {', '.join(missing)}"}
    if channel.channel_type == "script":
        return _evaluate_script_channel(config)
    return {"status": "success", "message": "配置校验通过，可用于告警推送"}


def _evaluate_script_channel(config: Dict[str, Any]) -> Dict[str, str]:
    repository_id = config.get("repository_id")
    if not repository_id:
        return {"status": "failed", "message": "请选择脚本仓库"}
    try:
        repository = CodeRepository.objects.get(id=repository_id)
    except CodeRepository.DoesNotExist:
        return {"status": "failed", "message": "脚本仓库不存在或已删除"}
    version_id = config.get("version_id")
    if version_id:
        if not repository.versions.filter(id=version_id).exists():
            return {"status": "failed", "message": "选择的脚本版本不存在"}
    elif repository.latest_version is None:
        return {"status": "failed", "message": "脚本仓库暂无可用版本"}
    return {"status": "success", "message": "配置校验通过，可用于告警推送"}
