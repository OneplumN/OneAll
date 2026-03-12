from __future__ import annotations

from rest_framework import permissions, viewsets

from apps.core.permissions import RequirePermission
from apps.settings.api.serializers import AlertTemplateSerializer
from apps.settings.models import AlertTemplate


class AlertTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = AlertTemplateSerializer
    queryset = AlertTemplate.objects.all().order_by("channel_type", "-is_default", "name")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.templates.view")]
        elif self.action == "destroy":
            permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.templates.delete")]
        elif self.action == "create":
            permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.templates.create")]
        else:
            permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.templates.update")]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        channel_type = self.request.query_params.get("channel_type")
        if channel_type:
            queryset = queryset.filter(channel_type=channel_type)
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()
        self._ensure_single_default(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._ensure_single_default(instance)

    def _ensure_single_default(self, instance: AlertTemplate) -> None:
        if instance.is_default:
            AlertTemplate.objects.filter(channel_type=instance.channel_type).exclude(id=instance.id).update(
                is_default=False
            )
        elif not AlertTemplate.objects.filter(
            channel_type=instance.channel_type, is_default=True
        ).exclude(id=instance.id).exists():
            instance.is_default = True
            instance.save(update_fields=["is_default", "updated_at"])
