from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Literal

from django.utils import timezone

try:
    from apps.monitoring.models import DetectionTask
    from apps.probes.models import ProbeNode
except Exception:  # pragma: no cover - optional during bootstrap
    DetectionTask = None  # type: ignore
    ProbeNode = None  # type: ignore


Severity = Literal["critical", "warning", "info"]


@dataclass(slots=True)
class AlertItem:
    id: str
    target: str
    status: str
    severity: Severity
    occurred_at: str
    probe: str | None = None
    message: str | None = None


def _detect_severity(status: str) -> Severity:
    critical_status = {"failed", "error", "critical"}
    warning_status = {"timeout", "degraded", "warning"}

    status_lower = status.lower()
    if status_lower in critical_status:
        return "critical"
    if status_lower in warning_status:
        return "warning"
    return "info"


def get_alert_summary(limit: int = 5) -> dict[str, object]:
    """Aggregate recent detection alerts for dashboard consumption."""

    now = timezone.now()
    window_start = now - timedelta(hours=24)

    if DetectionTask is None:
        return {
            "generated_at": now.isoformat(),
            "total_alerts": 0,
            "breakdown": [],
            "items": [],
        }

    queryset = (
        DetectionTask.objects.filter(executed_at__gte=window_start)
        .exclude(status=DetectionTask.Status.SUCCEEDED)
        .order_by("-executed_at")
    )

    total_alerts = queryset.count()

    critical_count = queryset.filter(status__iexact=DetectionTask.Status.FAILED).count()
    warning_count = queryset.filter(status__iexact=DetectionTask.Status.TIMEOUT).count()
    info_count = max(total_alerts - critical_count - warning_count, 0)

    probe_map: dict[int, str] = {}
    if ProbeNode is not None:
        probe_ids = list(
            queryset.exclude(probe_id=None).values_list("probe_id", flat=True)[: limit * 2]
        )
        if probe_ids:
            probe_map = {
                probe.id: probe.name
                for probe in ProbeNode.objects.filter(id__in=probe_ids).only("id", "name")
            }

    items: list[AlertItem] = []
    for task in queryset.select_related("probe")[:limit]:
        severity = _detect_severity(task.status)
        occurred = task.executed_at or task.created_at
        probe_name = None
        if task.probe_id and task.probe_id in probe_map:
            probe_name = probe_map[task.probe_id]
        elif getattr(task, "probe", None) is not None:
            probe_name = task.probe.name

        items.append(
            AlertItem(
                id=str(task.id),
                target=task.target,
                status=task.status,
                severity=severity,
                occurred_at=occurred.isoformat() if occurred else now.isoformat(),
                probe=probe_name,
                message=task.error_message or None,
            )
        )

    return {
        "generated_at": now.isoformat(),
        "total_alerts": total_alerts,
        "breakdown": [
            {"level": "critical", "count": critical_count},
            {"level": "warning", "count": warning_count},
            {"level": "info", "count": info_count},
        ],
        "items": [asdict(item) for item in items],
    }
