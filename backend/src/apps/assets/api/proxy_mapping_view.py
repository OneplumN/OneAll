from __future__ import annotations

from typing import Any, Dict, List

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.models import ProxyMapping
from apps.core.permissions import RequirePermission

from .proxy_mapping_serializers import ProxyMappingSerializer, ProxyMappingUpsertSerializer


class ProxyMappingView(APIView):
    """
    Proxy 映射维护：
    - GET：获取映射列表（仅 active）
    - PUT：批量 upsert（display_name 为空则软删除）
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        queryset = ProxyMapping.objects.filter(is_active=True).order_by("proxy")
        serializer = ProxyMappingSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request: Request) -> Response:
        self.check_permissions(request)
        serializer = ProxyMappingUpsertSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        user = request.user if getattr(request.user, "is_authenticated", False) else None
        items: List[Dict[str, Any]] = serializer.validated_data.get("items") or []
        changed = 0

        for item in items:
            proxy = str(item.get("proxy") or "").strip()
            if not proxy:
                continue
            display_name = str(item.get("display_name") or "").strip()
            remark = str(item.get("remark") or "").strip()
            is_active = item.get("is_active")

            if not display_name:
                # 约定：display_name 为空即删除（软删除）
                updated = (
                    ProxyMapping.objects.filter(proxy=proxy, is_active=True)
                    .update(is_active=False, updated_by=user)
                )
                changed += int(updated > 0)
                continue

            defaults = {
                "display_name": display_name,
                "remark": remark,
                "is_active": True if is_active is None else bool(is_active),
                "updated_by": user,
            }
            obj, created = ProxyMapping.objects.update_or_create(proxy=proxy, defaults=defaults)
            if created:
                obj.created_by = user
                obj.save(update_fields=["created_by"])
            changed += 1

        queryset = ProxyMapping.objects.filter(is_active=True).order_by("proxy")
        read = ProxyMappingSerializer(queryset, many=True)
        return Response({"changed": changed, "items": read.data}, status=status.HTTP_200_OK)

    # 兼容：允许 POST 调用同样的 upsert
    def post(self, request: Request) -> Response:
        self.permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]
        return self.put(request)

    def check_permissions(self, request: Request) -> None:
        # PUT 需要 manage 权限
        if request.method.upper() in {"PUT", "POST"}:
            self.permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]
        super().check_permissions(request)

