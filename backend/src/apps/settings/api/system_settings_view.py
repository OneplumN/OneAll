from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.settings.api.serializers import SystemSettingsSerializer
from apps.settings.services.system_settings_service import get_system_settings
from apps.core.models import AuditLog
from apps.core.permissions import get_user_permissions
from apps.core.permissions import RequirePermission


class SystemSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method.lower() in {"put", "patch", "post", "delete"}:
            return [permissions.IsAuthenticated(), RequirePermission("settings.system.manage")()]
        return [permissions.IsAuthenticated(), RequirePermission("settings.system.view")()]

    def get(self, request: Request) -> Response:
        instance = get_system_settings()
        serializer = SystemSettingsSerializer(instance)
        return Response(serializer.data)

    def put(self, request: Request) -> Response:
        instance = get_system_settings()
        if "settings.system.manage" not in get_user_permissions(request.user):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        serializer = SystemSettingsSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        if request.user and hasattr(updated, "updated_by"):
            updated.updated_by = request.user
            updated.save(update_fields=["updated_by"])
        AuditLog.objects.create(
            actor=request.user,
            action="system_settings.update",
            target_type="SystemSettings",
            target_id=str(updated.id),
            metadata={"fields": list(serializer.validated_data.keys())},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return Response(SystemSettingsSerializer(updated).data, status=status.HTTP_200_OK)
