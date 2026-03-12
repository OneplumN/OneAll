from __future__ import annotations

from typing import Iterable, List, Optional

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils import timezone

from apps.assets.models import AssetSyncRun
from apps.assets.services.sync_service import sync_assets
from apps.assets.tasks.asset_sync_task import run_asset_sync


class AssetSyncTriggerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        payload = request.data or {}
        sources = self._parse_sources(payload)
        mode = str(payload.get("mode") or payload.get("run_mode") or "").strip().lower()

        if mode == "sync":
            run = AssetSyncRun.objects.create(
                mode=AssetSyncRun.Mode.SYNC,
                status=AssetSyncRun.Status.RUNNING,
                source_filters=list(sources or []),
                started_at=timezone.now(),
                created_by=request.user,
                updated_by=request.user,
            )
            try:
                result = sync_assets(sources, run=run)
            except Exception as exc:
                run.status = AssetSyncRun.Status.FAILED
                run.finished_at = timezone.now()
                run.error_message = str(exc)
                run.save(update_fields=["status", "finished_at", "error_message", "updated_at"])
                raise
            return Response(
                {"detail": "资产同步完成", "run_id": str(run.id), "result": result},
                status=status.HTTP_200_OK,
            )

        run = AssetSyncRun.objects.create(
            mode=AssetSyncRun.Mode.ASYNC,
            status=AssetSyncRun.Status.QUEUED,
            source_filters=list(sources or []),
            created_by=request.user,
            updated_by=request.user,
        )
        run_asset_sync.delay(str(run.id), sources)
        return Response(
            {"detail": "资产同步任务已触发", "run_id": str(run.id)},
            status=status.HTTP_202_ACCEPTED,
        )

    @staticmethod
    def _parse_sources(payload: dict) -> Optional[List[str]]:
        raw_sources: Iterable[str] | str | None = payload.get("sources") or payload.get("source")
        if raw_sources is None:
            return None
        if isinstance(raw_sources, str):
            raw_sources = [raw_sources]
        normalized = [value.strip() for value in raw_sources if isinstance(value, str) and value.strip()]
        return normalized or None
