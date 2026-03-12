from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from apps.monitoring.models import DetectionTask
from apps.monitoring.repositories.monitoring_history_repository import (
    MonitoringHistoryFilters,
    MonitoringHistoryRepository,
)


@dataclass(frozen=True)
class Pagination:
    page: int
    page_size: int
    total_items: int

    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 0
        return math.ceil(self.total_items / self.page_size)


@dataclass(frozen=True)
class Aggregates:
    total_count: int
    status_counts: dict[str, int]
    average_response_time_ms: Optional[float]
    success_rate: Optional[float]


@dataclass(frozen=True)
class MonitoringHistoryResult:
    items: list[DetectionTask]
    aggregates: Aggregates
    pagination: Pagination


def normalize_page(page: int) -> int:
    return page if page > 0 else 1


def normalize_page_size(page_size: int) -> int:
    if page_size < 1:
        return 20
    if page_size > 100:
        return 100
    return page_size


def calculate_success_rate(status_counts: dict[str, int]) -> Optional[float]:
    total = sum(status_counts.values())
    if not total:
        return None
    succeeded = status_counts.get(DetectionTask.Status.SUCCEEDED, 0)
    return round((succeeded / total) * 100, 2)


def query_history(filters: MonitoringHistoryFilters, page: int = 1, page_size: int = 20) -> MonitoringHistoryResult:
    normalized_page = normalize_page(page)
    normalized_page_size = normalize_page_size(page_size)

    items, total, status_counts, avg_response_time = MonitoringHistoryRepository.fetch_history(
        filters, normalized_page, normalized_page_size
    )

    aggregates = Aggregates(
        total_count=total,
        status_counts=status_counts,
        average_response_time_ms=avg_response_time,
        success_rate=calculate_success_rate(status_counts),
    )
    pagination = Pagination(page=normalized_page, page_size=normalized_page_size, total_items=total)

    return MonitoringHistoryResult(items=items, aggregates=aggregates, pagination=pagination)
