from __future__ import annotations

import uuid

from celery import shared_task

from apps.monitoring.models import DetectionTask
from apps.monitoring.services import detection_service


@shared_task(name="apps.monitoring.tasks.expire_detection")
def expire_detection_task(detection_id: str) -> dict[str, str]:
    task_id = uuid.UUID(detection_id)
    try:
        detection = DetectionTask.objects.get(id=task_id)
    except DetectionTask.DoesNotExist:  # pragma: no cover
        return {"detection_id": detection_id, "status": "missing"}

    is_one_off = (detection.metadata or {}).get("execution_source") == "one_off"

    if detection.status in {
        DetectionTask.Status.SCHEDULED,
        DetectionTask.Status.RUNNING,
    } and (is_one_off or detection.published_at is not None):
        detection_service.mark_detection_timeout(task_id)
        detection.refresh_from_db(fields=["status"])

    return {"detection_id": detection_id, "status": detection.status}
