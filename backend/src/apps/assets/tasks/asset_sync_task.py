from __future__ import annotations

from celery import shared_task

from typing import Sequence

from django.utils import timezone

from apps.assets.models import AssetSyncRun
from apps.assets.services.sync_service import sync_assets


@shared_task(name="apps.assets.tasks.sync_assets")
def run_asset_sync(run_id: str, sources: Sequence[str] | None = None) -> dict[str, int]:
    run = AssetSyncRun.objects.filter(id=run_id).first()
    if run:
        run.status = AssetSyncRun.Status.RUNNING
        run.started_at = run.started_at or timezone.now()
        run.save(update_fields=["status", "started_at", "updated_at"])
    try:
        return sync_assets(sources, run=run)
    except Exception as exc:
        if run:
            run.status = AssetSyncRun.Status.FAILED
            run.finished_at = timezone.now()
            run.error_message = str(exc)
            run.save(update_fields=["status", "finished_at", "error_message", "updated_at"])
        raise
