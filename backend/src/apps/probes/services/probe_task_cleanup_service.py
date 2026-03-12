from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode

from . import probe_task_service


def mark_stale_running_tasks(*, probe: ProbeNode | None = None, now=None, grace_seconds: int = 0) -> int:
    current = now or timezone.now()
    grace = max(int(grace_seconds), 0)

    queryset = DetectionTask.objects.filter(status=DetectionTask.Status.RUNNING)
    if probe is not None:
        queryset = queryset.filter(probe=probe)

    stale_ids: list[str] = []
    for task in queryset.only("id", "updated_at", "metadata"):
        timeout_seconds = probe_task_service.timeout_from_metadata(task.metadata)
        deadline = task.updated_at + timedelta(seconds=timeout_seconds + grace)
        if deadline <= current:
            stale_ids.append(str(task.id))

    if not stale_ids:
        return 0

    cleaned = DetectionTask.objects.filter(id__in=stale_ids, status=DetectionTask.Status.RUNNING).update(
        status=DetectionTask.Status.TIMEOUT,
        error_message="探针未在超时时间内回传结果",
        updated_at=current,
    )
    return cleaned

