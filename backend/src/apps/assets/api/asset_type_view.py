from __future__ import annotations

from typing import Any, Dict, List

from django.http import Http404
from rest_framework import permissions
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.types import get_asset_type, list_asset_types
from apps.core.permissions import RequirePermission
from apps.settings.services.system_settings_service import get_integration_settings, update_integration_settings


class AssetTypeSettingsSerializer(serializers.Serializer):
    unique_fields = serializers.ListField(
        child=serializers.CharField(allow_blank=False, trim_whitespace=True),
        required=False,
    )
    extra_fields = serializers.ListField(child=serializers.DictField(), required=False)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        definition = self.context["definition"]
        unique_fields = attrs.get("unique_fields")
        if unique_fields is not None:
            allowed_fields = set(definition.all_fields())
            invalid = [field for field in unique_fields if field not in allowed_fields]
            if invalid:
                raise serializers.ValidationError(
                    {"unique_fields": [f"仅允许使用当前资产类型字段：{', '.join(invalid)}"]}
                )
        return attrs

    def validate_unique_fields(self, value: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()
        for item in value:
            key = str(item or "").strip()
            if not key or key in seen:
                continue
            cleaned.append(key)
            seen.add(key)
        if not cleaned:
            raise serializers.ValidationError("至少需要一个唯一键字段")
        return cleaned

    def validate_extra_fields(self, value: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned: List[Dict[str, Any]] = []
        seen: set[str] = set()
        builtin_fields = set(self.context["definition"].all_fields())
        for item in value or []:
            key = str(item.get("key") or "").strip()
            label = str(item.get("label") or "").strip()
            field_type = str(item.get("type") or "string").strip() or "string"
            if not key or not label:
                raise serializers.ValidationError("管理字段必须同时包含 key 和 label")
            if key in builtin_fields:
                raise serializers.ValidationError(f"管理字段 key 不能与内置字段重复：{key}")
            if key in seen:
                raise serializers.ValidationError(f"管理字段 key 重复：{key}")
            options = item.get("options") or []
            if field_type == "enum":
                options = [str(option).strip() for option in options if str(option).strip()]
                if not options:
                    raise serializers.ValidationError(f"枚举字段 {key} 必须提供 options")
            else:
                options = []
            cleaned.append(
                {
                    "key": key,
                    "label": label,
                    "type": field_type,
                    "options": options,
                    "required": bool(item.get("required")),
                    "list_visible": bool(item.get("list_visible")),
                }
            )
            seen.add(key)
        return cleaned


class AssetTypeListView(APIView):
    """列出当前系统支持的资产类型定义。

    主要用于前端资产中心等模块按类型渲染列表与配置。
    """

    # 与资产列表保持一致：暂时仅要求登录，细粒度权限后续统一收口。
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        definitions = list_asset_types()
        asset_settings = get_integration_settings("assets")
        type_overrides: dict = asset_settings.get("types") or {}

        data = [
            {
                "key": definition.key,
                "label": definition.label,
                "category": definition.category,
                "default_source": definition.default_source,
                "unique_fields": list(
                    (type_overrides.get(definition.key) or {}).get("unique_fields") or definition.unique_fields
                ),
                "default_unique_fields": list(definition.unique_fields),
                # 暴露该资产类型在 metadata 中常用的业务字段集合，供前端做「唯一字段」等配置时使用
                "fields": definition.all_fields(),
                # 从系统设置中读取扩展字段定义（如果存在）
                "extra_fields": list(
                    (type_overrides.get(definition.key) or {}).get("extra_fields") or []
                ),
            }
            for definition in definitions
        ]
        return Response(data)


class AssetTypeDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]

    def patch(self, request: Request, type_key: str) -> Response:
        definition = get_asset_type(type_key)
        if definition is None:
            raise Http404("Asset type not found")

        serializer = AssetTypeSettingsSerializer(data=request.data or {}, context={"definition": definition})
        serializer.is_valid(raise_exception=True)

        asset_settings = get_integration_settings("assets")
        type_overrides = dict(asset_settings.get("types") or {})
        current = dict(type_overrides.get(type_key) or {})
        current.update(serializer.validated_data)
        type_overrides[type_key] = current
        update_integration_settings("assets", {"types": type_overrides})

        return Response(
            {
                "key": definition.key,
                "label": definition.label,
                "category": definition.category,
                "default_source": definition.default_source,
                "unique_fields": list(current.get("unique_fields") or definition.unique_fields),
                "default_unique_fields": list(definition.unique_fields),
                "fields": definition.all_fields(),
                "extra_fields": list(current.get("extra_fields") or []),
            },
            status=status.HTTP_200_OK,
        )
