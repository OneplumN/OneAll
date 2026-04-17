from __future__ import annotations

import uuid
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import RequirePermission
from apps.monitoring.models import DetectionTask
from apps.monitoring.serializers.detection_serializer import DetectionTaskSerializer
from apps.monitoring.services import detection_service


class DetectionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("detection.oneoff.view")]

    def get(self, request: Request, detection_id: str) -> Response:
        task_id = detection_id if isinstance(detection_id, uuid.UUID) else uuid.UUID(str(detection_id))
        task = get_object_or_404(DetectionTask, id=task_id)
        self._expire_if_overdue(task)
        task.refresh_from_db()
        serializer = DetectionTaskSerializer(task)
        return Response(serializer.data)

    @staticmethod
    def _expire_if_overdue(task: DetectionTask) -> None:
        if task.status not in {DetectionTask.Status.SCHEDULED, DetectionTask.Status.RUNNING}:
            return

        timeout_seconds = _resolve_timeout_seconds(task)
        started_at = _resolve_timeout_anchor(task)
        if started_at is None:
            return
        deadline = started_at + timedelta(seconds=timeout_seconds)
        if deadline > timezone.now():
            return

        detection_service.mark_detection_timeout(task.id)


def _resolve_timeout_seconds(task: DetectionTask) -> int:
    metadata = task.metadata or {}
    value = metadata.get("timeout_seconds")
    if value is None:
        config = metadata.get("config")
        if isinstance(config, dict):
            value = config.get("timeout_seconds")
    try:
        timeout = int(value)
    except (TypeError, ValueError):
        timeout = 30
    return max(timeout, 1)


def _resolve_timeout_anchor(task: DetectionTask):
    if task.status == DetectionTask.Status.RUNNING:
        return task.claimed_at or task.published_at or task.created_at
    if task.status == DetectionTask.Status.SCHEDULED:
        return task.published_at or task.created_at
    return None
