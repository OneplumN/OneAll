from __future__ import annotations

import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.monitoring.models import DetectionTask
from apps.monitoring.serializers.detection_serializer import DetectionTaskSerializer
from apps.monitoring.services.detection_claim_service import claim_one_off_detection
from apps.monitoring.services.detection_result_service import (
    DetectionResultPayload,
    submit_detection_result,
)
from apps.probes.authentication import ensure_probe_authenticated
from apps.probes.models import ProbeNode, ProbeSchedule
from apps.probes.services import schedule_execution_service
from apps.probes.services import probe_task_service


class ProbeTaskClaimRequestSerializer(serializers.Serializer):
    probe_id = serializers.UUIDField()
    limit = serializers.IntegerField(min_value=1, max_value=10, default=1, required=False)


class ProbeTaskResultRequestSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=32)
    message = serializers.CharField(required=False, allow_blank=True)
    response_time_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    status_code = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)
    finished_at = serializers.DateTimeField(required=False, allow_null=True)


class ProbeScheduleResultRequestSerializer(serializers.Serializer):
    probe_id = serializers.UUIDField()
    scheduled_at = serializers.DateTimeField()
    status = serializers.CharField(max_length=32)
    message = serializers.CharField(required=False, allow_blank=True)
    response_time_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    status_code = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)
    finished_at = serializers.DateTimeField(required=False, allow_null=True)


class ProbeTaskClaimView(APIView):
    permission_classes: list = []
    authentication_classes: list = []

    def post(self, request, *args, **kwargs):
        serializer = ProbeTaskClaimRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        probe = get_object_or_404(ProbeNode, id=serializer.validated_data["probe_id"])
        ensure_probe_authenticated(request, probe)

        claimed = claim_one_off_detection(probe=probe)
        if claimed is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {
                "task_id": claimed.task_id,
                "target": claimed.target,
                "protocol": claimed.protocol,
                "timeout_seconds": claimed.timeout_seconds,
                "expected_status": claimed.expected_status,
                "metadata": claimed.metadata,
                "scheduled_at": claimed.scheduled_at,
            },
            status=status.HTTP_200_OK,
        )


class ProbeTaskResultView(APIView):
    permission_classes: list = []
    authentication_classes: list = []

    def post(self, request, task_id: uuid.UUID, *args, **kwargs):
        detection = get_object_or_404(DetectionTask, id=task_id)
        if not detection.probe_id:
            raise PermissionDenied("detection task is not bound to probe")

        probe = get_object_or_404(ProbeNode, id=detection.probe_id)
        ensure_probe_authenticated(request, probe)

        serializer = ProbeTaskResultRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = serializer.validated_data
        try:
            detection = submit_detection_result(
                probe=probe,
                detection_id=task_id,
                payload=DetectionResultPayload(
                    status=payload["status"],
                    message=payload.get("message", ""),
                    response_time_ms=payload.get("response_time_ms"),
                    status_code=payload.get("status_code"),
                    metadata=payload.get("metadata") or {},
                    executed_at=payload.get("finished_at") or timezone.now(),
                ),
            )
        except PermissionError as exc:
            raise AuthenticationFailed(str(exc)) from exc

        return Response(DetectionTaskSerializer(detection).data, status=status.HTTP_200_OK)


class ProbeNodeTaskListCompatView(APIView):
    """Legacy HTTP task pull endpoint: GET /probes/nodes/<id>/tasks/."""

    permission_classes: list = []
    authentication_classes: list = []

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        probe = get_object_or_404(ProbeNode, id=pk)
        ensure_probe_authenticated(request, probe)

        claimed = claim_one_off_detection(probe=probe)
        if claimed is None:
            claimed = self._claim_legacy_detection(probe)
        if claimed is None:
            return Response([], status=status.HTTP_200_OK)

        return Response(
            [
                {
                    "task_id": claimed.task_id,
                    "target": claimed.target,
                    "protocol": claimed.protocol,
                    "timeout_seconds": claimed.timeout_seconds,
                    "expect_status": claimed.expected_status,
                    "metadata": claimed.metadata,
                    "scheduled_at": claimed.scheduled_at,
                }
            ],
            status=status.HTTP_200_OK,
        )

    def _claim_legacy_detection(self, probe: ProbeNode):
        with transaction.atomic():
            detection = (
                DetectionTask.objects.select_for_update(skip_locked=True)
                .filter(
                    probe=probe,
                    status=DetectionTask.Status.SCHEDULED,
                )
                .order_by("created_at", "id")
                .first()
            )
            if detection is None:
                return None

            metadata = dict(detection.metadata or {})
            config = metadata.get("config")
            if isinstance(config, dict):
                for key, value in config.items():
                    metadata.setdefault(key, value)

            now = timezone.now()
            detection.mark_running(published_at=now, claimed_at=now)

            return type(
                "LegacyClaimedDetection",
                (),
                {
                    "task_id": str(detection.id),
                    "target": detection.target,
                    "protocol": detection.protocol,
                    "timeout_seconds": probe_task_service.timeout_from_metadata(metadata),
                    "expected_status": probe_task_service.expect_status_from_metadata(metadata),
                    "metadata": metadata,
                    "scheduled_at": detection.created_at.isoformat(),
                },
            )()


class ProbeNodeTaskResultCompatView(APIView):
    """Legacy HTTP result endpoint: POST /probes/nodes/<id>/tasks/<task_id>/result/."""

    permission_classes: list = []
    authentication_classes: list = []

    def post(self, request, pk: uuid.UUID, task_id: uuid.UUID, *args, **kwargs):
        probe = get_object_or_404(ProbeNode, id=pk)
        ensure_probe_authenticated(request, probe)

        detection = get_object_or_404(DetectionTask, id=task_id)
        if detection.probe_id and detection.probe_id != probe.id:
            raise PermissionDenied("detection task is not bound to probe")

        payload = dict(request.data or {})
        response_time_ms = payload.get("response_time_ms")
        if response_time_ms is None:
            response_time_ms = payload.get("latency_ms")

        try:
            submit_detection_result(
                probe=probe,
                detection_id=task_id,
                payload=DetectionResultPayload(
                    status=str(payload.get("status") or ""),
                    message=str(payload.get("message") or ""),
                    response_time_ms=response_time_ms,
                    status_code=payload.get("status_code"),
                    metadata=payload.get("metadata") or {},
                    executed_at=timezone.now(),
                ),
            )
        except PermissionError as exc:
            raise AuthenticationFailed(str(exc)) from exc

        return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)


class ProbeScheduleResultView(APIView):
    permission_classes: list = []
    authentication_classes: list = []

    def post(self, request, schedule_id: uuid.UUID, *args, **kwargs):
        schedule = get_object_or_404(ProbeSchedule, id=schedule_id)

        serializer = ProbeScheduleResultRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = serializer.validated_data
        probe = get_object_or_404(ProbeNode, id=payload["probe_id"])
        ensure_probe_authenticated(request, probe)

        if not schedule.probes.filter(id=probe.id).exists():
            raise PermissionDenied("probe is not assigned to schedule")

        execution = schedule_execution_service.record_result(
            schedule=schedule,
            probe=probe,
            scheduled_at=payload["scheduled_at"],
            status=payload["status"],
            response_time_ms=payload.get("response_time_ms"),
            status_code=payload.get("status_code"),
            message=payload.get("message"),
            metadata=payload.get("metadata") or {},
        )

        response_payload = {
            "id": str(execution.id),
            "schedule_id": str(schedule.id),
            "probe_id": str(probe.id),
            "status": execution.status,
            "scheduled_at": execution.scheduled_at,
            "finished_at": execution.finished_at,
            "response_time_ms": execution.response_time_ms,
            "status_code": execution.status_code,
            "message": execution.message,
            "metadata": execution.metadata,
        }
        return Response(response_payload, status=status.HTTP_200_OK)
