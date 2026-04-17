from __future__ import annotations

import uuid

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.monitoring.models import DetectionTask
from apps.monitoring.serializers.detection_serializer import (
    DetectionRequestSerializer,
    DetectionTaskSerializer,
)
from apps.monitoring.services.detection_service import (
    DetectionRequest,
    schedule_one_off_detection,
)
from apps.monitoring.services.detection_scheduler import ProbeCapacityError, ProbeUnavailableError


class OneOffDetectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = DetectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        try:
            detection = schedule_one_off_detection(
                DetectionRequest(
                    target=validated['target'],
                    protocol=validated['protocol'],
                    probe_id=str(validated['probe_id']) if validated.get('probe_id') else None,
                    timeout_seconds=validated['timeout_seconds'],
                    metadata=validated.get('metadata', {}),
                )
            )
        except (ProbeUnavailableError, ProbeCapacityError) as exc:
            return Response(
                {
                    'detail': str(exc),
                    'suggestions': getattr(exc, 'suggestions', []),
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = DetectionTaskSerializer(detection)
        return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)
