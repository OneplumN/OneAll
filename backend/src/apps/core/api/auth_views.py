from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth.ldap_client import authenticate_via_ldap
from apps.core.models import AuditLog
from apps.settings.services.ldap_service import assign_default_roles
from apps.core.throttling import LoginIPThrottle, LoginUsernameThrottle
from core.auth.jwt import JWTAuthentication, generate_access_token
from apps.core.permissions import get_user_permissions
from apps.core.roles import get_primary_role

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField()


class LoginView(APIView):
    """Issue JWT access token for valid user credentials."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [LoginIPThrottle, LoginUsernameThrottle]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(request=request, username=username, password=password)

        if not user:
            user = _authenticate_with_ldap(username=username, password=password, request=request)

        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        token = generate_access_token(user)

        return Response(
            {
                "access_token": token,
                "token_type": "Bearer",
                "user": _serialize_user(user),
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Return basic information about current authenticated user."""

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request: Request) -> Response:
        user = request.user
        return Response(_serialize_user(user))

    def patch(self, request: Request) -> Response:
        user = request.user
        serializer = ProfileUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        updated = serializer.update(user, serializer.validated_data)
        return Response(_serialize_user(updated), status=status.HTTP_200_OK)


class ProfileUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate(self, attrs):
        user = self.context["request"].user
        auth_source = getattr(user, "auth_source", "local") or "local"

        # LDAP 用户默认只允许维护手机号（显示名/邮箱从目录同步）
        if auth_source == "ldap":
            forbidden = set(attrs.keys()) - {"phone"}
            if forbidden:
                raise serializers.ValidationError({"detail": "LDAP 用户仅允许修改手机号"})
        return attrs

    def update(self, instance: User, validated_data: dict) -> User:
        for field in ("display_name", "email", "phone"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save(update_fields=list(validated_data.keys()))
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_new_password = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        user = self.context["request"].user
        auth_source = getattr(user, "auth_source", "local") or "local"
        if auth_source == "ldap":
            raise PermissionDenied("LDAP 用户不支持在本平台修改密码")

        current_password = attrs.get("current_password") or ""
        if not user.check_password(current_password):
            raise serializers.ValidationError({"current_password": ["当前密码不正确"]})

        new_password = attrs.get("new_password") or ""
        confirm = attrs.get("confirm_new_password")
        if confirm is not None and new_password != (confirm or ""):
            raise serializers.ValidationError({"confirm_new_password": ["两次输入的新密码不一致"]})

        validate_password(new_password, user=user)
        return attrs


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "密码已更新"}, status=status.HTTP_200_OK)


def _serialize_user(user: User) -> dict[str, str | list[str]]:
    role_names: list[str] = []
    role = get_primary_role(user)
    if role:
        role_names = [role.name]

    return {
        "id": str(user.id),
        "username": user.get_username(),
        "display_name": getattr(user, "display_name", "") or user.get_full_name(),
        "email": user.email,
        "phone": getattr(user, "phone", ""),
        "roles": role_names,
        "permissions": sorted(get_user_permissions(user)),
        "auth_source": getattr(user, "auth_source", "local"),
        "is_admin": bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)),
    }


def _authenticate_with_ldap(*, username: str, password: str, request: Request) -> User | None:
    ldap_payload = authenticate_via_ldap(username=username, password=password)
    if not ldap_payload:
        return None

    user = User.objects.filter(username=username).first()
    if user and user.auth_source not in ("ldap", ""):
        # 已存在的本地用户不通过 LDAP 登录
        return None

    created = False
    now = timezone.now()
    if not user:
        user = User(username=username)
        user.set_unusable_password()
        created = True

    user.display_name = ldap_payload.get("display_name") or username
    email = ldap_payload.get("email") or user.email
    if email:
        user.email = email
    user.auth_source = "ldap"
    user.external_id = ldap_payload.get("dn") or user.external_id
    user.external_synced_at = now

    with transaction.atomic():
        user.save()
        assigned_roles = assign_default_roles(
            user=user,
            actor=user,
            reason="ldap_default_roles",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

    if created:
        AuditLog.objects.create(
            actor=user,
            action="user.create.ldap_sync",
            target_type="User",
            target_id=str(user.id),
            metadata={
                "username": username,
                "auth_source": "ldap",
            },
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
    elif assigned_roles:
        # 角色分配的审计已在 assign_default_roles 中记录
        pass

    return user
