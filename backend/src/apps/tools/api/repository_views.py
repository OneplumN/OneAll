from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tools.api.serializers import ScriptVersionCreateSerializer, ToolDefinitionSerializer
from apps.tools.models import ScriptVersion, ToolDefinition
from apps.tools.services.repository_audit import RepositoryAuditService


class RepositoryUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        tool = get_object_or_404(ToolDefinition, id=request.data.get("tool_id"))
        serializer = ScriptVersionCreateSerializer(
            data=request.data,
            context={"tool": tool, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        version = serializer.save()
        RepositoryAuditService(actor=request.user).log_upload(tool, version)
        return Response(ToolDefinitionSerializer(tool).data, status=status.HTTP_201_CREATED)


class RepositoryRollbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        tool = get_object_or_404(ToolDefinition, id=request.data.get("tool_id"))
        version_id = request.data.get("version_id")
        version = get_object_or_404(ScriptVersion, id=version_id, tool=tool)
        tool.latest_version = version
        tool.updated_by = request.user
        tool.save(update_fields=["latest_version", "updated_by", "updated_at"])
        RepositoryAuditService(actor=request.user).log_rollback(tool, version)
        return Response(ToolDefinitionSerializer(tool).data)
