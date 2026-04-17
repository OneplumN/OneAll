from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import RequirePermission, get_user_permissions
from apps.tools.api.serializers import (
    CodeDirectorySerializer,
    CodeDirectoryWriteSerializer,
    CodeRepositorySerializer,
    CodeRepositoryVersionCreateSerializer,
    CodeRepositoryVersionSerializer,
    CodeRepositoryWriteSerializer,
    ToolExecutionSerializer,
)
from apps.tools.models import CodeDirectory, CodeRepository, CodeRepositoryVersion
from apps.tools.services.repository_execution_service import (
    RepositoryExecutionError,
    RepositoryExecutionService,
)


class CodeDirectoryListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method.upper() == "POST":
            return [permissions.IsAuthenticated(), RequirePermission("tools.repository.create")()]
        return [permissions.IsAuthenticated(), RequirePermission("tools.repository.view")()]

    def get(self, request: Request) -> Response:
        queryset = CodeDirectory.objects.order_by("title")
        serializer = CodeDirectorySerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = CodeDirectoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        directory = serializer.save(created_by=request.user)
        return Response(CodeDirectorySerializer(directory).data, status=status.HTTP_201_CREATED)


class CodeDirectoryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("tools.repository.manage")]

    def put(self, request: Request, key: str) -> Response:
        directory = get_object_or_404(CodeDirectory, key=key)
        serializer = CodeDirectoryWriteSerializer(directory, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        directory = serializer.save(updated_by=request.user)
        return Response(CodeDirectorySerializer(directory).data)

    def delete(self, request: Request, key: str) -> Response:
        directory = get_object_or_404(CodeDirectory, key=key)
        if directory.builtin:
            return Response({"detail": "内置目录不可删除。"}, status=status.HTTP_400_BAD_REQUEST)
        fallback = CodeDirectory.objects.exclude(key=directory.key).first()
        if fallback is None:
            return Response({"detail": "无法删除最后一个目录。"}, status=status.HTTP_400_BAD_REQUEST)
        CodeRepository.objects.filter(directory=directory).update(directory=fallback)
        directory.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CodeRepositoryListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method.upper() == "POST":
            return [permissions.IsAuthenticated(), RequirePermission("tools.repository.create")()]
        return [permissions.IsAuthenticated(), RequirePermission("tools.repository.view")()]

    def get(self, request: Request) -> Response:
        queryset = CodeRepository.objects.select_related("directory", "latest_version").order_by("name")
        serializer = CodeRepositorySerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = CodeRepositoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repo = serializer.save(created_by=request.user)
        return Response(CodeRepositorySerializer(repo).data, status=status.HTTP_201_CREATED)


class CodeRepositoryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method.upper() == "GET":
            return [permissions.IsAuthenticated(), RequirePermission("tools.repository.view")()]
        return [permissions.IsAuthenticated()]

    def get(self, request: Request, repository_id: str) -> Response:
        repo = get_object_or_404(CodeRepository, id=repository_id)
        serializer = CodeRepositorySerializer(repo)
        return Response(serializer.data)

    def put(self, request: Request, repository_id: str) -> Response:
        repo = get_object_or_404(CodeRepository, id=repository_id)
        self._ensure_repo_manage_scope(request, repo)
        serializer = CodeRepositoryWriteSerializer(repo, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        repo = serializer.save(updated_by=request.user)
        return Response(CodeRepositorySerializer(repo).data)

    def delete(self, request: Request, repository_id: str) -> Response:
        repo = get_object_or_404(CodeRepository, id=repository_id)
        self._ensure_repo_manage_scope(request, repo)
        repo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _ensure_repo_manage_scope(request: Request, repo: CodeRepository) -> None:
        if getattr(request.user, "is_superuser", False):
            return
        if "tools.repository.manage" in get_user_permissions(request.user):
            return
        if getattr(repo, "created_by_id", None) and str(repo.created_by_id) == str(request.user.id):
            return
        raise PermissionDenied("仅仓库创建者或系统管理员可修改该仓库")


class CodeRepositoryVersionListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method.upper() == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), RequirePermission("tools.repository.view")()]

    def get(self, request: Request, repository_id: str) -> Response:
        repo = get_object_or_404(CodeRepository, id=repository_id)
        versions = repo.versions.order_by("-created_at")
        serializer = CodeRepositoryVersionSerializer(versions, many=True)
        return Response(serializer.data)

    def post(self, request: Request, repository_id: str) -> Response:
        repo = get_object_or_404(CodeRepository, id=repository_id)
        CodeRepositoryDetailView._ensure_repo_manage_scope(request, repo)
        serializer = CodeRepositoryVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            version = repo.versions.create(
                version=serializer.validated_data.get("version") or f"v{repo.versions.count() + 1}.0.0",
                summary=serializer.validated_data.get("summary", ""),
                change_log=serializer.validated_data.get("change_log", ""),
                content=serializer.validated_data["content"],
                created_by=request.user,
            )
            repo.latest_version = version
            repo.content = version.content
            repo.save(update_fields=["latest_version", "content"])
        return Response(CodeRepositoryVersionSerializer(version).data, status=status.HTTP_201_CREATED)


class CodeRepositoryVersionRollbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, repository_id: str, version_id: str) -> Response:
        repo = get_object_or_404(CodeRepository, id=repository_id)
        CodeRepositoryDetailView._ensure_repo_manage_scope(request, repo)
        version = get_object_or_404(CodeRepositoryVersion, id=version_id, repository=repo)
        repo.latest_version = version
        repo.content = version.content
        repo.save(update_fields=["latest_version", "content"])
        return Response(CodeRepositorySerializer(repo).data)


class CodeRepositoryExecuteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, repository_id: str) -> Response:
        repository = get_object_or_404(CodeRepository, id=repository_id)
        CodeRepositoryDetailView._ensure_repo_manage_scope(request, repository)
        parameters = request.data.get("parameters") or {}
        service = RepositoryExecutionService(actor=request.user)
        try:
            execution = service.execute(repository, parameters=parameters)
        except RepositoryExecutionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ToolExecutionSerializer(execution).data, status=status.HTTP_202_ACCEPTED)
