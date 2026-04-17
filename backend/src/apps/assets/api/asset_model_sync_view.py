from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils import timezone

from apps.assets.models import AssetModel
from apps.assets.models.asset_sync_run import AssetSyncRun
from apps.assets.services.sync_service import sync_asset_model
from apps.core.permissions import RequirePermission


class AssetModelSyncView(APIView):
    """Trigger sync for a specific AssetModel via its bound script."""

    permission_classes = [permissions.IsAuthenticated, RequirePermission("assets.records.manage")]

    def post(self, request: Request, model_id) -> Response:
        model = get_object_or_404(AssetModel, pk=model_id)
        run = AssetSyncRun.objects.create(
            mode=AssetSyncRun.Mode.SYNC,
            status=AssetSyncRun.Status.RUNNING,
            source_filters=[model.key],
            started_at=timezone.now(),
            created_by=request.user,
            updated_by=request.user,
        )
        try:
            summary = sync_asset_model(model, run=run)
        except ValueError as exc:
            run.status = AssetSyncRun.Status.FAILED
            run.finished_at = timezone.now()
            run.error_message = str(exc)
            run.save(update_fields=["status", "finished_at", "error_message", "updated_at"])
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:  # pragma: no cover - defensive
            run.status = AssetSyncRun.Status.FAILED
            run.finished_at = timezone.now()
            run.error_message = f"{exc.__class__.__name__}: {exc}"
            run.save(update_fields=["status", "finished_at", "error_message", "updated_at"])
            return Response(
                {"detail": f"资产同步失败：{exc.__class__.__name__}: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        run.status = AssetSyncRun.Status.SUCCEEDED
        run.finished_at = timezone.now()
        run.summary = summary
        run.save(update_fields=["status", "finished_at", "summary", "updated_at"])

        return Response(
            {
                "detail": "资产同步完成",
                "run_id": str(run.id),
                "model_key": model.key,
                "summary": summary,
            },
            status=status.HTTP_200_OK,
        )
