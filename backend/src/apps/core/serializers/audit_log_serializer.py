from __future__ import annotations

from rest_framework import serializers

from apps.core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()

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
