from __future__ import annotations

from typing import Any, Dict, List

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import RequirePermission
from apps.probes.models import ProbeSchedule, ProbeScheduleExecution


def _parse_int(value: Any, default: int, *, min_value: int, max_value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_value, min(max_value, parsed))


def _normalize_expected_status(value: Any) -> int | list[int] | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, list):
        normalized: list[int] = []
        for item in value:
            try:
                code = int(item)
            except (TypeError, ValueError):
                continue
            if 100 <= code <= 599:
                normalized.append(code)
        normalized = sorted(set(normalized))
        if not normalized:
            return None
        if len(normalized) == 1:
            return normalized[0]
        return normalized
    return None


class DashboardDetectionGridView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("monitoring.overview.view")]

    def get(self, request: Request) -> Response:
        limit = _parse_int(request.query_params.get("limit"), 50, min_value=1, max_value=200)

        schedules = list(
            ProbeSchedule.objects.filter(status=ProbeSchedule.Status.ACTIVE)
            .exclude(protocol="CERTIFICATE")
            .select_related("monitoring_request")
            .order_by("-updated_at")[:limit]
        )
        schedule_ids = [s.id for s in schedules]
        latest_by_schedule: dict[str, ProbeScheduleExecution] = {}
        if schedule_ids:
            executions = (
                ProbeScheduleExecution.objects.filter(schedule_id__in=schedule_ids)
                .select_related("probe", "schedule")
                .order_by("schedule_id", "-scheduled_at")
            )
            for execution in executions:
                key = str(execution.schedule_id)
                if key not in latest_by_schedule:
                    latest_by_schedule[key] = execution

        rows: List[Dict[str, Any]] = []
        for schedule in schedules:
            metadata = schedule.metadata or {}
            expected = _normalize_expected_status(metadata.get("expected_status_codes"))
            if expected is None and schedule.monitoring_request_id:
                request_meta = getattr(schedule.monitoring_request, "metadata", None) or {}
                expected = _normalize_expected_status(request_meta.get("expected_status_codes"))

            actual_status: int | None = None
            latest = latest_by_schedule.get(str(schedule.id))
            raw_code = latest.status_code if latest else None
            try:
                actual_status = int(raw_code) if raw_code not in (None, "") else None
            except (TypeError, ValueError):
                actual_status = None

            system_name = ""
            task_name = schedule.name
            if schedule.monitoring_request_id:
                request_meta = getattr(schedule.monitoring_request, "metadata", None) or {}
                system_name = str(request_meta.get("system_name") or "").strip()
                if not system_name:
                    system_name = str(getattr(schedule.monitoring_request, "title", "") or "").strip()

            message = str(getattr(schedule, "last_message", "") or "").strip() or None
            if latest:
                message = str(latest.message or "").strip() or None
                last_status = str(latest.status or "").strip()
                last_scheduled_at = latest.scheduled_at
                last_probe_name = latest.probe.name if latest.probe_id else None
                response_ms = latest.response_time_ms
            else:
                last_status = ""
                last_scheduled_at = None
                last_probe_name = None
                response_ms = None
            if not message and last_status in {ProbeScheduleExecution.Status.MISSED, ProbeScheduleExecution.Status.FAILED}:
                message = "任务异常" if last_status == ProbeScheduleExecution.Status.FAILED else "任务超时/未上报结果"

            rows.append(
                {
                    "id": str(schedule.id),
                    "domain": schedule.target,
                    "system_name": system_name or None,
                    "task_name": task_name,
                    "expected_status": expected,
                    "actual_status": actual_status,
                    "response_ms": response_ms,
                    "probe": last_probe_name,
                    "checked_at": last_scheduled_at,
                    "status_message": message,
                }
            )

        return Response(rows)
