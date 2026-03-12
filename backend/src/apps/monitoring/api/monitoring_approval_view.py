from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import AuditLog
from apps.monitoring.models import MonitoringRequest
from apps.monitoring.serializers import MonitoringRequestSerializer
from apps.monitoring.services.monitoring_job_service import create_job_for_request


class MonitoringRequestApproveView(APIView):
    """
    平台内审批：通过
    - 仅系统管理员允许操作（IsAdminUser）
    - 仅允许对 pending 状态的申请执行
    - 通过后创建 MonitoringJob，并在探针-调度页面中可见
    """

    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request: Request, pk: str) -> Response:
        monitoring_request = get_object_or_404(MonitoringRequest, pk=pk)
        if monitoring_request.status != MonitoringRequest.Status.PENDING:
            return Response(
                {"detail": "仅允许审批待处理（pending）的申请"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        approver = (request.user.get_username() if request.user else None) or None
        monitoring_request.mark_approved(approver)
        create_job_for_request(monitoring_request)

        AuditLog.objects.create(
            actor=request.user,
            action="monitoring_request.approve",
            target_type="MonitoringRequest",
            target_id=str(monitoring_request.id),
            metadata={"status": monitoring_request.status},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(MonitoringRequestSerializer(monitoring_request).data, status=status.HTTP_200_OK)


class MonitoringRequestRejectView(APIView):
    """
    平台内审批：驳回
    - 仅系统管理员允许操作（IsAdminUser）
    - 仅允许对 pending 状态的申请执行
    - 驳回后申请人可修改并重新提交（后续再补“重新提交”接口/前端入口）
    """

    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request: Request, pk: str) -> Response:
        monitoring_request = get_object_or_404(MonitoringRequest, pk=pk)
        if monitoring_request.status != MonitoringRequest.Status.PENDING:
            return Response(
                {"detail": "仅允许驳回待处理（pending）的申请"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = (request.data or {}).get("reason")
        monitoring_request.mark_rejected(str(reason) if reason else None)

        AuditLog.objects.create(
            actor=request.user,
            action="monitoring_request.reject",
            target_type="MonitoringRequest",
            target_id=str(monitoring_request.id),
            metadata={"status": monitoring_request.status, "reason": reason},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(MonitoringRequestSerializer(monitoring_request).data, status=status.HTTP_200_OK)


class MonitoringRequestResubmitView(APIView):
    """
    重新提交（平台内审批）：
    - 申请人本人或系统管理员可操作
    - 仅允许对 rejected 状态的申请执行
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, pk: str) -> Response:
        monitoring_request = get_object_or_404(MonitoringRequest, pk=pk)
        if monitoring_request.status != MonitoringRequest.Status.REJECTED:
            return Response(
                {"detail": "仅允许重新提交已驳回（rejected）的申请"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_admin = bool(getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False))
        if not is_admin and monitoring_request.created_by_id and str(monitoring_request.created_by_id) != str(request.user.id):
            return Response({"detail": "仅允许申请人重新提交该申请"}, status=status.HTTP_403_FORBIDDEN)
        if not is_admin and monitoring_request.created_by_id is None:
            return Response({"detail": "缺少申请人信息，无法重新提交"}, status=status.HTTP_400_BAD_REQUEST)

        monitoring_request.status = MonitoringRequest.Status.PENDING
        meta = dict(monitoring_request.metadata or {})
        meta.pop("reject_reason", None)
        monitoring_request.metadata = meta
        monitoring_request.updated_by = request.user
        monitoring_request.save(update_fields=["status", "metadata", "updated_by", "updated_at"])

        AuditLog.objects.create(
            actor=request.user,
            action="monitoring_request.resubmit",
            target_type="MonitoringRequest",
            target_id=str(monitoring_request.id),
            metadata={"status": monitoring_request.status},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(MonitoringRequestSerializer(monitoring_request).data, status=status.HTTP_200_OK)
