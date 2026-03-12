from __future__ import annotations

from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import AuditLog
from apps.core.models.user import Role, User
from apps.core.permissions import RequirePermission
from apps.settings.api.serializers import (
    LocalUserCreateSerializer,
    RoleSerializer,
    UserRoleSerializer,
)
from apps.settings.utils import build_permission_catalog, get_all_permissions
from apps.settings.services.ldap_service import LDAPSyncError, sync_ldap_users


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().annotate(user_count=Count("users"))
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        role = serializer.save()
        log_audit(self.request, "role.create", "Role", str(role.id), {"name": role.name})

    def perform_update(self, serializer):
        role = serializer.save()
        log_audit(self.request, "role.update", "Role", str(role.id), {"name": role.name})

    def perform_destroy(self, instance):
        role_id = str(instance.id)
        name = instance.name
        super().perform_destroy(instance)
        log_audit(self.request, "role.delete", "Role", role_id, {"name": name})


class PermissionCatalogView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"modules": build_permission_catalog()})


class UserRoleListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), RequirePermission("settings.users.manage")()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        users = User.objects.order_by("username").prefetch_related("roles")
        return Response(UserRoleSerializer(users, many=True).data)

    def post(self, request):
        serializer = LocalUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_audit(
            request,
            "user.create",
            "User",
            str(user.id),
            {"username": user.username, "auth_source": user.auth_source},
        )
        return Response(UserRoleSerializer(user).data, status=status.HTTP_201_CREATED)


class UserRoleUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "用户不存在"}, status=status.HTTP_404_NOT_FOUND)

        role_ids = request.data.get("role_ids", [])
        if role_ids is None:
            role_ids = []
        if not isinstance(role_ids, list):
            return Response({"detail": "role_ids 必须是数组"}, status=status.HTTP_400_BAD_REQUEST)

        kept_role_id = None
        if role_ids:
            kept_role_id = role_ids[0]

        kept_roles = []
        if kept_role_id:
            role = Role.objects.filter(id=kept_role_id).first()
            if not role:
                return Response({"detail": "角色不存在"}, status=status.HTTP_400_BAD_REQUEST)
            kept_roles = [role]

        user.roles.set(kept_roles)
        log_audit(
            request,
            "user.roles.update",
            "User",
            str(user.id),
            {"role_ids": [str(role.id) for role in kept_roles]},
        )
        return Response(UserRoleSerializer(user).data)


class UserDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("settings.users.manage")]

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "用户不存在"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_authenticated and str(request.user.id) == str(user.id):
            return Response({"detail": "不能删除当前登录用户"}, status=status.HTTP_400_BAD_REQUEST)

        if getattr(user, "is_superuser", False):
            return Response({"detail": "不能删除系统管理员用户"}, status=status.HTTP_400_BAD_REQUEST)

        username = user.username
        user.delete()
        log_audit(request, "user.delete", "User", str(user_id), {"username": username})
        return Response(status=status.HTTP_204_NO_CONTENT)


class LDAPSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("settings.users.manage")]

    def post(self, request):
        try:
            result = sync_ldap_users(
                actor=request.user,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        except LDAPSyncError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:  # pragma: no cover - unexpected failure
            return Response({"detail": "LDAP 同步失败，请检查日志"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "同步完成", "result": result})


def log_audit(request, action: str, target_type: str, target_id: str, metadata: dict | None = None):
    metadata = metadata or {}
    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata,
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
