from __future__ import annotations

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services.report_service import build_detection_report


class DetectionReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        days = int(request.query_params.get('days', 30))
        report = build_detection_report(days=days)
        return Response(report)
