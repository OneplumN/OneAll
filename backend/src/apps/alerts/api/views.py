from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import AlertCheck, AlertCheckExecution, AlertEvent, AlertSchedule
from apps.alerts.services import build_system_overview
from apps.core.permissions import RequireAnyPermission, RequirePermission
from apps.monitoring.models import MonitoringRequest
from apps.probes.api.serializers import ProbeScheduleSerializer
from apps.probes.models import ProbeSchedule


def _primary_schedule_for_check(check: AlertCheck) -> AlertSchedule | None:
    schedules = getattr(check, "schedules", None) or check.schedules
    return schedules.filter(status=AlertSchedule.Status.ACTIVE).first() or schedules.first()


def _executor_ref_for_check(check: AlertCheck) -> str:
    latest_exec = (
        AlertCheckExecution.objects.filter(schedule__alert_check=check)
        .exclude(executor_ref="")
        .order_by("-scheduled_at")
        .first()
    )
    return latest_exec.executor_ref if latest_exec else ""


def _metadata_for_check(
    check: AlertCheck,
    primary_schedule: AlertSchedule | None,
    request_metadata_map: dict[str, dict] | None = None,
) -> dict:
    if primary_schedule and primary_schedule.metadata:
        return primary_schedule.metadata
    if check.source_type == AlertCheck.SourceType.MONITORING_REQUEST and check.source_id:
        request_id = str(check.source_id)
        if request_metadata_map and request_id in request_metadata_map:
            return request_metadata_map[request_id]
        request = MonitoringRequest.objects.filter(id=check.source_id).only("metadata").first()
        return dict(request.metadata or {}) if request else {}
    return {}


def _serialize_check_summary(check: AlertCheck, *, request_metadata_map: dict[str, dict] | None = None) -> dict:
    schedules = getattr(check, "schedules", None) or check.schedules
    schedule_count = schedules.count()
    primary_schedule = _primary_schedule_for_check(check)
    metadata = _metadata_for_check(check, primary_schedule, request_metadata_map=request_metadata_map)

    return {
        "id": str(check.id),
        "name": check.name,
        "target": check.target,
        "protocol": check.protocol,
        "source_type": check.source_type,
        "source_id": str(check.source_id) if check.source_id else None,
        "executor_type": check.executor_type,
        "executor_ref": _executor_ref_for_check(check),
        "schedule_count": schedule_count,
        "is_active": bool(getattr(check, "is_active", True)),
        "metadata": metadata or {},
        "created_at": check.created_at.isoformat(),
        "updated_at": check.updated_at.isoformat(),
    }


def _serialize_check_detail(check: AlertCheck) -> dict:
    schedules = (
        AlertSchedule.objects.filter(alert_check=check)
        .order_by("id")
        .prefetch_related("executions")
    )

    schedules_payload = []
    for schedule in schedules:
        executions = getattr(schedule, "executions", None) or schedule.executions
        last_exec = executions.order_by("-scheduled_at").first()

        schedules_payload.append(
            {
                "id": str(schedule.id),
                "frequency_minutes": schedule.frequency_minutes,
                "status": schedule.status,
                "start_at": schedule.start_at.isoformat() if schedule.start_at else None,
                "end_at": schedule.end_at.isoformat() if schedule.end_at else None,
                "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
                "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
                "metadata": schedule.metadata or {},
                "last_execution": None
                if not last_exec
                else {
                    "id": str(last_exec.id),
                    "status": last_exec.status,
                    "scheduled_at": last_exec.scheduled_at.isoformat()
                    if last_exec.scheduled_at
                    else None,
                    "started_at": last_exec.started_at.isoformat()
                    if last_exec.started_at
                    else None,
                    "finished_at": last_exec.finished_at.isoformat()
                    if last_exec.finished_at
                    else None,
                    "response_time_ms": last_exec.response_time_ms,
                    "status_code": last_exec.status_code,
                    "error_message": last_exec.error_message,
                },
            }
        )

    probe_ids: list[str] = []
    probes_payload: list[dict] = []
    if check.source_type == AlertCheck.SourceType.PROBE_SCHEDULE and check.source_id:
        source_schedule = ProbeSchedule.objects.filter(id=check.source_id).prefetch_related("probes").first()
        if source_schedule:
            probe_ids = [str(probe.id) for probe in source_schedule.probes.all()]
            probes_payload = [
                {
                    "id": str(probe.id),
                    "name": probe.name,
                    "location": probe.location,
                    "network_type": probe.network_type,
                    "status": probe.status,
                }
                for probe in source_schedule.probes.all()
            ]

    request_metadata_map = _monitoring_request_metadata_map([check])
    payload = {
        "check": {
            **_serialize_check_summary(check, request_metadata_map=request_metadata_map),
            "probe_ids": probe_ids,
            "probes": probes_payload,
        },
        "schedules": schedules_payload,
    }
    return payload


def _listable_checks_queryset():
    manual_schedule_ids = list(
        ProbeSchedule.objects.filter(
        source_type=ProbeSchedule.Source.MANUAL
        ).values_list("id", flat=True)
    )
    return AlertCheck.objects.filter(
        Q(source_type=AlertCheck.SourceType.MONITORING_REQUEST)
        | Q(
            source_type=AlertCheck.SourceType.PROBE_SCHEDULE,
            source_id__in=manual_schedule_ids,
        )
    )


def _monitoring_request_metadata_map(checks) -> dict[str, dict]:
    request_ids = [
        check.source_id
        for check in checks
        if check.source_type == AlertCheck.SourceType.MONITORING_REQUEST and check.source_id
    ]
    if not request_ids:
        return {}
    return {
        str(item["id"]): dict(item["metadata"] or {})
        for item in MonitoringRequest.objects.filter(id__in=request_ids).values("id", "metadata")
    }


class AlertEventListView(APIView):
    """Read-only list of recent alert events."""

    permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.module.access")]

    DEFAULT_LIMIT = 100
    MAX_LIMIT = 200

    def get(self, request: Request) -> Response:
        qs = AlertEvent.objects.order_by("-created_at")

        source = request.query_params.get("source")
        if source:
            qs = qs.filter(source=source)

        severity = request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity)

        limit = self._parse_limit(request.query_params.get("limit"))
        qs = qs[:limit]

        data = [
            {
                "id": str(event.id),
                "source": event.source,
                "event_type": event.event_type,
                "severity": event.severity,
                "title": event.title,
                "message": event.message,
                "status": event.status,
                "created_at": event.created_at.isoformat(),
                "sent_at": event.sent_at.isoformat() if event.sent_at else None,
                "context": event.context or {},
            }
            for event in qs
        ]
        return Response(data)

    def _parse_limit(self, raw: str | None) -> int:
        if raw is None:
            return self.DEFAULT_LIMIT
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return self.DEFAULT_LIMIT
        return max(1, min(value, self.MAX_LIMIT))


class AlertCheckListView(APIView):
    """当前所有告警检查（AlertCheck）及其基础信息。"""

    permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.module.access")]

    def get(self, request: Request) -> Response:
        qs = _listable_checks_queryset().order_by("created_at").prefetch_related("schedules")

        source_type = request.query_params.get("source_type")
        if source_type:
            qs = qs.filter(source_type=source_type)

        executor_type = request.query_params.get("executor_type")
        if executor_type:
            qs = qs.filter(executor_type=executor_type)

        checks = list(qs)
        request_metadata_map = _monitoring_request_metadata_map(checks)
        data = [
            _serialize_check_summary(check, request_metadata_map=request_metadata_map)
            for check in checks
        ]
        return Response(data)

    def post(self, request: Request) -> Response:
        serializer = ProbeScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save()
        check = get_object_or_404(
            AlertCheck.objects.prefetch_related("schedules"),
            source_type=AlertCheck.SourceType.PROBE_SCHEDULE,
            source_id=schedule.id,
        )
        return Response(_serialize_check_summary(check), status=status.HTTP_201_CREATED)


class AlertCheckScheduleListView(APIView):
    """查看某个告警检查下的所有调度及最近一次执行。"""

    permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.module.access")]

    def get(self, request: Request, check_id: str) -> Response:
        check = get_object_or_404(AlertCheck, id=check_id)
        return Response(_serialize_check_detail(check))


class AlertCheckDetailView(APIView):
    """
    监控策略详情 / 更新接口。

    目前仅支持部分字段更新（例如 is_active），用于前端“策略启停”等简单配置。
    """

    permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.module.access")]

    def patch(self, request: Request, check_id: str) -> Response:
        check = get_object_or_404(AlertCheck, id=check_id)

        payload = request.data or {}

        # 策略启停：更新 AlertCheck.is_active，并同步其下所有 ACTIVE/PAUSED 调度的状态。
        if "is_active" in payload and len(payload.keys()) == 1:
            is_active = bool(payload.get("is_active"))
            if check.is_active != is_active:
                check.is_active = is_active
                check.save(update_fields=["is_active", "updated_at"])

                # 将调度状态与策略状态对齐：启用 -> ACTIVE，停用 -> PAUSED（不动 ARCHIVED）
                if is_active:
                    AlertSchedule.objects.filter(
                        alert_check=check,
                        status=AlertSchedule.Status.PAUSED,
                    ).update(status=AlertSchedule.Status.ACTIVE)
                else:
                    AlertSchedule.objects.filter(
                        alert_check=check,
                        status=AlertSchedule.Status.ACTIVE,
                    ).update(status=AlertSchedule.Status.PAUSED)

            check.refresh_from_db()
            return Response(_serialize_check_summary(check))

        if check.source_type != AlertCheck.SourceType.PROBE_SCHEDULE or not check.source_id:
            return Response(
                {"detail": "该策略来源于监控申请，当前不支持在监控策略页直接修改。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule = get_object_or_404(ProbeSchedule, id=check.source_id)
        if schedule.source_type != ProbeSchedule.Source.MANUAL:
            return Response(
                {"detail": "该策略不是手工策略，当前不支持在监控策略页直接修改。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProbeScheduleSerializer(instance=schedule, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        check.refresh_from_db()
        return Response(_serialize_check_summary(check))

    def delete(self, request: Request, check_id: str) -> Response:
        check = get_object_or_404(AlertCheck, id=check_id)

        if check.source_type != AlertCheck.SourceType.PROBE_SCHEDULE or not check.source_id:
            return Response(
                {"detail": "该策略来源于监控申请，当前不支持在监控策略页直接删除。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule = get_object_or_404(ProbeSchedule, id=check.source_id)
        if schedule.source_type != ProbeSchedule.Source.MANUAL:
            return Response(
                {"detail": "该策略不是手工策略，当前不支持在监控策略页直接删除。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule.delete()
        check.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AlertSystemOverviewView(APIView):
    """System-level monitoring overview for honeycomb visualization."""

    permission_classes = [
        permissions.IsAuthenticated,
        RequireAnyPermission("alerts.module.access", "monitoring.overview.view"),
    ]

    def get(self, request: Request) -> Response:
        return Response(build_system_overview())
