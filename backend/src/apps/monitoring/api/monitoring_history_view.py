from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.monitoring.repositories.monitoring_history_repository import MonitoringHistoryFilters
from apps.monitoring.serializers.monitoring_history_serializer import (
    MonitoringHistoryQuerySerializer,
    MonitoringHistoryTaskSerializer,
)
from apps.monitoring.services import monitoring_history_service


class MonitoringHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        query_serializer = MonitoringHistoryQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        data = query_serializer.validated_data

        filters = MonitoringHistoryFilters(
            target=data.get("target"),
            status=data.get("status"),
            protocol=data.get("protocol"),
            probe_id=str(data["probe_id"]) if data.get("probe_id") else None,
            started_after=data.get("started_after"),
            started_before=data.get("started_before"),
        )

        result = monitoring_history_service.query_history(
            filters=filters, page=data.get("page", 1), page_size=data.get("page_size", 20)
        )

        item_serializer = MonitoringHistoryTaskSerializer(result.items, many=True)
        response_payload = {
            "items": item_serializer.data,
            "aggregates": {
                "total_count": result.aggregates.total_count,
                "status_counts": result.aggregates.status_counts,
                "average_response_time_ms": result.aggregates.average_response_time_ms,
                "success_rate": result.aggregates.success_rate,
            },
            "pagination": {
                "page": result.pagination.page,
                "page_size": result.pagination.page_size,
                "total_items": result.pagination.total_items,
                "total_pages": result.pagination.total_pages,
            },
        }

        return Response(response_payload, status=status.HTTP_200_OK)
