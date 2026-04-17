from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeScheduleExecution
from apps.probes.models import ProbeNode
from apps.probes.repositories.metrics_queries import (
    fetch_result_buckets,
    fetch_runtime_timeseries,
    fetch_latest_uptime,
)
from apps.probes.repositories.runtime_metrics import insert_runtime_snapshot


def record_runtime_snapshot(*, probe: ProbeNode, payload: dict[str, Any]) -> None:
    """Persist a structured runtime snapshot coming from a probe agent."""

    metrics_generated_at: datetime = payload.get("captured_at") or timezone.now()
    heartbeats = payload.get("heartbeats") or {}
    tasks = payload.get("tasks") or {}
    queue = payload.get("queue") or {}
    workers = payload.get("workers") or {}

    runtime = probe.runtime_metrics or {}
    cpu_usage = runtime.get("cpu_usage")
    memory_usage_mb = runtime.get("memory_usage_mb")

    insert_runtime_snapshot(
        probe_id=probe.id,
        node_name=probe.name,
        uptime_seconds=payload.get("uptime_seconds", 0),
        cpu_usage=cpu_usage,
        memory_usage_mb=memory_usage_mb,
        heartbeats_sent=heartbeats.get("sent", 0),
        heartbeats_failed=heartbeats.get("failed", 0),
        heartbeats_last_success=heartbeats.get("last_success"),
        tasks_fetched=tasks.get("fetched", 0),
        tasks_executed=tasks.get("executed", 0),
        tasks_failed=tasks.get("failed", 0),
        queue_depth=queue.get("depth", 0),
        queue_capacity=queue.get("capacity", 0),
        active_workers=workers.get("active", 0),
        metrics_generated_at=metrics_generated_at,
    )


def get_runtime_history(*, probe_id: str, hours: int, interval_minutes: int) -> dict[str, Any]:
    since = timezone.now() - timedelta(hours=hours)
    interval = f"{interval_minutes} minutes"
    points = fetch_runtime_timeseries(probe_id=probe_id, since=since, interval=interval)
    return {
        "from": since,
        "to": timezone.now(),
        "points": [
            {
                "timestamp": point.timestamp,
                "cpu_usage": point.cpu_usage,
                "memory_usage_mb": point.memory_usage_mb,
                "queue_depth": point.queue_depth,
                "active_workers": point.active_workers,
                "tasks_executed": point.tasks_executed,
                "heartbeats_sent": point.heartbeats_sent,
            }
            for point in points
        ],
    }


def get_result_statistics(*, probe_id: str, hours: int, interval_minutes: int) -> dict[str, Any]:
    since = timezone.now() - timedelta(hours=hours)
    interval = f"{interval_minutes} minutes"
    buckets = fetch_result_buckets(probe_id=probe_id, since=since, interval=interval)
    detection_stats = _summarize_detection_buckets(buckets)
    schedule_stats = _summarize_schedule_executions(probe_id=probe_id, since=since)

    # When Timescale is disabled or there are no detection buckets in the current
    # window, fall back to relational one-off detections so health totals still
    # reflect real executions in development / sqlite mode.
    if not buckets:
        detection_stats = _summarize_detection_tasks(probe_id=probe_id, since=since)

    total_success = detection_stats["success"] + schedule_stats["success"]
    total_failed = detection_stats["failed"] + schedule_stats["failed"]
    total = total_success + total_failed
    avg_latency = _merge_latency(
        left_avg=detection_stats["avg_latency_ms"],
        left_count=detection_stats["latency_count"],
        right_avg=schedule_stats["avg_latency_ms"],
        right_count=schedule_stats["latency_count"],
    )
    success_rate = (total_success / total) if total else 0
    return {
        "from": since,
        "to": timezone.now(),
        "points": [
            {
                "timestamp": bucket.timestamp,
                "success": bucket.success,
                "failed": bucket.failed,
                "avg_latency_ms": bucket.avg_latency_ms,
            }
            for bucket in buckets
        ],
        "total": {
            "success": total_success,
            "failed": total_failed,
            "success_rate": success_rate,
            "avg_latency_ms": avg_latency,
        },
    }


def _summarize_detection_buckets(buckets: list) -> dict[str, float | int | None]:
    total_success = sum(bucket.success for bucket in buckets)
    total_failed = sum(bucket.failed for bucket in buckets)
    latency_sum = sum(bucket.avg_latency_ms for bucket in buckets if bucket.avg_latency_ms is not None)
    latency_count = sum(1 for bucket in buckets if bucket.avg_latency_ms is not None)
    avg_latency = (latency_sum / latency_count) if latency_count else None
    return {
        "success": total_success,
        "failed": total_failed,
        "avg_latency_ms": avg_latency,
        "latency_count": latency_count,
    }


def _summarize_detection_tasks(*, probe_id: str, since: datetime) -> dict[str, float | int | None]:
    agg = DetectionTask.objects.filter(
        probe_id=probe_id,
        executed_at__isnull=False,
        executed_at__gte=since,
    ).aggregate(
        success=Count("id", filter=Q(status=DetectionTask.Status.SUCCEEDED)),
        failed=Count("id", filter=Q(status__in=[DetectionTask.Status.FAILED, DetectionTask.Status.TIMEOUT])),
        avg_latency_ms=Avg("response_time_ms"),
        latency_count=Count("response_time_ms"),
    )
    return {
        "success": int(agg["success"] or 0),
        "failed": int(agg["failed"] or 0),
        "avg_latency_ms": float(agg["avg_latency_ms"]) if agg["avg_latency_ms"] is not None else None,
        "latency_count": int(agg["latency_count"] or 0),
    }


def _summarize_schedule_executions(*, probe_id: str, since: datetime) -> dict[str, float | int | None]:
    agg = ProbeScheduleExecution.objects.filter(
        probe_id=probe_id,
        scheduled_at__gte=since,
    ).aggregate(
        success=Count("id", filter=Q(status=ProbeScheduleExecution.Status.SUCCEEDED)),
        failed=Count("id", filter=Q(status__in=[ProbeScheduleExecution.Status.FAILED, ProbeScheduleExecution.Status.MISSED])),
        avg_latency_ms=Avg("response_time_ms"),
        latency_count=Count("response_time_ms"),
    )
    return {
        "success": int(agg["success"] or 0),
        "failed": int(agg["failed"] or 0),
        "avg_latency_ms": float(agg["avg_latency_ms"]) if agg["avg_latency_ms"] is not None else None,
        "latency_count": int(agg["latency_count"] or 0),
    }


def _merge_latency(
    *,
    left_avg: float | int | None,
    left_count: int,
    right_avg: float | int | None,
    right_count: int,
) -> float | None:
    total_count = int(left_count or 0) + int(right_count or 0)
    if total_count <= 0:
        return None
    left_sum = (float(left_avg) * left_count) if left_avg is not None else 0.0
    right_sum = (float(right_avg) * right_count) if right_avg is not None else 0.0
    return (left_sum + right_sum) / total_count


def get_latest_uptime(*, probe_id: str) -> Optional[int]:
    """Return latest uptime_seconds value for the probe, if recorded."""

    return fetch_latest_uptime(probe_id=probe_id)
