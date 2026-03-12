from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from django.utils import timezone

try:
    from apps.monitoring.models import MonitoringRequest
    from apps.probes.models import ProbeNode
    from apps.settings.models import PluginConfig
except Exception:  # pragma: no cover - optional during bootstrap
    MonitoringRequest = None  # type: ignore
    ProbeNode = None  # type: ignore
    PluginConfig = None  # type: ignore


TodoType = Literal["monitoring_request", "probe_health", "plugin"]


@dataclass(slots=True)
class TodoEntry:
    id: str
    label: str
    created_at: str
    link: str | None = None
    metadata: dict[str, str] | None = None


@dataclass(slots=True)
class TodoBucket:
    id: str
    title: str
    description: str
    type: TodoType
    total: int
    items: list[TodoEntry]


def _collect_pending_requests(limit: int) -> TodoBucket | None:
    if MonitoringRequest is None:
        return None

    queryset = MonitoringRequest.objects.filter(status=MonitoringRequest.Status.PENDING).order_by("-created_at")
    total = queryset.count()
    if total == 0:
        return TodoBucket(
            id="pending-monitoring-requests",
            title="待审批拨测申请",
            description="待 ITSM 审批或人工处理的监控申请",
            type="monitoring_request",
            total=0,
            items=[],
        )

    items = [
        TodoEntry(
            id=str(req.id),
            label=req.title,
            created_at=req.created_at.isoformat(),
            metadata={"target": req.target, "protocol": req.protocol},
        )
        for req in queryset[:limit]
    ]
    return TodoBucket(
        id="pending-monitoring-requests",
        title="待审批拨测申请",
        description="待 ITSM 审批或人工处理的监控申请",
        type="monitoring_request",
        total=total,
        items=items,
    )


def _collect_offline_probes(limit: int) -> TodoBucket | None:
    if ProbeNode is None:
        return None

    queryset = ProbeNode.objects.filter(status="offline").order_by("-updated_at")
    total = queryset.count()
    if total == 0:
        return TodoBucket(
            id="offline-probes",
            title="离线探针节点",
            description="需排查心跳异常的探针节点",
            type="probe_health",
            total=0,
            items=[],
        )

    items = [
        TodoEntry(
            id=str(probe.id),
            label=probe.name,
            created_at=(probe.updated_at or probe.created_at).isoformat(),
            metadata={"location": probe.location, "network_type": probe.network_type},
        )
        for probe in queryset.select_related("proxy")[:limit]
    ]

    return TodoBucket(
        id="offline-probes",
        title="离线探针节点",
        description="需排查心跳异常的探针节点",
        type="probe_health",
        total=total,
        items=items,
    )


def _collect_plugin_issues(limit: int) -> TodoBucket | None:
    if PluginConfig is None:
        return None

    queryset = (
        PluginConfig.objects.filter(enabled=True)
        .exclude(status__in=["healthy", "ok"])
        .order_by("-last_checked_at")
    )
    total = queryset.count()
    if total == 0:
        return TodoBucket(
            id="plugin-issues",
            title="插件健康异常",
            description="需排查的监控插件或外部集成",
            type="plugin",
            total=0,
            items=[],
        )

    items = [
        TodoEntry(
            id=str(plugin.id),
            label=plugin.name,
            created_at=(plugin.last_checked_at or plugin.updated_at or plugin.created_at).isoformat(),
            metadata={"status": plugin.status, "type": plugin.type},
        )
        for plugin in queryset[:limit]
    ]

    return TodoBucket(
        id="plugin-issues",
        title="插件健康异常",
        description="需排查的监控插件或外部集成",
        type="plugin",
        total=total,
        items=items,
    )


def get_todo_items(limit: int = 5) -> dict[str, object]:
    now = timezone.now()
    buckets = []

    for collector in (_collect_pending_requests, _collect_offline_probes, _collect_plugin_issues):
        bucket = collector(limit)
        if bucket is not None:
            buckets.append(bucket)

    return {
        "generated_at": now.isoformat(),
        "items": [asdict(bucket) for bucket in buckets],
    }
