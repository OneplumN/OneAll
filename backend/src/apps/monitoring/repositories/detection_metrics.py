from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

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


def store_detection_result(
    *,
    detection_id,
    probe_id,
    protocol: str,
    target: str,
    status: str,
    response_time_ms: Optional[int],
    metadata: Dict[str, Any] | None,
    recorded_at: datetime | None = None,
) -> None:
    """Persist detection metrics into TimescaleDB (no-op when disabled)."""

    connection = _get_timescale_connection()
    if connection is None:
        return

    payload = json.dumps(metadata or {})
    recorded_ts = recorded_at or timezone.now()

    sql = """
        INSERT INTO probe_detection_results (
            detection_id,
            probe_id,
            protocol,
            target,
            status,
            response_time_ms,
            metadata,
            recorded_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
        ON CONFLICT (detection_id, recorded_at) DO UPDATE
        SET
            probe_id = EXCLUDED.probe_id,
            protocol = EXCLUDED.protocol,
            target = EXCLUDED.target,
            status = EXCLUDED.status,
            response_time_ms = EXCLUDED.response_time_ms,
            metadata = EXCLUDED.metadata,
            recorded_at = EXCLUDED.recorded_at
    """
    params = (
        str(detection_id),
        str(probe_id) if probe_id else None,
        protocol,
        target,
        status,
        response_time_ms,
        payload,
        recorded_ts,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
    except Exception:
        logger.warning(
            "Failed to store detection metrics",  # pragma: no cover - logging only
            extra={"detection_id": str(detection_id)},
            exc_info=True,
        )
