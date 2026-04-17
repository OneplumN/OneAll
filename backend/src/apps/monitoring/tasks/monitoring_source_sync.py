from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Tuple

from celery import shared_task

from apps.monitoring.integrations import prometheus_adapter
from apps.monitoring.repositories.monitoring_source_metrics import (
    record_monitoring_source_snapshot,
)

logger = logging.getLogger(__name__)


Fetcher = Callable[[], dict]


def _registered_sources() -> Tuple[Tuple[str, Fetcher], ...]:
    return (
        ("prometheus", lambda: prometheus_adapter.fetch_metrics("up")),
    )


@shared_task(name="apps.monitoring.tasks.sync_monitoring_sources")
def sync_monitoring_sources() -> int:
    """Fetch monitoring source health data and persist snapshots.

    Returns the number of monitoring sources successfully processed.
    """

    processed = 0
    synced_at = datetime.now(timezone.utc)

    for source_type, fetcher in _registered_sources():
        try:
            payload = fetcher()
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Failed to fetch monitoring source", extra={"source_type": source_type})
            continue

        record_monitoring_source_snapshot(
            source_type=source_type,
            payload=payload if isinstance(payload, dict) else {"data": payload},
            synced_at=synced_at,
        )
        processed += 1

    logger.info(
        "monitoring_sources_synced",
        extra={"processed": processed, "synced_at": synced_at.isoformat()},
    )
    return processed
