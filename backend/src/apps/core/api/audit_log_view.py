from __future__ import annotations

from django.utils.dateparse import parse_datetime
from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.core.permissions import RequirePermission
from apps.core.models import AuditLog
from apps.core.serializers import AuditLogSerializer


class AuditLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):  # pragma: no cover - thin wrapper
        return Response(
            {
                "results": data,
                "pagination": {
                    "page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                    "total": self.page.paginator.count,
                },
            }
        )


class AuditLogListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("settings.audit_log.view")]
    serializer_class = AuditLogSerializer
    pagination_class = AuditLogPagination

    def get_queryset(self):  # pragma: no cover - simple queryset builder
        queryset = AuditLog.objects.all()
        params = self.request.query_params

        actor = params.get("actor")
        if actor:
            queryset = queryset.filter(actor_id=actor)

        action = params.get("action")
        if action:
            queryset = queryset.filter(action__icontains=action)

        target_type = params.get("target_type")
        if target_type:
            queryset = queryset.filter(target_type__icontains=target_type)

        start = params.get("start")
        if start:
            start_dt = parse_datetime(start)
            if start_dt:
                queryset = queryset.filter(occurred_at__gte=start_dt)

        end = params.get("end")
        if end:
            end_dt = parse_datetime(end)
            if end_dt:
                queryset = queryset.filter(occurred_at__lte=end_dt)

        return queryset.order_by("-occurred_at", "-created_at")
