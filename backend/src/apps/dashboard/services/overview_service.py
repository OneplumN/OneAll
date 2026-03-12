from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict

from django.core.cache import cache
from django.utils import timezone

try:
    from apps.probes.models import ProbeNode
except Exception:  # pragma: no cover - optional dependency during bootstrap
    ProbeNode = None  # type: ignore

try:
    from apps.monitoring.models import DetectionTask, MonitoringRequest
except Exception:  # pragma: no cover - optional dependency during bootstrap
    DetectionTask = None  # type: ignore
    MonitoringRequest = None  # type: ignore

CACHE_KEY = "dashboard:overview:metrics"
CACHE_TTL_SECONDS = 60


@dataclass
class OverviewMetric:
    name: str
    value: int | float
    unit: str | None = None
    trend: float | None = None


def _collect_metrics() -> Dict[str, Any]:
    active_probes = 0
    offline_probes = 0

    if ProbeNode is not None:
        active_probes = ProbeNode.objects.filter(status="online").count()
        offline_probes = ProbeNode.objects.filter(status="offline").count()

    pending_jobs = 0
    last_24h_runs = 0
    open_incidents = 0

    if MonitoringRequest is not None:
        pending_jobs = MonitoringRequest.objects.filter(status=MonitoringRequest.Status.PENDING).count()

    if DetectionTask is not None:
        window_start = timezone.now() - timedelta(hours=24)
        last_24h_runs = DetectionTask.objects.filter(executed_at__gte=window_start).count()
        open_incidents = DetectionTask.objects.filter(
            executed_at__gte=window_start,
            status__in=[DetectionTask.Status.FAILED, DetectionTask.Status.TIMEOUT],
        ).count()

    return {
        "generated_at": timezone.now().isoformat(),
        "probes": {
            "active": active_probes,
            "offline": offline_probes,
        },
        "detection": {
            "pending_jobs": pending_jobs,
            "last_24h_runs": last_24h_runs,
        },
        "incidents": {
            "open": open_incidents,
            "acknowledged": 0,
        },
    }


def get_overview_metrics(force_refresh: bool = False) -> Dict[str, Any]:
    if not force_refresh:
        cached = cache.get(CACHE_KEY)
        if cached:
            return cached

    metrics = _collect_metrics()
    cache.set(CACHE_KEY, metrics, CACHE_TTL_SECONDS)
    return metrics
