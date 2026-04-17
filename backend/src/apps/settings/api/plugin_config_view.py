from __future__ import annotations

from rest_framework import permissions, viewsets

from apps.core.permissions import RequirePermission
from apps.settings.models import PluginConfig
from .serializers import PluginConfigSerializer


class PluginConfigViewSet(viewsets.ModelViewSet):
    queryset = PluginConfig.objects.all().order_by("name")
    serializer_class = PluginConfigSerializer
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            permission_classes = [permissions.IsAuthenticated, RequirePermission("settings.system.view")]
        else:
            permission_classes = [permissions.IsAuthenticated, RequirePermission("settings.system.manage")]
        return [permission() for permission in permission_classes]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        kwargs["partial"] = partial
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
