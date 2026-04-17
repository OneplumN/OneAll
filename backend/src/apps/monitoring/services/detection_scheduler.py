from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode


class ProbeUnavailableError(RuntimeError):
    def __init__(self, message: str, *, suggestions: list[dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.suggestions = suggestions or []


class ProbeCapacityError(RuntimeError):
    def __init__(self, message: str, *, suggestions: list[dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.suggestions = suggestions or []


@dataclass
class DetectionScheduler:
    max_active_tasks: int = getattr(settings, "DETECTION_MAX_ACTIVE_TASKS", 5)

    def _probe_capacity_limit(self, probe: ProbeNode | None) -> int:
        if not probe:
            return self.max_active_tasks
        config = probe.agent_config or {}
        if isinstance(config, dict):
            explicit = config.get("max_concurrent_tasks") or config.get("max_running_tasks")
            if isinstance(explicit, (int, float)) and explicit > 0:
                return int(explicit)
        return self.max_active_tasks

    def _suggest_alternatives(self, probe: ProbeNode | None) -> list[dict[str, str]]:
        queryset = ProbeNode.objects.filter(status="online")
        if probe is not None:
            queryset = queryset.exclude(id=probe.id)
        suggestions = [
            {"id": str(node.id), "name": node.name, "location": node.location}
            for node in queryset.order_by("name")[:5]
        ]
        return suggestions

    def guard_probe(self, probe: ProbeNode | None, protocol: str | None = None) -> None:
        if probe is None:
            return

        if probe.status != "online":
            raise ProbeUnavailableError(
                f"探针 {probe.name} 当前不可用（状态：{probe.get_status_display()}）",
                suggestions=self._suggest_alternatives(probe),
            )

        supported = probe.supported_protocols or []
        if protocol and supported:
            normalized = {str(item).upper() for item in supported if item}
            if protocol.upper() not in normalized:
                raise ProbeUnavailableError(
                    f"探针 {probe.name} 不支持协议 {protocol}",
                    suggestions=self._suggest_alternatives(probe),
                )

        active = DetectionTask.objects.filter(
            probe=probe,
            status__in=[DetectionTask.Status.SCHEDULED, DetectionTask.Status.RUNNING],
        ).count()
        limit = max(self._probe_capacity_limit(probe), 1)
        if active >= limit:
            raise ProbeCapacityError(
                f"探针 {probe.name} 当前排队任务过多（{active} 个），请稍后重试或选择其他探针",
                suggestions=self._suggest_alternatives(probe),
            )
