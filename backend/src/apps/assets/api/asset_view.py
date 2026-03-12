from __future__ import annotations

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.models import AssetRecord
from apps.core.permissions import RequirePermission
from .asset_serializers import AssetRecordSerializer, AssetRecordCreateSerializer, AssetRecordUpdateSerializer


class AssetRecordListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        include_removed = str(request.query_params.get("include_removed") or "").strip().lower() in {"1", "true", "yes", "y"}
        queryset = AssetRecord.objects.all()
        if not include_removed:
            queryset = queryset.filter(is_removed=False)
        queryset = queryset.order_by('-synced_at')
        serializer = AssetRecordSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = AssetRecordCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        read_serializer = AssetRecordSerializer(record)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class AssetRecordImportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    MAX_RECORDS = 500

    def post(self, request: Request) -> Response:
        records = request.data.get('records')
        if not isinstance(records, list) or not records:
            return Response(
                {'detail': 'records 字段必须是非空列表'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(records) > self.MAX_RECORDS:
            return Response(
                {'detail': f'每次最多导入 {self.MAX_RECORDS} 条记录'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        errors: list[dict] = []
        validated_rows: list[dict] = []
        row_meta: list[tuple[int, str, str]] = []
        seen_keys: set[tuple[str, str]] = set()

        for index, payload in enumerate(records):
            serializer = AssetRecordCreateSerializer(data=payload)
            if not serializer.is_valid():
                errors.append({'index': index, 'errors': serializer.errors})
                continue

            data = serializer.validated_data
            source = str(data.get("source") or "")
            external_id = str(data.get("external_id") or "")
            key = (source, external_id)
            if key in seen_keys:
                errors.append(
                    {
                        'index': index,
                        'errors': {
                            'external_id': ['external_id 重复（同一 source + external_id 仅能导入一次）']
                        },
                    }
                )
                continue
            seen_keys.add(key)

            if not data.get("sync_status"):
                data["sync_status"] = "manual"

            validated_rows.append(data)
            row_meta.append((index, source, external_id))

        if not validated_rows:
            return Response(
                {
                    'detail': '所有记录校验失败',
                    'errors': errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_keys: set[tuple[str, str]] = set()
        external_ids_by_source: dict[str, set[str]] = {}
        for _, source, external_id in row_meta:
            external_ids_by_source.setdefault(source, set()).add(external_id)

        for source, external_ids in external_ids_by_source.items():
            if not external_ids:
                continue
            existing = AssetRecord.objects.filter(source=source, external_id__in=external_ids).values_list(
                "source", "external_id"
            )
            existing_keys.update((str(s), str(e)) for s, e in existing)

        instances: list[AssetRecord] = []
        for (index, source, external_id), data in zip(row_meta, validated_rows, strict=False):
            if (source, external_id) in existing_keys:
                errors.append(
                    {
                        'index': index,
                        'errors': {
                            'external_id': ['记录已存在（同一 source + external_id）']
                        },
                    }
                )
                continue
            instances.append(AssetRecord(**data))

        if not instances:
            return Response(
                {
                    'detail': '所有记录均已存在或校验失败',
                    'created': 0,
                    'failed': len(errors),
                    'errors': errors,
                },
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            AssetRecord.objects.bulk_create(instances, batch_size=200)

        created = len(instances)

        if created == 0:
            return Response(
                {
                    'detail': '所有记录校验失败',
                    'errors': errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_status = status.HTTP_200_OK if not errors else status.HTTP_200_OK
        return Response(
            {
                'created': created,
                'failed': len(errors),
                'errors': errors,
            },
            status=response_status,
        )


class AssetRecordQueryView(APIView):
    """资产查询（分页版，用于资产中心列表页）."""

    permission_classes = [permissions.IsAuthenticated]

    DEFAULT_LIMIT = 20
    MAX_LIMIT = 200

    def get(self, request: Request) -> Response:
        from django.db.models import Q

        interface_availability_labels = {"0": "未知", "1": "可用", "2": "不可用"}
        interface_availability_code_by_label = {v: k for k, v in interface_availability_labels.items()}
        interface_availability_label_aliases = {
            "available": "可用",
            "unavailable": "不可用",
            "unknown": "未知",
            "up": "可用",
            "down": "不可用",
            "enabled": "可用",
            "disabled": "停用",
        }

        params = request.query_params
        limit = self._parse_int(params.get("limit"), default=self.DEFAULT_LIMIT, min_value=1, max_value=self.MAX_LIMIT)
        offset = self._parse_int(params.get("offset"), default=0, min_value=0, max_value=10_000_000)
        include_facets = str(params.get("include_facets") or "").strip().lower() in {"1", "true", "yes", "y"}
        include_removed = str(params.get("include_removed") or "").strip().lower() in {"1", "true", "yes", "y"}

        qs = AssetRecord.objects.all()
        if not include_removed:
            qs = qs.filter(is_removed=False)

        sources = self._parse_list(
            params.getlist("source")
            or params.getlist("source[]")
            or params.getlist("sources")
            or params.getlist("sources[]")
        )
        if sources:
            qs = qs.filter(source__in=sources)

        asset_types = self._parse_list(
            params.getlist("asset_type")
            or params.getlist("asset_type[]")
            or params.getlist("asset_types")
            or params.getlist("asset_types[]")
        )
        if asset_types:
            qs = qs.filter(
                Q(metadata__asset_type__in=asset_types)
                | Q(metadata__asset_type__isnull=True)
                | Q(metadata__asset_type="")
            )

        keyword = str(params.get("keyword") or "").strip()
        if keyword:
            qs = self._apply_keyword(qs, keyword)

        proxy = str(params.get("proxy") or "").strip()
        if proxy:
            qs = qs.filter(Q(metadata__proxy=proxy) | Q(metadata__proxy_name=proxy))

        interface_available = str(params.get("interface_available") or "").strip()
        if interface_available:
            raw = interface_available.strip()
            lowered = raw.lower()
            normalized_label = interface_availability_label_aliases.get(lowered, raw)
            normalized_code = interface_availability_code_by_label.get(normalized_label)
            if lowered.isdigit():
                normalized_code = lowered
                normalized_label = interface_availability_labels.get(lowered, normalized_label)

            # “停用”并非接口 available 枚举值，而是 Zabbix 主机状态（host.status=1）。
            # 这里做兼容：当用户用接口可用性筛选“停用”时，映射到主机停用条件。
            if normalized_label == "停用" or lowered == "disabled":
                qs = qs.filter(
                    Q(metadata__status="1")
                    | Q(metadata__status=1)
                    | Q(metadata__host_status="1")
                    | Q(metadata__host_status=1)
                    | Q(sync_status="disabled")
                )
            else:
                iface_q = (
                    Q(metadata__interface_available_label=raw)
                    | Q(metadata__interface_available=raw)
                    | Q(metadata__interface_available_label=normalized_label)
                    | Q(metadata__interface_available=normalized_label)
                )
                if normalized_code:
                    iface_q |= Q(metadata__interface_available=normalized_code)
                    iface_q |= Q(
                        metadata__interface_available_label=interface_availability_labels.get(normalized_code, normalized_label)
                    )
                    try:
                        iface_q |= Q(metadata__interface_available=int(normalized_code))
                    except ValueError:
                        pass
                qs = qs.filter(iface_q)

        app_status = str(params.get("app_status") or "").strip()
        if app_status:
            qs = qs.filter(Q(metadata__app_status=app_status) | Q(metadata__status=app_status))

        online_status = str(params.get("online_status") or "").strip()
        if online_status:
            qs = qs.filter(metadata__online_status=online_status)

        network_type = str(params.get("network_type") or "").strip()
        if network_type:
            qs = qs.filter(Q(metadata__network_type=network_type) | Q(metadata__network=network_type))

        order = str(params.get("order") or "").strip()
        direction = str(params.get("direction") or "").strip().lower()
        qs = self._apply_order(qs, order, direction)

        total = qs.count()
        items = list(qs[offset : offset + limit])
        serializer = AssetRecordSerializer(items, many=True)

        payload: dict = {
            "items": serializer.data,
            "pagination": {"limit": limit, "offset": offset, "total": total},
        }
        if include_facets:
            payload["facets"] = self._build_facets(qs, sources=sources, asset_types=asset_types, network_type=network_type)
        return Response(payload)

    @staticmethod
    def _parse_list(values) -> list[str]:
        result: list[str] = []
        for value in values or []:
            text = str(value).strip()
            if text:
                result.append(text)
        return result

    @staticmethod
    def _parse_int(value, *, default: int, min_value: int, max_value: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(min_value, min(max_value, parsed))

    @staticmethod
    def _apply_keyword(qs, keyword: str):
        from django.db.models import Q

        kw = keyword.strip()
        if not kw:
            return qs
        return qs.filter(
            Q(name__icontains=kw)
            | Q(system_name__icontains=kw)
            | Q(external_id__icontains=kw)
            | Q(metadata__ip__icontains=kw)
            | Q(metadata__host_ip__icontains=kw)
            | Q(metadata__host_name__icontains=kw)
            | Q(metadata__visible_name__icontains=kw)
            | Q(metadata__proxy__icontains=kw)
            | Q(metadata__proxy_name__icontains=kw)
            | Q(metadata__app_code__icontains=kw)
            | Q(metadata__app_name_cn__icontains=kw)
            | Q(metadata__app_name_en__icontains=kw)
            | Q(metadata__app_system__icontains=kw)
        )

    @staticmethod
    def _apply_order(qs, order: str, direction: str):
        # 默认按同步时间倒序
        if not order:
            return qs.order_by("-synced_at")
        direction = direction if direction in {"asc", "desc"} else "desc"
        prefix = "" if direction == "asc" else "-"
        allowed = {
            "synced_at": "synced_at",
            "name": "name",
            "external_id": "external_id",
            "system_name": "system_name",
        }
        field = allowed.get(order)
        if not field:
            return qs.order_by("-synced_at")
        return qs.order_by(f"{prefix}{field}")

    @classmethod
    def _build_facets(cls, qs, *, sources: list[str], asset_types: list[str], network_type: str) -> dict:
        # facets 以“当前查询基准集合”为准（不包含分页）。
        # 避免把全量记录返回到前端，改为后端聚合生成候选项。
        interface_availability_labels = {"0": "未知", "1": "可用", "2": "不可用"}

        def _unique(field: str) -> list[str]:
            values = (
                qs.order_by()
                .values_list(field, flat=True)
                .distinct()
            )
            result: list[str] = []
            for value in values:
                text = "" if value is None else str(value).strip()
                if text and text != "-":
                    result.append(text)
            result.sort()
            return result[:500]

        facets: dict[str, list[str]] = {}

        proxy_values = set(_unique("metadata__proxy")) | set(_unique("metadata__proxy_name"))
        proxy_list = sorted([v for v in proxy_values if v])
        if proxy_list:
            facets["proxy"] = proxy_list[:500]

        iface_labels = set(_unique("metadata__interface_available_label"))
        iface_codes = _unique("metadata__interface_available")
        iface_values: set[str] = set(v for v in iface_labels if v)
        for code in iface_codes:
            text = str(code).strip()
            if not text:
                continue
            iface_values.add(interface_availability_labels.get(text, text))

        host_status_values = set(_unique("metadata__status")) | set(_unique("metadata__host_status")) | set(_unique("sync_status"))
        if "1" in host_status_values or "disabled" in host_status_values:
            iface_values.add("停用")

        if iface_values:
            ordered = [v for v in ["可用", "不可用", "未知", "停用"] if v in iface_values]
            ordered += sorted([v for v in iface_values if v not in {"可用", "不可用", "未知", "停用"}])
            facets["interface_available"] = ordered[:200]

        status_values = set(_unique("metadata__app_status")) | set(_unique("metadata__status"))
        status_list = sorted([v for v in status_values if v])
        if status_list:
            facets["app_status"] = status_list[:200]

        online_values = set(_unique("metadata__online_status"))
        online_list = sorted([v for v in online_values if v])
        if online_list:
            facets["online_status"] = online_list[:50]

        network_values = set(_unique("metadata__network_type")) | set(_unique("metadata__network"))
        network_list = sorted([v for v in network_values if v])
        if network_list:
            facets["network_type"] = network_list[:50]

        source_list = sorted(set(sources or _unique("source")))
        if source_list:
            facets["source"] = source_list

        type_list = sorted(set(asset_types or _unique("metadata__asset_type")))
        if type_list:
            facets["asset_type"] = type_list[:200]

        if network_type and "network_type" in facets and network_type not in facets["network_type"]:
            facets["network_type"] = [network_type] + facets["network_type"]

        return facets


class AssetRecordDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]

    def patch(self, request: Request, record_id) -> Response:
        record = get_object_or_404(AssetRecord, pk=record_id)
        asset_type = (record.metadata or {}).get("asset_type")
        is_workorder = asset_type in {"workorder-host", "workorder"} or str(record.external_id).startswith("workorder:")
        if record.source != AssetRecord.Source.MANUAL or not is_workorder:
            return Response(
                {"detail": "仅支持编辑工单纳管主机信息资产"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = dict(request.data) if isinstance(request.data, dict) else {}
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        metadata["asset_type"] = "workorder-host"
        payload["metadata"] = metadata

        serializer = AssetRecordUpdateSerializer(record, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        read_serializer = AssetRecordSerializer(updated)
        return Response(read_serializer.data, status=status.HTTP_200_OK)
