from __future__ import annotations

import logging
import uuid

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import AuditLog
from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution
from apps.probes.services.probe_monitor_service import handle_heartbeat
from apps.probes.services import (
    probe_metrics_service,
    schedule_config_service,
    schedule_execution_service,
)
from apps.probes.authentication import ensure_probe_authenticated, extract_probe_token

from .serializers import (
    ProbeAgentConfigSerializer,
    ProbeAlertRecordSerializer,
    ProbeNodeSerializer,
    ProbeScheduleSerializer,
    ProbeTokenSerializer,
    ProbeScheduleExecutionSerializer,
)

logger = logging.getLogger(__name__)


class ProbeExecutionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        pagination = {
            "page": self.page.number,
            "page_size": self.get_page_size(self.request) or self.page.paginator.per_page,
            "total_items": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
        }
        payload = {
            "items": data,
            "pagination": pagination,
        }
        extra = getattr(self, "extra_context", None)
        if extra:
            payload.update(extra)
            self.extra_context = {}
        return Response(payload)


def _status_filter_expression(raw_status: str) -> Q:
    normalized = ProbeScheduleExecution.normalize_status(raw_status)
    expression = Q(status__iexact=normalized)
    for alias in ProbeScheduleExecution.status_aliases(normalized):
        expression |= Q(status__iexact=alias)
    return expression


class ProbeNodeViewSet(viewsets.ModelViewSet):
    queryset = ProbeNode.objects.order_by("name")
    serializer_class = ProbeNodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    # heartbeat/tasks endpoints are deprecated (all probe communications are via gRPC).

    @action(
        detail=True,
        methods=["get"],
        url_path="metrics/history",
        permission_classes=[permissions.IsAuthenticated],
    )
    def metrics_history(self, request, *args, **kwargs):
        probe = self.get_object()
        hours = self._parse_int_param(request, "hours", default=6, min_value=1, max_value=72)
        interval = self._parse_int_param(request, "interval_minutes", default=5, min_value=1, max_value=60)
        history = probe_metrics_service.get_runtime_history(
            probe_id=str(probe.id),
            hours=hours,
            interval_minutes=interval,
        )
        payload = {
            "from": history["from"].isoformat(),
            "to": history["to"].isoformat(),
            "points": [
                {
                    **point,
                    "timestamp": point["timestamp"].isoformat(),
                }
                for point in history["points"]
            ],
        }
        return Response(payload, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="results/stats",
        permission_classes=[permissions.IsAuthenticated],
    )
    def result_stats(self, request, *args, **kwargs):
        probe = self.get_object()
        hours = self._parse_int_param(request, "hours", default=24, min_value=1, max_value=168)
        interval = self._parse_int_param(request, "interval_minutes", default=15, min_value=5, max_value=120)
        stats = probe_metrics_service.get_result_statistics(
            probe_id=str(probe.id),
            hours=hours,
            interval_minutes=interval,
        )
        payload = {
            "from": stats["from"].isoformat(),
            "to": stats["to"].isoformat(),
            "points": [
                {
                    **point,
                    "timestamp": point["timestamp"].isoformat(),
                }
                for point in stats["points"]
            ],
            "total": stats["total"],
        }
        return Response(payload, status=status.HTTP_200_OK)


    @action(
        detail=True,
        methods=["get", "put"],
        url_path="config",
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )
    def agent_config(self, request, *args, **kwargs):
        probe = self.get_object()
        if request.method.lower() == "get":
            if not request.user.is_authenticated:
                ensure_probe_authenticated(request, probe)
            return Response(self._build_agent_config_response(probe), status=status.HTTP_200_OK)
        if not request.user.is_authenticated:
            raise PermissionDenied("需要登录后才能更新配置")
        serializer = ProbeAgentConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        if not payload.get("version"):
            payload["version"] = timezone.now().isoformat()
        probe.agent_config = payload
        probe.save(update_fields=["agent_config", "updated_at"])
        return Response(payload, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="runtime", permission_classes=[permissions.IsAuthenticated])
    def runtime(self, request, *args, **kwargs):
        probe = self.get_object()
        heartbeat_delay = None
        if probe.last_heartbeat_at:
            heartbeat_delay = (timezone.now() - probe.last_heartbeat_at).total_seconds()
        stats = (
            ProbeScheduleExecution.objects.filter(probe=probe)
            .values("status")
            .annotate(total=Count("id"))
        )
        task_summary = {
            ProbeScheduleExecution.Status.SCHEDULED: 0,
            ProbeScheduleExecution.Status.RUNNING: 0,
            ProbeScheduleExecution.Status.SUCCEEDED: 0,
            ProbeScheduleExecution.Status.FAILED: 0,
            ProbeScheduleExecution.Status.MISSED: 0,
        }
        for item in stats:
            status_key = item["status"]
            if status_key in task_summary:
                task_summary[status_key] = item["total"]
        payload = {
            "probe": {
                "id": probe.id,
                "name": probe.name,
                "status": probe.status,
                "location": probe.location,
                "network_type": probe.network_type,
                "supported_protocols": probe.supported_protocols,
                "last_heartbeat_at": probe.last_heartbeat_at,
                "last_authenticated_at": probe.last_authenticated_at,
            },
            "heartbeat_delay_seconds": heartbeat_delay,
            "tasks": task_summary,
            "resource_metrics": self._build_resource_metrics(probe.runtime_metrics or {}),
        }
        return Response(payload, status=status.HTTP_200_OK)

    def _build_resource_metrics(self, metrics: dict | None) -> dict:
        data = metrics if isinstance(metrics, dict) else {}
        return {
            "cpu_usage": data.get("cpu_usage"),
            "memory_usage_mb": data.get("memory_usage_mb"),
            "load_avg": data.get("load_avg"),
            "task_queue_depth": data.get("task_queue_depth"),
            "active_tasks": data.get("active_tasks"),
            "queue_latency_ms": data.get("queue_latency_ms"),
            "reported_at": data.get("reported_at"),
        }

    def _get_or_create_probe(self, request, payload: dict, token: str | None) -> ProbeNode:
        try:
            probe = self.get_object()
        except Http404:
            if not token:
                raise AuthenticationFailed("Probe token required")
            return self._auto_register_probe(payload, token)
        ensure_probe_authenticated(request, probe, token)
        return probe

    def _auto_register_probe(self, payload: dict, token: str) -> ProbeNode:
        node_id = self.kwargs.get(self.lookup_field or "pk")
        if not node_id:
            raise Http404
        try:
            probe_uuid = uuid.UUID(str(node_id))
        except (TypeError, ValueError):
            raise Http404
        supported_protocols = payload.get("supported_protocols") or []
        status_value = payload.get("status", "offline")
        probe, created = ProbeNode.objects.get_or_create(
            id=probe_uuid,
            defaults={
                "name": f"probe-{str(probe_uuid)[:8]}",
                "location": "自动注册",
                "network_type": "external",
                "supported_protocols": supported_protocols,
                "status": status_value,
            },
        )
        probe.set_api_token(token)
        probe.touch_authenticated()
        if created:
            logger.info("Auto registered probe %s via heartbeat", probe_uuid)
        return probe
    
    @action(detail=True, methods=["post"], url_path="token", permission_classes=[permissions.IsAuthenticated])
    def rotate_token(self, request, *args, **kwargs):
        probe = self.get_object()
        serializer = ProbeTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_token = serializer.validated_data["token"]
        probe.set_api_token(new_token)
        probe.touch_authenticated()
        return Response({"token": new_token, "token_hint": probe.api_token_hint}, status=status.HTTP_200_OK)

    def _build_agent_config_response(self, probe: ProbeNode) -> dict:
        config = dict(probe.agent_config or {})
        if not config.get("version"):
            timestamp = probe.updated_at or timezone.now()
            config["version"] = timestamp.isoformat()
        return config

    def _parse_int_param(self, request, name: str, *, default: int, min_value: int, max_value: int) -> int:
        raw = request.query_params.get(name)
        if raw is None:
            return default
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return default
        return max(min_value, min(max_value, value))


class RecentProbeAlertView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 50

    def get(self, request, *args, **kwargs):
        limit = self._parse_limit(request.query_params.get("limit"))
        logs = list(
            AuditLog.objects.filter(action="probes.alert")
            .order_by("-occurred_at")
            .values("id", "metadata", "occurred_at")[:limit]
        )
        if not logs:
            return Response({"items": []}, status=status.HTTP_200_OK)

        schedule_ids = {entry.get("metadata", {}).get("schedule_id") for entry in logs}
        probe_ids = {entry.get("metadata", {}).get("probe_id") for entry in logs}
        schedule_map = {
            str(schedule.id): schedule.name
            for schedule in ProbeSchedule.objects.filter(id__in=[sid for sid in schedule_ids if sid]).only("id", "name")
        }
        probe_map = {
            str(probe.id): probe.name
            for probe in ProbeNode.objects.filter(id__in=[pid for pid in probe_ids if pid]).only("id", "name")
        }

        records: list[dict] = []
        for log in logs:
            metadata = log.get("metadata") or {}
            schedule_id = metadata.get("schedule_id")
            probe_id = metadata.get("probe_id")
            status_value = metadata.get("status") or ""
            record = {
                "id": log.get("id"),
                "execution_id": metadata.get("execution_id"),
                "schedule_id": schedule_id,
                "schedule_name": schedule_map.get(str(schedule_id), "") if schedule_id else "",
                "probe_id": probe_id,
                "probe_name": probe_map.get(str(probe_id), "") if probe_id else "",
                "status": status_value,
                "severity": self._resolve_severity(status_value),
                "threshold": metadata.get("threshold") or 1,
                "alert_contacts": metadata.get("alert_contacts") or [],
                "occurred_at": log.get("occurred_at"),
                "message": metadata.get("message") or "",
            }
            records.append(record)

        serializer = ProbeAlertRecordSerializer(records, many=True)
        return Response({"items": serializer.data}, status=status.HTTP_200_OK)

    def _parse_limit(self, raw: str | None) -> int:
        if raw is None:
            return self.DEFAULT_LIMIT
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return self.DEFAULT_LIMIT
        return max(1, min(value, self.MAX_LIMIT))

    def _resolve_severity(self, status_value: str) -> str:
        normalized = (status_value or "").lower()
        if normalized == ProbeScheduleExecution.Status.FAILED:
            return "critical"
        if normalized == ProbeScheduleExecution.Status.MISSED:
            return "warning"
        return "info"


class ProbeScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ProbeScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ProbeSchedule.objects.select_related("monitoring_request").prefetch_related("probes").all()
        status_param = self.request.query_params.get("status")
        source_param = self.request.query_params.get("source")
        probe_param = self.request.query_params.get("probe_id")
        if status_param:
            queryset = queryset.filter(status=status_param)
        if source_param:
            queryset = queryset.filter(source_type=source_param)
        if probe_param:
            queryset = queryset.filter(probes__id=probe_param)
        return queryset.order_by("name").distinct()

    def perform_create(self, serializer):
        schedule = serializer.save(
            source_type=ProbeSchedule.Source.MANUAL,
            status=ProbeSchedule.Status.ACTIVE,
        )
        probe_ids = list(schedule.probes.values_list("id", flat=True))
        schedule_config_service.request_probe_refresh(probe_ids)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        schedule = self.get_object()

        serializer = self.get_serializer(schedule, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if schedule.source_type == ProbeSchedule.Source.MANUAL:
            updated = serializer.save()
            probe_ids = list(updated.probes.values_list("id", flat=True))
            schedule_config_service.request_probe_refresh(probe_ids)
            return Response(self.get_serializer(updated).data)

        if schedule.source_type != ProbeSchedule.Source.MONITORING_REQUEST:
            raise PermissionDenied("非手工调度不允许直接修改")

        monitoring_request = schedule.monitoring_request or getattr(schedule.monitoring_job, "request", None)
        job = schedule.monitoring_job
        if not monitoring_request or not job:
            return Response({"detail": "该调度缺少关联申请/任务，无法编辑"}, status=status.HTTP_400_BAD_REQUEST)

        is_admin = bool(getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False))
        if not is_admin and monitoring_request.created_by_id and str(monitoring_request.created_by_id) != str(request.user.id):
            return Response({"detail": "仅允许申请人编辑该调度"}, status=status.HTTP_403_FORBIDDEN)
        if not is_admin and monitoring_request.created_by_id is None:
            return Response({"detail": "缺少申请人信息，无法编辑"}, status=status.HTTP_400_BAD_REQUEST)

        old_probe_ids = set(str(pid) for pid in schedule.probes.values_list("id", flat=True))

        validated = dict(serializer.validated_data)

        # start_at / end_at 属于调度自身字段，不参与 MonitoringRequest -> ProbeSchedule 的映射
        start_at = validated.pop("start_at", None) if "start_at" in validated else None
        end_at = validated.pop("end_at", None) if "end_at" in validated else None

        # 同步编辑：将 ProbeSchedule 的编辑映射回 MonitoringRequest/MonitoringJob/metadata，再触发 sync
        if "name" in validated:
            monitoring_request.title = validated.pop("name")
        if "description" in validated:
            monitoring_request.description = validated.pop("description") or ""
        if "target" in validated:
            monitoring_request.target = validated.pop("target")
        if "protocol" in validated:
            monitoring_request.protocol = validated.pop("protocol")

        if "frequency_minutes" in validated:
            freq = int(validated.pop("frequency_minutes") or 1)
            monitoring_request.frequency_minutes = freq
            job.frequency_minutes = freq

        metadata = dict(monitoring_request.metadata or {})

        if "timeout_seconds" in validated:
            metadata["timeout_seconds"] = int(validated.pop("timeout_seconds"))
        if "expected_status_codes" in validated:
            codes = validated.pop("expected_status_codes") or []
            normalized = sorted({int(code) for code in codes if 100 <= int(code) <= 599})
            metadata["expected_status_codes"] = normalized if normalized else [200]
        if "alert_threshold" in validated:
            metadata["alert_threshold"] = int(validated.pop("alert_threshold"))
        if "alert_contacts" in validated:
            contacts = validated.pop("alert_contacts") or []
            metadata["alert_contacts"] = [str(c).strip() for c in contacts if str(c).strip()]
        if "probe_ids" in validated:
            probe_ids = validated.pop("probe_ids") or []
            metadata["probe_ids"] = [str(v) for v in probe_ids]

        monitoring_request.metadata = metadata
        monitoring_request.updated_by = request.user
        job.save(update_fields=["frequency_minutes", "updated_at"])
        monitoring_request.save(update_fields=[
            "title",
            "description",
            "target",
            "protocol",
            "frequency_minutes",
            "metadata",
            "updated_by",
            "updated_at",
        ])

        from apps.probes.services.probe_schedule_service import sync_schedule_from_job

        updated_schedule = sync_schedule_from_job(job)
        if start_at is not None or end_at is not None:
            if start_at is not None:
                updated_schedule.start_at = start_at
            if end_at is not None:
                updated_schedule.end_at = end_at
            updated_schedule.save(update_fields=["start_at", "end_at", "updated_at"])

        new_probe_ids = set(str(pid) for pid in updated_schedule.probes.values_list("id", flat=True))
        schedule_config_service.request_probe_refresh(list(old_probe_ids | new_probe_ids))

        return Response(self.get_serializer(updated_schedule).data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        # 兼容 DRF 基类逻辑：实际更新走 update() 覆盖
        return super().perform_update(serializer)

    def destroy(self, request, *args, **kwargs):
        schedule = self.get_object()
        if schedule.source_type != ProbeSchedule.Source.MANUAL:
            raise PermissionDenied("非手工调度不允许删除")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="pause")
    def pause(self, request, *args, **kwargs):
        schedule = self.get_object()
        reason = request.data.get("reason")
        schedule.pause(reason)
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="resume")
    def resume(self, request, *args, **kwargs):
        schedule = self.get_object()
        schedule.activate()
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, *args, **kwargs):
        schedule = self.get_object()
        reason = request.data.get("reason")
        schedule.archive(reason)
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="executions")
    def executions(self, request, *args, **kwargs):
        schedule = self.get_object()
        queryset = ProbeScheduleExecution.objects.filter(schedule=schedule).select_related("probe").order_by("-scheduled_at")
        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(_status_filter_expression(status_param))
        page = self.paginate_queryset(queryset)
        serializer = ProbeScheduleExecutionSerializer(page or queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class ProbeScheduleExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProbeScheduleExecution.objects.select_related("schedule", "probe").all().order_by("-scheduled_at")
    serializer_class = ProbeScheduleExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ProbeExecutionPagination

    def get_queryset(self):
        queryset = self.queryset
        schedule_id = self.request.query_params.get("schedule_id")
        probe_id = self.request.query_params.get("probe_id")
        status_param = self.request.query_params.get("status")
        started_after = self.request.query_params.get("started_after")
        started_before = self.request.query_params.get("started_before")
        target = self.request.query_params.get("target")
        protocol = self.request.query_params.get("protocol")

        if schedule_id:
            queryset = queryset.filter(schedule_id=schedule_id)
        if probe_id:
            queryset = queryset.filter(probe_id=probe_id)
        if status_param:
            queryset = queryset.filter(_status_filter_expression(status_param))
        parsed_after = self._parse_datetime(started_after)
        if parsed_after:
            queryset = queryset.filter(scheduled_at__gte=parsed_after)
        parsed_before = self._parse_datetime(started_before)
        if parsed_before:
            queryset = queryset.filter(scheduled_at__lte=parsed_before)
        if target:
            queryset = queryset.filter(schedule__target__icontains=target)
        if protocol:
            queryset = queryset.filter(schedule__protocol=protocol)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        aggregates = self._build_aggregates(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            if getattr(self, "paginator", None):
                self.paginator.extra_context = {"aggregates": aggregates}
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        payload = {
            "items": serializer.data,
            "aggregates": aggregates,
            "pagination": {
                "page": 1,
                "page_size": len(serializer.data),
                "total_items": len(serializer.data),
                "total_pages": 1,
            },
        }
        return Response(payload)

    def _build_aggregates(self, queryset):
        total_count = queryset.count()
        average_response = queryset.aggregate(avg=Avg("response_time_ms")).get("avg")
        status_counts_qs = queryset.values("status").annotate(total=Count("id"))
        status_counts = self._aggregate_status_counts(status_counts_qs)
        success = status_counts[ProbeScheduleExecution.Status.SUCCEEDED]
        executed_total = (
            success
            + status_counts[ProbeScheduleExecution.Status.FAILED]
            + status_counts[ProbeScheduleExecution.Status.MISSED]
        )
        success_rate = round((success / executed_total) * 100, 1) if executed_total else 0.0
        return {
            "total_count": total_count,
            "status_counts": status_counts,
            "average_response_time_ms": average_response,
            "success_rate": success_rate,
        }

    def _aggregate_status_counts(self, queryset_counts: list[dict]) -> dict[str, int]:
        normalized_counts = {
            ProbeScheduleExecution.Status.SCHEDULED: 0,
            ProbeScheduleExecution.Status.RUNNING: 0,
            ProbeScheduleExecution.Status.SUCCEEDED: 0,
            ProbeScheduleExecution.Status.FAILED: 0,
            ProbeScheduleExecution.Status.MISSED: 0,
        }
        for entry in queryset_counts:
            status_key = entry["status"]
            count = entry["total"]
            normalized_key = ProbeScheduleExecution.normalize_status(status_key)
            if normalized_key in normalized_counts:
                normalized_counts[normalized_key] += count
        return normalized_counts

    def _parse_datetime(self, value: str | None):
        if not value:
            return None
        candidate = value.strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            return timezone.datetime.fromisoformat(candidate)
        except ValueError:
            return None
