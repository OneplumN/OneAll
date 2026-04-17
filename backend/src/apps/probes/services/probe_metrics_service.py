from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from django.utils import timezone

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
    total_success = sum(bucket.success for bucket in buckets)
    total_failed = sum(bucket.failed for bucket in buckets)
    total = total_success + total_failed
    avg_latency = None
    latencies = [bucket.avg_latency_ms for bucket in buckets if bucket.avg_latency_ms is not None]
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
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


def get_latest_uptime(*, probe_id: str) -> Optional[int]:
    """Return latest uptime_seconds value for the probe, if recorded."""

    return fetch_latest_uptime(probe_id=probe_id)
