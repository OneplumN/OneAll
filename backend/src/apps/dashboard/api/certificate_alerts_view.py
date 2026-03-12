from __future__ import annotations

from typing import Any, Dict, List

from django.utils import timezone
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.probes.models import ProbeSchedule, ProbeScheduleExecution
from apps.settings.models import SystemSettings


def _parse_int(value: Any, default: int, *, min_value: int, max_value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_value, min(max_value, parsed))


def _parse_days(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class DashboardCertificateAlertsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        limit = _parse_int(request.query_params.get("limit"), 12, min_value=1, max_value=100)
        settings = SystemSettings.objects.order_by("-updated_at").first()
        threshold_critical = getattr(settings, "certificate_expiry_threshold_critical_days", 15) if settings else 15
        threshold_warning = getattr(settings, "certificate_expiry_threshold_warning_days", 30) if settings else 30
        threshold_notice = getattr(settings, "certificate_expiry_threshold_notice_days", 45) if settings else 45

        schedules = list(
            ProbeSchedule.objects.filter(status=ProbeSchedule.Status.ACTIVE, protocol="CERTIFICATE")
            .order_by("-updated_at")
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

        total_schedules = len(schedule_ids)
        with_result = 0
        missing_certificate_payload = 0

        items: List[Dict[str, Any]] = []
        for schedule in schedules:
            latest = latest_by_schedule.get(str(schedule.id))
            if latest:
                with_result += 1
            meta = (latest.metadata if latest else None) or {}
            cert = meta.get("certificate") if isinstance(meta, dict) else None
            cert = cert if isinstance(cert, dict) else {}

            days_remaining = _parse_days(cert.get("days_until_expiry"))
            issuer = cert.get("issuer")
            if not cert:
                missing_certificate_payload += 1

            # 没有拿到有效的 days，仍然可展示为异常项（便于排障）
            severity: str | None = None
            if days_remaining is None:
                severity = "warning"
            elif days_remaining < 0:
                severity = "critical"
            elif days_remaining <= threshold_critical:
                severity = "critical"
            elif days_remaining <= threshold_warning:
                severity = "warning"
            elif days_remaining <= threshold_notice:
                severity = "info"
            else:
                continue

            message = str((latest.message if latest else "") or "").strip() or None
            if not message and days_remaining is None:
                message = "证书信息缺失"

            items.append(
                {
                    "id": str(schedule.id),
                    "domain": schedule.target,
                    "issuer": issuer,
                    "days_remaining": days_remaining,
                    "severity": severity,
                    "probe": latest.probe.name if latest and latest.probe_id else None,
                    "checked_at": latest.scheduled_at if latest else None,
                    "message": message,
                }
            )

        # 更关心“更近/已过期”的证书
        items.sort(key=lambda item: (item.get("days_remaining") is None, item.get("days_remaining", 10**9)))
        items = items[:limit]

        return Response(
            {
                "generated_at": timezone.now().isoformat(),
                "thresholds": {
                    "critical": threshold_critical,
                    "warning": threshold_warning,
                    "notice": threshold_notice,
                },
                "stats": {
                    "schedules_total": total_schedules,
                    "schedules_with_result": with_result,
                    "missing_certificate_payload": missing_certificate_payload,
                },
                "items": items,
            }
        )
