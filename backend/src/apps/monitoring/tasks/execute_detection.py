from __future__ import annotations

import uuid

from celery import shared_task
from django.utils import timezone

from apps.monitoring.models import DetectionTask
from apps.monitoring.repositories import detection_metrics
from apps.monitoring.services import detection_service


@shared_task(name="apps.monitoring.tasks.execute_detection")
def execute_detection_task(detection_id: str) -> dict[str, str]:
    task_id = uuid.UUID(detection_id)

    detection = DetectionTask.objects.get(id=task_id)
    detection.mark_running()

    # Placeholder implementation: real probe execution handled by probe runner integration
    detection_service.mark_detection_succeeded(task_id, response_time_ms=None, result_payload={})
    detection.refresh_from_db()
    detection_metrics.store_detection_result(
        detection_id=task_id,
        probe_id=detection.probe_id,
        protocol=detection.protocol,
        target=detection.target,
        status=detection.status,
        response_time_ms=detection.response_time_ms,
        metadata=detection.result_payload,
        recorded_at=detection.executed_at or timezone.now(),
    )

    return {"detection_id": detection_id, "status": detection.status}
