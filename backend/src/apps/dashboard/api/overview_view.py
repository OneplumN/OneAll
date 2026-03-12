from __future__ import annotations

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.services.overview_service import get_overview_metrics


class DashboardOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        metrics = get_overview_metrics()
        return Response(metrics)
