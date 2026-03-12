from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from django.db import transaction

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode
from apps.monitoring.tasks.execute_detection import execute_detection_task
from apps.monitoring.services.detection_scheduler import DetectionScheduler, ProbeCapacityError, ProbeUnavailableError


class DetectionStatus(str, Enum):
    SCHEDULED = DetectionTask.Status.SCHEDULED
    RUNNING = DetectionTask.Status.RUNNING
    SUCCEEDED = DetectionTask.Status.SUCCEEDED
    FAILED = DetectionTask.Status.FAILED
    TIMEOUT = DetectionTask.Status.TIMEOUT


@dataclass
class DetectionRequest:
    target: str
    protocol: str
    probe_id: Optional[str]
    timeout_seconds: int
    metadata: dict[str, Any]


def _get_probe(probe_id: Optional[str]) -> Optional[ProbeNode]:
    if not probe_id:
        return None
    try:
        return ProbeNode.objects.get(id=probe_id)
    except ProbeNode.DoesNotExist as exc:  # pragma: no cover
        raise ValueError("指定的探针不存在") from exc


def schedule_one_off_detection(request: DetectionRequest) -> DetectionTask:
    if request.protocol not in DetectionTask.Protocol.values:
        raise ValueError("不支持的拨测协议")

    probe = _get_probe(request.probe_id)

    scheduler = DetectionScheduler()
    scheduler.guard_probe(probe)
    requested_by = None
    if request.metadata and request.metadata.get("initiated_by"):
        try:
            requested_by = uuid.UUID(str(request.metadata["initiated_by"]))
        except (ValueError, TypeError):
            requested_by = None

    with transaction.atomic():
        detection = DetectionTask.objects.create(
            target=request.target,
            protocol=request.protocol,
            probe=probe,
            status=DetectionTask.Status.SCHEDULED,
            metadata=request.metadata or {},
            requested_by=requested_by,
        )

    execute_detection_task.delay(str(detection.id))
    return detection


def mark_detection_timeout(detection_id: uuid.UUID) -> None:
    try:
        detection = DetectionTask.objects.get(id=detection_id)
    except DetectionTask.DoesNotExist:  # pragma: no cover
        return

    detection.mark_timeout()


def mark_detection_failed(detection_id: uuid.UUID, message: str) -> None:
    try:
        detection = DetectionTask.objects.get(id=detection_id)
    except DetectionTask.DoesNotExist:  # pragma: no cover
        return

    detection.mark_failed(message)


def mark_detection_succeeded(
    detection_id: uuid.UUID,
    response_time_ms: Optional[int],
    result_payload: Optional[dict[str, Any]] = None,
) -> None:
    try:
        detection = DetectionTask.objects.get(id=detection_id)
    except DetectionTask.DoesNotExist:  # pragma: no cover
        return

    detection.mark_succeeded(response_time_ms, result_payload or {})
