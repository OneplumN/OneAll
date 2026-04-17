from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import RequirePermission
from apps.tools.models import ScriptPlugin
from apps.tools.services.repository_execution_service import RepositoryExecutionService
from .serializers import (
    SECRET_MASK,
    ScriptPluginSerializer,
    ScriptPluginUpdateSerializer,
    ToolExecutionSerializer,
    _is_secret_key,
)


class ScriptPluginListView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("tools.library.view")]

    def get(self, request: Request) -> Response:
        queryset = ScriptPlugin.objects.select_related("repository", "repository_version").order_by("name")
        serializer = ScriptPluginSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class ScriptPluginDetailView(APIView):
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), RequirePermission("tools.library.view")()]
        return [permissions.IsAuthenticated(), RequirePermission("tools.library.manage")()]

    def get(self, request: Request, slug: str) -> Response:
        plugin = get_object_or_404(ScriptPlugin.objects.select_related("repository", "repository_version"), slug=slug)
        return Response(ScriptPluginSerializer(plugin, context={"request": request}).data)

    def patch(self, request: Request, slug: str) -> Response:
        plugin = get_object_or_404(ScriptPlugin, slug=slug)
        serializer = ScriptPluginUpdateSerializer(plugin, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        plugin.refresh_from_db()
        return Response(ScriptPluginSerializer(plugin, context={"request": request}).data, status=status.HTTP_200_OK)


class ScriptPluginExecuteView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("tools.library.manage")]

    def post(self, request: Request, slug: str) -> Response:
        plugin = get_object_or_404(ScriptPlugin.objects.select_related("repository", "repository_version"), slug=slug)
        parameters = request.data.get("parameters") or {}
        metadata = plugin.metadata or {}
        config_values = metadata.get("config_values", {})
        payload = {**config_values, **_filter_parameters(parameters)}
        service = RepositoryExecutionService(actor=request.user)
        execution = service.execute(
            plugin.repository,
            parameters=payload,
            repository_version=plugin.repository_version,
        )

        logs = list(metadata.get("logs", []))
        logs.append(
            {
                "timestamp": timezone.now().isoformat(),
                "message": f"触发任务 run_id={execution.run_id}",
            }
        )
        metadata["logs"] = logs[-50:]
        plugin.metadata = metadata
        plugin.save(update_fields=["metadata", "updated_at"])

        return Response(ToolExecutionSerializer(execution).data, status=status.HTTP_202_ACCEPTED)


def _filter_parameters(parameters: dict) -> dict:
    cleaned: dict = {}
    for key, value in (parameters or {}).items():
        if _is_secret_key(str(key)) and value == SECRET_MASK:
            continue
        cleaned[str(key)] = value
    return cleaned
