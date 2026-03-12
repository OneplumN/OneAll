from __future__ import annotations

from celery import shared_task

from apps.dashboard.services.overview_service import get_overview_metrics


@shared_task(name="apps.dashboard.tasks.overview_refresh.refresh_metrics")
def refresh_metrics() -> dict[str, object]:
    """Warm the dashboard overview cache."""

    return get_overview_metrics(force_refresh=True)
