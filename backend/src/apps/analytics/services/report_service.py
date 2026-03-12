from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from django.db.models import QuerySet
from django.db.models.functions import TruncDate
from django.utils import timezone as dj_timezone

from apps.monitoring.models import DetectionTask


FINAL_STATUSES = {
    DetectionTask.Status.SUCCEEDED,
    DetectionTask.Status.FAILED,
    DetectionTask.Status.TIMEOUT,
}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _percentile(values: list[int], p: float) -> Optional[int]:
    if not values:
        return None
    if p <= 0:
        return min(values)
    if p >= 1:
        return max(values)
    values = sorted(values)
    k = int(round((len(values) - 1) * p))
    k = max(0, min(k, len(values) - 1))
    return int(values[k])


def _classify_failure(task: DetectionTask) -> str:
    if task.status == DetectionTask.Status.TIMEOUT:
        return "超时"
    status_code = _safe_str(task.status_code)
    if status_code and status_code not in {"200", "201", "204"}:
        return "HTTP 状态码"
    message = _safe_str(task.error_message).lower()
    if not message:
        return "其他"
    if any(key in message for key in ["dns", "name resolution", "nxdomain"]):
        return "DNS"
    if any(key in message for key in ["tls", "ssl", "handshake", "certificate"]):
        return "TLS/证书"
    if any(key in message for key in ["connect", "connection", "refused", "reset", "unreachable"]):
        return "连接"
    if "timeout" in message:
        return "超时"
    return "其他"


@dataclass(frozen=True)
class _TrendPoint:
    day: str
    total: int
    success_rate: float
    p95_ms: Optional[int]


def _base_queryset(start: datetime) -> QuerySet[DetectionTask]:
    return (
        DetectionTask.objects.select_related("probe")
        .filter(created_at__gte=start, status__in=FINAL_STATUSES)
        .order_by("-created_at")
    )


def fetch_detection_metrics(days: int) -> Dict[str, Any]:
    now = dj_timezone.now()
    start = now - timedelta(days=max(days, 1))

    queryset = _base_queryset(start)
    total = queryset.count()
    succeeded_qs = queryset.filter(status=DetectionTask.Status.SUCCEEDED)
    failed_qs = queryset.filter(status=DetectionTask.Status.FAILED)
    timeout_qs = queryset.filter(status=DetectionTask.Status.TIMEOUT)

    succeeded = succeeded_qs.count()
    failed = failed_qs.count()
    timeout = timeout_qs.count()
    success_rate = (succeeded / total) if total else 0.0

    latency_values: list[int] = list(
        succeeded_qs.exclude(response_time_ms__isnull=True).values_list("response_time_ms", flat=True)
    )
    p50_ms = _percentile(latency_values, 0.5)
    p95_ms = _percentile(latency_values, 0.95)

    # 趋势：按天（created_at）聚合
    trend_rows = list(
        queryset.annotate(day=TruncDate("created_at"))
        .values("day")
        .order_by("day")
    )
    # 为了算 p95，需要按天拉取成功延迟并在 Python 侧算
    latency_by_day: dict[str, list[int]] = defaultdict(list)
    for row in succeeded_qs.exclude(response_time_ms__isnull=True).annotate(day=TruncDate("created_at")).values(
        "day", "response_time_ms"
    ):
        day = row.get("day")
        if not day:
            continue
        latency_by_day[str(day)].append(int(row.get("response_time_ms") or 0))

    totals_by_day: dict[str, int] = Counter()
    succeeded_by_day: dict[str, int] = Counter()
    for row in queryset.annotate(day=TruncDate("created_at")).values("day", "status"):
        day = row.get("day")
        if not day:
            continue
        key = str(day)
        totals_by_day[key] += 1
        if row.get("status") == DetectionTask.Status.SUCCEEDED:
            succeeded_by_day[key] += 1

    trend: list[Dict[str, Any]] = []
    for item in trend_rows:
        day = item.get("day")
        if not day:
            continue
        key = str(day)
        day_total = int(totals_by_day.get(key) or 0)
        day_succeeded = int(succeeded_by_day.get(key) or 0)
        day_rate = (day_succeeded / day_total) if day_total else 0.0
        day_p95 = _percentile(latency_by_day.get(key, []), 0.95)
        trend.append(
            {
                "day": key,
                "total": day_total,
                "success_rate": round(day_rate, 4),
                "p95_ms": day_p95,
            }
        )

    # 失败类型分布
    failure_types: Counter = Counter()
    for task in queryset.exclude(status=DetectionTask.Status.SUCCEEDED):
        failure_types[_classify_failure(task)] += 1

    # Top 目标（按失败次数）
    target_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "succeeded": 0, "failed": 0, "timeout": 0, "latencies": []})
    for task in queryset:
        target = _safe_str(task.target) or "-"
        stat = target_stats[target]
        stat["total"] += 1
        if task.status == DetectionTask.Status.SUCCEEDED:
            stat["succeeded"] += 1
            if task.response_time_ms is not None:
                stat["latencies"].append(int(task.response_time_ms))
        elif task.status == DetectionTask.Status.TIMEOUT:
            stat["timeout"] += 1
        else:
            stat["failed"] += 1

    top_targets: list[Dict[str, Any]] = []
    for target, stat in target_stats.items():
        total_n = int(stat["total"])
        failed_n = int(stat["failed"])
        timeout_n = int(stat["timeout"])
        succeeded_n = int(stat["succeeded"])
        fail_total = failed_n + timeout_n
        top_targets.append(
            {
                "target": target,
                "total": total_n,
                "succeeded": succeeded_n,
                "failed": failed_n,
                "timeout": timeout_n,
                "fail_rate": round((fail_total / total_n) if total_n else 0.0, 4),
                "p95_ms": _percentile(stat["latencies"], 0.95),
            }
        )
    top_targets.sort(key=lambda item: (item["failed"] + item["timeout"], item["total"]), reverse=True)
    top_targets = top_targets[:20]

    # Top 探针（按失败次数）
    probe_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"name": "", "total": 0, "succeeded": 0, "failed": 0, "timeout": 0, "latencies": []})
    for task in queryset:
        probe_id = str(task.probe_id) if task.probe_id else "unknown"
        stat = probe_stats[probe_id]
        stat["name"] = getattr(task.probe, "name", "") or "未知探针"
        stat["total"] += 1
        if task.status == DetectionTask.Status.SUCCEEDED:
            stat["succeeded"] += 1
            if task.response_time_ms is not None:
                stat["latencies"].append(int(task.response_time_ms))
        elif task.status == DetectionTask.Status.TIMEOUT:
            stat["timeout"] += 1
        else:
            stat["failed"] += 1

    top_probes: list[Dict[str, Any]] = []
    for probe_id, stat in probe_stats.items():
        total_n = int(stat["total"])
        succeeded_n = int(stat["succeeded"])
        failed_n = int(stat["failed"])
        timeout_n = int(stat["timeout"])
        top_probes.append(
            {
                "probe_id": probe_id,
                "probe_name": stat["name"],
                "total": total_n,
                "succeeded": succeeded_n,
                "failed": failed_n,
                "timeout": timeout_n,
                "success_rate": round((succeeded_n / total_n) if total_n else 0.0, 4),
                "p95_ms": _percentile(stat["latencies"], 0.95),
            }
        )
    top_probes.sort(key=lambda item: (item["failed"] + item["timeout"], item["total"]), reverse=True)
    top_probes = top_probes[:20]

    recent_failures: list[Dict[str, Any]] = []
    for task in queryset.exclude(status=DetectionTask.Status.SUCCEEDED)[:50]:
        recent_failures.append(
            {
                "id": str(task.id),
                "target": task.target,
                "protocol": task.protocol,
                "status": task.status,
                "response_time_ms": task.response_time_ms,
                "status_code": task.status_code,
                "error_message": task.error_message,
                "probe": {
                    "id": str(task.probe_id) if task.probe_id else None,
                    "name": getattr(task.probe, "name", None) if task.probe else None,
                },
                "created_at": task.created_at.isoformat(),
            }
        )

    return {
        "range": {"start": start.isoformat(), "end": now.isoformat(), "days": days},
        "summary": {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "timeout": timeout,
            "success_rate": round(success_rate, 4),
            "p50_ms": p50_ms,
            "p95_ms": p95_ms,
        },
        "trend": trend,
        "failure_types": [{"type": k, "count": int(v)} for k, v in failure_types.most_common()],
        "top_targets": top_targets,
        "top_probes": top_probes,
        "recent_failures": recent_failures,
    }


def build_detection_report(days: int = 30) -> Dict[str, Any]:
    metrics = fetch_detection_metrics(days)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **metrics,
    }
