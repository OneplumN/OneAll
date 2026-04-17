from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_timescale_connection():
    if "timescale" not in connections.databases:
        return None
    try:
        return connections["timescale"]
    except ConnectionDoesNotExist:
        return None


def insert_runtime_snapshot(
    *,
    probe_id,
    node_name: str,
    uptime_seconds: int,
    cpu_usage: float | None,
    memory_usage_mb: float | None,
    heartbeats_sent: int,
    heartbeats_failed: int,
    heartbeats_last_success: Optional[datetime],
    tasks_fetched: int,
    tasks_executed: int,
    tasks_failed: int,
    queue_depth: int,
    queue_capacity: int,
    active_workers: int,
    metrics_generated_at: datetime,
) -> None:
    """Write a probe runtime snapshot into TimescaleDB."""

    connection = _get_timescale_connection()
    if connection is None:
        return

    recorded_at = timezone.now()
    sql = """
        INSERT INTO probe_runtime_metrics (
            probe_id,
            node_name,
            uptime_seconds,
            cpu_usage,
            memory_usage_mb,
            heartbeats_sent,
            heartbeats_failed,
            heartbeats_last_success,
            tasks_fetched,
            tasks_executed,
            tasks_failed,
            queue_depth,
            queue_capacity,
            active_workers,
            metrics_generated_at,
            recorded_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        str(probe_id),
        node_name,
        uptime_seconds,
        cpu_usage,
        memory_usage_mb,
        heartbeats_sent,
        heartbeats_failed,
        heartbeats_last_success,
        tasks_fetched,
        tasks_executed,
        tasks_failed,
        queue_depth,
        queue_capacity,
        active_workers,
        metrics_generated_at,
        recorded_at,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
    except Exception:
        logger.warning(
            "Failed to store probe runtime metrics",  # pragma: no cover - logging only
            extra={"probe_id": str(probe_id)},
            exc_info=True,
        )
