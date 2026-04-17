from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import AuditLog
from apps.monitoring.models import MonitoringRequest
from apps.monitoring.serializers import MonitoringRequestSerializer
from apps.monitoring.serializers.monitoring_request_serializer import MonitoringRequestUpdateSerializer
from apps.monitoring.models.monitoring_job import MonitoringJob
from apps.monitoring.services.monitoring_job_service import sync_job_from_request


class MonitoringRequestDetailView(APIView):
    """
    工单申请详情与修改：
    - 仅允许在 rejected 状态下修改
    - 申请人本人或系统管理员可修改
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        instance = get_object_or_404(MonitoringRequest.objects.select_related("created_by"), pk=pk)
        return Response(MonitoringRequestSerializer(instance).data, status=status.HTTP_200_OK)

    def patch(self, request: Request, pk: str) -> Response:
        instance = get_object_or_404(MonitoringRequest.objects.select_related("created_by"), pk=pk)
        editable_statuses = {MonitoringRequest.Status.REJECTED, MonitoringRequest.Status.APPROVED}
        if instance.status not in editable_statuses:
            return Response(
                {"detail": "仅允许修改已驳回（rejected）或已通过（approved）的申请"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_admin = bool(getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False))
        if not is_admin and instance.created_by_id and str(instance.created_by_id) != str(request.user.id):
            return Response({"detail": "仅允许申请人修改该申请"}, status=status.HTTP_403_FORBIDDEN)
        if not is_admin and instance.created_by_id is None:
            return Response({"detail": "缺少申请人信息，无法修改"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = MonitoringRequestUpdateSerializer(instance, data=request.data or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save(updated_by=request.user)

        # 已通过的申请：修改后立即生效（同步到 MonitoringJob -> ProbeSchedule -> 探针配置）
        if updated.status == MonitoringRequest.Status.APPROVED:
            from apps.alerts.services import ensure_schedule_for_monitoring_job
            from apps.probes.services.probe_schedule_service import sync_schedule_from_job
            from apps.probes.services import schedule_config_service

            jobs = list(
                MonitoringJob.objects.filter(request=updated, status=MonitoringJob.Status.ACTIVE).select_related("probe_schedule")
            )
            probe_ids_to_refresh: set[str] = set()

            for job in jobs:
                sync_job_from_request(job, updated)

                schedule = getattr(job, "probe_schedule", None)
                if schedule:
                    probe_ids_to_refresh.update(str(pid) for pid in schedule.probes.values_list("id", flat=True))

                schedule = sync_schedule_from_job(job)
                probe_ids_to_refresh.update(str(pid) for pid in schedule.probes.values_list("id", flat=True))

                ensure_schedule_for_monitoring_job(job)

            if probe_ids_to_refresh:
                schedule_config_service.request_probe_refresh(list(probe_ids_to_refresh))

        AuditLog.objects.create(
            actor=request.user,
            action="monitoring_request.update",
            target_type="MonitoringRequest",
            target_id=str(updated.id),
            metadata={"fields": list(serializer.validated_data.keys())},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(MonitoringRequestSerializer(updated).data, status=status.HTTP_200_OK)
