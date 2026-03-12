from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from django.db import connections
from django.db.utils import ConnectionDoesNotExist


def _get_connection():
    if "timescale" not in connections.databases:
        return None
    try:
        return connections["timescale"]
    except ConnectionDoesNotExist:
        return None


@dataclass
class RuntimePoint:
    timestamp: datetime
    queue_depth: float
    active_workers: float
    tasks_executed: float
    heartbeats_sent: float


@dataclass
class ResultPoint:
    timestamp: datetime
    success: int
    failed: int
    avg_latency_ms: float | None


def fetch_runtime_timeseries(
    *,
    probe_id: str,
    since: datetime,
    interval: str,
) -> List[RuntimePoint]:
    """Return time bucketed runtime metrics for a probe."""

    conn = _get_connection()
    if conn is None:
        return []

    sql = """
        SELECT
            time_bucket(%s::interval, recorded_at) AS bucket,
            AVG(queue_depth) AS queue_depth,
            AVG(active_workers) AS active_workers,
            AVG(tasks_executed) AS tasks_executed,
            AVG(heartbeats_sent) AS heartbeats_sent
        FROM probe_runtime_metrics
        WHERE probe_id = %s AND recorded_at >= %s
        GROUP BY bucket
        ORDER BY bucket ASC
    """
    params: Iterable = (interval, str(probe_id), since)
    points: list[RuntimePoint] = []

    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        for bucket, queue_depth, active_workers, tasks_executed, heartbeats_sent in rows:
            if bucket is None:
                continue
            points.append(
                RuntimePoint(
                    timestamp=bucket,
                    queue_depth=float(queue_depth or 0),
                    active_workers=float(active_workers or 0),
                    tasks_executed=float(tasks_executed or 0),
                    heartbeats_sent=float(heartbeats_sent or 0),
                )
            )
    return points


def fetch_result_buckets(
    *,
    probe_id: str,
    since: datetime,
    interval: str,
) -> List[ResultPoint]:
    """Return detection outcome buckets for probe."""

    conn = _get_connection()
    if conn is None:
        return []

    sql = """
        SELECT
            time_bucket(%s::interval, recorded_at) AS bucket,
            COUNT(*) FILTER (WHERE status = 'succeeded') AS success,
            COUNT(*) FILTER (WHERE status <> 'succeeded') AS failed,
            AVG(response_time_ms) AS avg_latency
        FROM probe_detection_results
        WHERE probe_id = %s AND recorded_at >= %s
        GROUP BY bucket
        ORDER BY bucket ASC
    """
    params: Iterable = (interval, str(probe_id), since)
    points: list[ResultPoint] = []

    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        for bucket, success, failed, avg_latency in cursor.fetchall():
            if bucket is None:
                continue
            points.append(
                ResultPoint(
                    timestamp=bucket,
                    success=int(success or 0),
                    failed=int(failed or 0),
                    avg_latency_ms=float(avg_latency) if avg_latency is not None else None,
                )
            )
    return points
