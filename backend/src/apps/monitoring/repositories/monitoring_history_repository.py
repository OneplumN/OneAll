from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.db.models import Avg, Count, Q, QuerySet

from apps.monitoring.models import DetectionTask


@dataclass(frozen=True)
class MonitoringHistoryFilters:
    target: Optional[str] = None
    status: Optional[str] = None
    protocol: Optional[str] = None
    probe_id: Optional[str] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None


def _apply_time_filters(queryset: QuerySet, filters: MonitoringHistoryFilters) -> QuerySet:
    if filters.started_after:
        queryset = queryset.filter(
            Q(executed_at__isnull=False, executed_at__gte=filters.started_after)
            | Q(executed_at__isnull=True, created_at__gte=filters.started_after)
        )
    if filters.started_before:
        queryset = queryset.filter(
            Q(executed_at__isnull=False, executed_at__lte=filters.started_before)
            | Q(executed_at__isnull=True, created_at__lte=filters.started_before)
        )
    return queryset


def _apply_filters(filters: MonitoringHistoryFilters) -> QuerySet:
    queryset = DetectionTask.objects.select_related("probe").all()

    if filters.target:
        queryset = queryset.filter(target__icontains=filters.target.strip())
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    if filters.protocol:
        queryset = queryset.filter(protocol=filters.protocol)
    if filters.probe_id:
        queryset = queryset.filter(probe_id=filters.probe_id)

    queryset = _apply_time_filters(queryset, filters)
    return queryset


def _calculate_status_counts(queryset: QuerySet) -> dict[str, int]:
    raw_counts = queryset.values("status").annotate(total=Count("id"))
    counts: dict[str, int] = {
        DetectionTask.Status.SCHEDULED: 0,
        DetectionTask.Status.RUNNING: 0,
        DetectionTask.Status.SUCCEEDED: 0,
        DetectionTask.Status.FAILED: 0,
        DetectionTask.Status.TIMEOUT: 0,
    }
    for item in raw_counts:
        counts[item["status"]] = item["total"]
    return counts


def _calculate_average_response_time(queryset: QuerySet) -> Optional[float]:
    value = queryset.aggregate(avg=Avg("response_time_ms"))["avg"]
    return float(value) if value is not None else None


class MonitoringHistoryRepository:
    @classmethod
    def fetch_history(
        cls,
        filters: MonitoringHistoryFilters,
        page: int,
        page_size: int,
    ) -> tuple[list[DetectionTask], int, dict[str, int], Optional[float]]:
        queryset = _apply_filters(filters).order_by("-executed_at", "-created_at")

        total = queryset.count()
        offset = (page - 1) * page_size
        items = list(queryset[offset : offset + page_size])

        status_counts = _calculate_status_counts(queryset)
        avg_response_time = _calculate_average_response_time(queryset)

        return items, total, status_counts, avg_response_time
