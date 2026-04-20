from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import RequirePermission
from apps.settings.services import alert_channel_service


class AlertChannelListView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.channels.view")]

    def get(self, request: Request) -> Response:
        data = alert_channel_service.list_channels()
        return Response({"channels": data})


class AlertChannelUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.channels.update")]

    def put(self, request: Request, channel_type: str) -> Response:
        payload = request.data or {}
        enabled = payload.get("enabled", False)
        config = payload.get("config") or {}
        try:
            record = alert_channel_service.update_channel(
                channel_type=channel_type,
                enabled=enabled,
                config=config,
                actor=request.user,
                meta={"ip": request.META.get("REMOTE_ADDR"), "ua": request.META.get("HTTP_USER_AGENT", "")},
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(record)


class AlertChannelTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("alerts.channels.test")]

    def post(self, request: Request, channel_type: str) -> Response:
        result = alert_channel_service.test_channel(
            channel_type=channel_type,
            actor=request.user,
            meta={"ip": request.META.get("REMOTE_ADDR"), "ua": request.META.get("HTTP_USER_AGENT", "")},
        )
        return Response(result, status=status.HTTP_200_OK)
