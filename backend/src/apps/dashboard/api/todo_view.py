from __future__ import annotations

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import RequirePermission
from apps.dashboard.services.todo_service import get_todo_items


class DashboardTodoView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("monitoring.overview.view")]

    def get(self, request: Request) -> Response:  # pragma: no cover - thin wrapper
        try:
            limit = int(request.query_params.get("limit", 5))
        except (TypeError, ValueError):
            limit = 5

        data = get_todo_items(limit=max(1, min(limit, 20)))
        return Response(data)
