from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class AssetSyncRun(BaseModel):
    class Mode(models.TextChoices):
        SYNC = "sync", "同步"
        ASYNC = "async", "异步"

    class Status(models.TextChoices):
        QUEUED = "queued", "排队中"
        RUNNING = "running", "执行中"
        SUCCEEDED = "succeeded", "成功"
        FAILED = "failed", "失败"
        SCRIPT_TRIGGERED = "script_triggered", "脚本已触发"

    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.ASYNC)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
    source_filters = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "assets_asset_sync_run"
        ordering = ("-created_at",)
        verbose_name = "Asset Sync Run"
        verbose_name_plural = "Asset Sync Runs"


class AssetSyncChange(BaseModel):
    class Action(models.TextChoices):
        CREATE = "create", "新增"
        UPDATE = "update", "更新"
        RESTORE = "restore", "恢复"
        SOFT_DELETE = "soft_delete", "软删除"

    run = models.ForeignKey(AssetSyncRun, on_delete=models.CASCADE, related_name="changes")
    record = models.ForeignKey(
        "assets.AssetRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sync_changes",
    )
    source = models.CharField(max_length=32, blank=True, default="")
    external_id = models.CharField(max_length=128, blank=True, default="")
    action = models.CharField(max_length=32, choices=Action.choices)
    changed_fields = models.JSONField(default=list, blank=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "assets_asset_sync_change"
        ordering = ("-created_at",)
        verbose_name = "Asset Sync Change"
        verbose_name_plural = "Asset Sync Changes"

