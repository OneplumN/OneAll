from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.monitoring.services.zabbix_service import (
    ZabbixServiceError,
    fetch_dashboard_snapshot,
    get_cached_snapshot,
    is_snapshot_fresh,
    resolve_refresh_interval_seconds,
    store_snapshot,
    test_connectivity,
    trigger_manual_sync,
)
from apps.monitoring.tasks.zabbix_dashboard_refresh import (
    refresh_zabbix_dashboard_snapshot,
)


class ZabbixDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        force_refresh = request.query_params.get("force")
        if _is_truthy(force_refresh):
            try:
                snapshot = fetch_dashboard_snapshot(force_refresh=True)
            except ZabbixServiceError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            payload = store_snapshot(snapshot)
            return Response(_build_snapshot_response(payload))

        payload = get_cached_snapshot()
        if payload is None:
            try:
                snapshot = fetch_dashboard_snapshot()
            except ZabbixServiceError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            payload = store_snapshot(snapshot)
        else:
            interval = resolve_refresh_interval_seconds()
            if not is_snapshot_fresh(payload, interval):
                refresh_zabbix_dashboard_snapshot.delay()
        return Response(_build_snapshot_response(payload))


class ZabbixTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = test_connectivity()
        except ZabbixServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"detail": "连接正常", **data})


class ZabbixSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = trigger_manual_sync()
        except ZabbixServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(data, status=status.HTTP_202_ACCEPTED)


def _build_snapshot_response(payload: dict) -> dict:
    snapshot = dict(payload.get("snapshot") or {})
    snapshot["refreshed_at"] = payload.get("refreshed_at")
    return snapshot


def _is_truthy(value) -> bool:
    if value is None:
        return False
    normalized = str(value).strip().lower()
    return normalized in {"1", "true", "yes", "on"}
