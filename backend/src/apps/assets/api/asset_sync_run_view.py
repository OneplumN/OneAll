from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.models import AssetSyncChange, AssetSyncRun
from apps.core.permissions import RequirePermission

from .asset_sync_run_serializers import AssetSyncChangeSerializer, AssetSyncRunSerializer


class AssetSyncRunListView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.view")]

    def get(self, request: Request) -> Response:
        limit = min(int(request.query_params.get("limit") or 20), 100)
        offset = max(int(request.query_params.get("offset") or 0), 0)
        status_filter = str(request.query_params.get("status") or "").strip()
        mode_filter = str(request.query_params.get("mode") or "").strip()

        qs: QuerySet[AssetSyncRun] = AssetSyncRun.objects.all()
        if status_filter:
            qs = qs.filter(status=status_filter)
        if mode_filter:
            qs = qs.filter(mode=mode_filter)

        total = qs.count()
        runs = list(qs.order_by("-created_at")[offset : offset + limit])
        serializer = AssetSyncRunSerializer(runs, many=True)
        return Response({"total": total, "items": serializer.data}, status=status.HTTP_200_OK)


class AssetSyncRunDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.view")]

    def get(self, request: Request, run_id) -> Response:
        include_changes = str(request.query_params.get("include_changes") or "").strip().lower() in {"1", "true", "yes"}
        changes_limit = min(int(request.query_params.get("changes_limit") or 200), 1000)

        run = get_object_or_404(AssetSyncRun, pk=run_id)
        run_data = AssetSyncRunSerializer(run).data

        if not include_changes:
            return Response(run_data, status=status.HTTP_200_OK)

        changes = list(
            AssetSyncChange.objects.filter(run=run).order_by("-created_at")[:changes_limit]
        )
        change_data = AssetSyncChangeSerializer(changes, many=True).data
        return Response({**run_data, "changes": change_data}, status=status.HTTP_200_OK)

