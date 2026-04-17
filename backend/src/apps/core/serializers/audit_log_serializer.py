from __future__ import annotations

from rest_framework import serializers

from apps.core.permissions import get_user_permissions
from apps.core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    ip_address = serializers.SerializerMethodField()
    user_agent = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "actor",
            "action",
            "target_type",
            "target_id",
            "result",
            "metadata",
            "ip_address",
            "user_agent",
            "occurred_at",
        )

    @staticmethod
    def get_actor(obj: AuditLog) -> dict[str, str] | None:
        if not obj.actor:
            return None
        return {
            "id": str(obj.actor_id),
            "username": obj.actor.get_username(),
            "display_name": getattr(obj.actor, "display_name", ""),
        }

    def get_metadata(self, obj: AuditLog):
        return _sanitize_payload(obj.metadata or {})

    def get_ip_address(self, obj: AuditLog):
        if _can_view_audit_network_fields(self.context.get("request")):
            return obj.ip_address
        return None

    def get_user_agent(self, obj: AuditLog):
        if _can_view_audit_network_fields(self.context.get("request")):
            return obj.user_agent
        return ""


def _can_view_audit_network_fields(request) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return "settings.audit_log.manage" in get_user_permissions(user)


def _sanitize_payload(value):
    if isinstance(value, dict):
        return {
            str(key): _sanitize_scalar(str(key), nested)
            for key, nested in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    return value


def _sanitize_scalar(key: str, value):
    lowered = key.lower()
    if any(token in lowered for token in ("password", "secret", "token", "authorization", "cookie")):
        return "***"
    return _sanitize_payload(value)
