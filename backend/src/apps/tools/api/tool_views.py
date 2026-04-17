from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import RequireAnyPermission, RequirePermission
from apps.tools.api.serializers import (
    ScriptVersionCreateSerializer,
    ToolCreateSerializer,
    ToolDefinitionSerializer,
    ToolExecuteSerializer,
    ToolExecutionSerializer,
)
from apps.tools.models import ScriptPlugin, ToolDefinition, ToolExecution
from apps.tools.services.repository_audit import RepositoryAuditService
from apps.tools.services.tool_runner import ToolRunnerService


class ToolDefinitionListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method.upper() == "POST":
            return [permissions.IsAuthenticated(), RequirePermission("tools.library.create")()]
        return [permissions.IsAuthenticated(), RequirePermission("tools.library.view")()]

    def get(self, request: Request) -> Response:
        queryset = ToolDefinition.objects.all().order_by("name")
        serializer = ToolDefinitionSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = ToolCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        tool = serializer.save()
        data = ToolDefinitionSerializer(tool).data
        return Response(data, status=status.HTTP_201_CREATED)


class ToolScriptVersionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("tools.library.manage")]

    def post(self, request: Request, tool_id: str) -> Response:
        tool = get_object_or_404(ToolDefinition, id=tool_id)
        serializer = ScriptVersionCreateSerializer(
            data=request.data,
            context={"tool": tool, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        version = serializer.save()
        RepositoryAuditService(actor=request.user).log_upload(tool, version)
        return Response(ToolDefinitionSerializer(tool).data, status=status.HTTP_201_CREATED)


class ToolExecuteView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequireAnyPermission("tools.library.manage", "tools.library.execute")]

    def post(self, request: Request, tool_id: str) -> Response:
        tool = get_object_or_404(ToolDefinition, id=tool_id)
        serializer = ToolExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        script_version = serializer.validated_data.get("script_version_id")
        runner = ToolRunnerService(actor=request.user)
        execution = runner.enqueue(
            tool,
            parameters=serializer.validated_data.get("parameters"),
            script_version=script_version,
        )

        return Response(ToolExecutionSerializer(execution).data, status=status.HTTP_202_ACCEPTED)


class ToolExecutionListView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("tools.library.view")]

    def get(self, request: Request) -> Response:
        queryset = ToolExecution.objects.select_related("tool", "script_version").order_by("-created_at")
        plugin_slug = request.query_params.get("plugin_slug")
        if plugin_slug:
            plugin = ScriptPlugin.objects.filter(slug=plugin_slug).first()
            if plugin:
                queryset = queryset.filter(tool__metadata__repository_id=str(plugin.repository_id))
            else:
                return Response([], status=status.HTTP_200_OK)
        serializer = ToolExecutionSerializer(queryset[:50], many=True)
        return Response(serializer.data)
