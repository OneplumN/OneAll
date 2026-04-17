from __future__ import annotations

from typing import Any, Dict, List

import logging

from rest_framework import permissions, serializers, status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse

from apps.assets.models import AssetModel
from apps.assets.services import script_loader
from apps.assets.services.script_loader import ScriptLoadError, load_sync_script, save_sync_script
from apps.core.permissions import RequirePermission


logger = logging.getLogger(__name__)


class AssetModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetModel
        fields = [
            "id",
            "key",
            "label",
            "category",
            "fields",
            "unique_key",
            "script_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "script_id"]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure unique_key only references defined field keys."""

        instance: AssetModel | None = getattr(self, "instance", None)
        fields_value = attrs.get("fields")
        unique_key_value = attrs.get("unique_key")

        if fields_value is None and instance is not None:
            fields_value = instance.fields
        if unique_key_value is None and instance is not None:
            unique_key_value = instance.unique_key

        fields_value = fields_value or []
        unique_key_value = unique_key_value or []

        field_keys = {str(item.get("key")) for item in fields_value if isinstance(item, dict) and item.get("key")}
        missing: List[str] = [str(k) for k in unique_key_value if k not in field_keys]
        if missing:
            raise serializers.ValidationError(
                {"unique_key": [f"unique_key 包含未在字段中定义的 key: {', '.join(missing)}"]}
            )

        return attrs


class AssetModelListCreateView(APIView):
    """List and create asset models.

    - GET: list current models (active by default)
    - POST: create a new model (requires manage permission)
    """

    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request: Request) -> None:
        if request.method.upper() == "POST":
            self.permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]
        super().check_permissions(request)

    def get(self, request: Request) -> Response:
        include_inactive = str(request.query_params.get("include_inactive") or "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        qs = AssetModel.objects.all().order_by("key")
        if not include_inactive:
            qs = qs.filter(is_active=True)
        serializer = AssetModelSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        self.check_permissions(request)
        serializer = AssetModelSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        model = serializer.save()
        read = AssetModelSerializer(model)
        return Response(read.data, status=status.HTTP_201_CREATED)


class AssetModelDetailView(APIView):
    """Retrieve and update a single asset model.

    - GET: fetch model details
    - PUT/PATCH: update fields / unique_key / label / category / is_active (requires manage permission)
    """

    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request: Request) -> None:
        if request.method.upper() in {"PUT", "PATCH", "DELETE"}:
            self.permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]
        super().check_permissions(request)

    def get(self, request: Request, model_id) -> Response:
        model = get_object_or_404(AssetModel, pk=model_id)
        serializer = AssetModelSerializer(model)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request: Request, model_id) -> Response:
        self.check_permissions(request)
        model = get_object_or_404(AssetModel, pk=model_id)
        serializer = AssetModelSerializer(model, data=request.data or {})
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        read = AssetModelSerializer(updated)
        return Response(read.data, status=status.HTTP_200_OK)

    def patch(self, request: Request, model_id) -> Response:
        self.check_permissions(request)
        model = get_object_or_404(AssetModel, pk=model_id)
        serializer = AssetModelSerializer(model, data=request.data or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        read = AssetModelSerializer(updated)
        return Response(read.data, status=status.HTTP_200_OK)


class AssetModelScriptUploadView(APIView):
    """Upload or replace the sync script for a given AssetModel."""

    permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]

    def post(self, request: Request, model_id) -> Response:
        model = get_object_or_404(AssetModel, pk=model_id)
        file_obj = request.FILES.get("file") or request.FILES.get("script")
        if not file_obj:
            return Response(
                {"detail": "未收到脚本文件，请使用 file 字段上传 .py 文件。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        script_id = model.key
        try:
            save_sync_script(script_id, file_obj)
            # Validate that script is importable and exposes run(context)
            load_sync_script(script_id)
        except (ValueError, ScriptLoadError) as exc:
            return Response(
                {"detail": f"脚本校验失败：{exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:  # pragma: no cover - defensive guard for unexpected import errors
            logger.exception("Failed to validate sync script", extra={"model_id": str(model.id), "script_id": script_id})
            return Response(
                {"detail": f"脚本校验失败：{exc.__class__.__name__}: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Bind script to model
        model.script_id = script_id
        model.save(update_fields=["script_id", "updated_at"])

        serializer = AssetModelSerializer(model)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssetModelScriptDownloadView(APIView):
    """Download the current sync script for a given AssetModel."""

    permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]

    def get(self, request: Request, model_id) -> HttpResponse:
        model = get_object_or_404(AssetModel, pk=model_id)
        script_id = model.script_id or model.key
        script_path = script_loader.SCRIPTS_ROOT / f"{script_id}.py"
        if not script_path.exists():
            return HttpResponse(
                f"# 当前模型尚未绑定脚本：{model.key}\n",
                content_type="text/x-python; charset=utf-8",
                status=404,
            )

        content = script_path.read_text(encoding="utf-8")
        filename = f"asset_sync_{model.key}.py"
        response = HttpResponse(
            content,
            content_type="text/x-python; charset=utf-8",
            status=200,
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class AssetModelScriptTemplateView(APIView):
    """Return a Python sync script template for the given AssetModel."""

    permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]

    def get(self, request: Request, model_id) -> HttpResponse:
        model = get_object_or_404(AssetModel, pk=model_id)
        asset_type = model.key
        fields = model.fields or []
        unique_key = model.unique_key or []

        # Build metadata field skeleton
        metadata_lines: List[str] = []
        for field in fields:
            key = str(field.get("key") or "").strip()
            label = str(field.get("label") or "").strip()
            if not key:
                continue
            comment = f"  # {label}" if label else ""
            metadata_lines.append(f'            "{key}": raw.get("{key}", ""),{comment}')

        if not metadata_lines:
            metadata_lines.append('            "example_field": raw.get("example_field", ""),  # 示例字段')

        unique_hint = ", ".join(str(k) for k in unique_key) if unique_key else ""

        primary_key = unique_key[0] if unique_key else ""
        template = f'''"""
资产同步脚本模板（自动生成）

模型 key: {asset_type}
业务唯一键字段: {unique_hint or "未配置（请在模型中设置）"}

说明：
1. 这是一个可直接改造成真实同步逻辑的 HTTP JSON 脚本骨架，不会生成 demo 假数据。
2. 你只需要在本文件中填写 API_URL / 请求头 / 字段映射逻辑，然后重新上传即可。
3. 如果没有配置完成，执行同步会直接报错，避免把示例数据写入正式资产库。
"""

from typing import Any, Dict, List

import requests


API_URL = ""
REQUEST_HEADERS: Dict[str, str] = {{
    # "Authorization": "Bearer <token>",
}}
REQUEST_TIMEOUT_SECONDS = 15
VERIFY_TLS = True
SOURCE_NAME = "Manual"


def fetch_source_rows() -> List[Dict[str, Any]]:
    if not API_URL.strip():
        raise ValueError("请先在脚本中配置 API_URL 或替换 fetch_source_rows() 中的真实取数逻辑")

    response = requests.get(
        API_URL,
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT_SECONDS,
        verify=VERIFY_TLS,
    )
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("items") or payload.get("data") or payload.get("rows") or payload.get("results") or []
    else:
        raise ValueError(f"源接口返回值类型不支持：{{type(payload).__name__}}")

    if not isinstance(rows, list):
        raise ValueError("源接口返回值中未找到列表数据，请检查 fetch_source_rows() 的解析逻辑")
    return rows


def map_row(raw: Dict[str, Any], asset_type: str) -> Dict[str, Any]:
    # TODO: 按真实接口字段修改这里的取值逻辑
    external_id = str(raw.get("{primary_key}") or raw.get("id") or "").strip()
    if not external_id:
        raise ValueError("存在缺少 external_id 的记录，请检查唯一键映射")

    return {{
        "asset_type": asset_type,
        "source": SOURCE_NAME,
        "external_id": external_id,
        "metadata": {{
{chr(10).join(metadata_lines)}
        }},
    }}


def run(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    asset_type = str(context.get("asset_type") or "{asset_type}")
    raw_rows = fetch_source_rows()
    return [map_row(row, asset_type) for row in raw_rows]
'''

        # 使用 HttpResponse 返回原始 Python 源码，避免被 JSON 渲染器二次包装。
        return HttpResponse(
            template,
            content_type="text/x-python; charset=utf-8",
            status=200,
        )
