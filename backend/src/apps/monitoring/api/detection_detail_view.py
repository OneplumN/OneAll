from __future__ import annotations

import uuid

from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.monitoring.models import DetectionTask
from apps.monitoring.serializers.detection_serializer import DetectionTaskSerializer


class DetectionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, detection_id: str) -> Response:
        task_id = detection_id if isinstance(detection_id, uuid.UUID) else uuid.UUID(str(detection_id))
        task = get_object_or_404(DetectionTask, id=task_id)
        serializer = DetectionTaskSerializer(task)
        return Response(serializer.data)
