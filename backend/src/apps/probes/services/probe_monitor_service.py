from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from apps.probes.models import ProbeNode

logger = logging.getLogger(__name__)


def handle_heartbeat(*, probe: ProbeNode, payload: dict[str, object]) -> None:
    """Update probe metadata based on heartbeat payload."""

    status = payload.get("status", probe.status)
    supported_protocols = payload.get("supported_protocols", probe.supported_protocols)
    metrics = _normalize_metrics(payload.get("metrics"))

    updates: Dict[str, Any] = {
        "status": status,
        "supported_protocols": supported_protocols,
        "last_heartbeat_at": datetime.now(timezone.utc),
    }
    if metrics is not None:
        updates["runtime_metrics"] = metrics

    ProbeNode.objects.filter(id=probe.id).update(**updates)

    logger.info("Probe %s heartbeat processed", probe.id)


def _normalize_metrics(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None

    normalized: dict[str, Any] = {}

    cpu = _coerce_float(raw.get("cpu_usage"))
    if cpu is not None:
        normalized["cpu_usage"] = max(0.0, min(cpu, 100.0))

    memory = _coerce_float(raw.get("memory_usage_mb"))
    if memory is not None:
        normalized["memory_usage_mb"] = max(memory, 0.0)

    load_avg = _coerce_float(raw.get("load_avg"))
    if load_avg is not None:
        normalized["load_avg"] = max(load_avg, 0.0)

    queue_depth = _coerce_int(raw.get("task_queue_depth"))
    if queue_depth is not None:
        normalized["task_queue_depth"] = max(queue_depth, 0)

    active_tasks = _coerce_int(raw.get("active_tasks"))
    if active_tasks is not None:
        normalized["active_tasks"] = max(active_tasks, 0)

    latency = _coerce_int(raw.get("queue_latency_ms"))
    if latency is not None:
        normalized["queue_latency_ms"] = max(latency, 0)

    if not normalized:
        return None

    normalized["reported_at"] = datetime.now(timezone.utc).isoformat()
    return normalized


def _coerce_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
