from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.monitoring.serializers import (
    MonitoringRequestCreateSerializer,
    MonitoringRequestSerializer,
)
from apps.monitoring.models import MonitoringRequest


class MonitoringRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        queryset = MonitoringRequest.objects.select_related("created_by").all().order_by("-created_at")
        serializer = MonitoringRequestSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = MonitoringRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        monitoring_request = serializer.save(created_by=request.user, updated_by=request.user)

        response_data = MonitoringRequestSerializer(monitoring_request).data
        return Response(response_data, status=status.HTTP_201_CREATED)
