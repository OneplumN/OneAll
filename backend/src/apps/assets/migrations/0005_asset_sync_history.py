from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0004_assetrecord_soft_delete_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetSyncRun",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assetsyncrun_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assetsyncrun_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "mode",
                    models.CharField(
                        choices=[("sync", "同步"), ("async", "异步")],
                        default="async",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("queued", "排队中"),
                            ("running", "执行中"),
                            ("succeeded", "成功"),
                            ("failed", "失败"),
                            ("script_triggered", "脚本已触发"),
                        ],
                        default="queued",
                        max_length=32,
                    ),
                ),
                ("source_filters", models.JSONField(blank=True, default=list)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("summary", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True, default="")),
            ],
            options={
                "db_table": "assets_asset_sync_run",
                "ordering": ("-created_at",),
                "verbose_name": "Asset Sync Run",
                "verbose_name_plural": "Asset Sync Runs",
            },
        ),
        migrations.CreateModel(
            name="AssetSyncChange",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assetsyncchange_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assetsyncchange_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("source", models.CharField(blank=True, default="", max_length=32)),
                ("external_id", models.CharField(blank=True, default="", max_length=128)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("create", "新增"),
                            ("update", "更新"),
                            ("restore", "恢复"),
                            ("soft_delete", "软删除"),
                        ],
                        max_length=32,
                    ),
                ),
                ("changed_fields", models.JSONField(blank=True, default=list)),
                ("before", models.JSONField(blank=True, default=dict)),
                ("after", models.JSONField(blank=True, default=dict)),
                (
                    "record",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sync_changes",
                        to="assets.assetrecord",
                    ),
                ),
                (
                    "run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="changes",
                        to="assets.assetsyncrun",
                    ),
                ),
            ],
            options={
                "db_table": "assets_asset_sync_change",
                "ordering": ("-created_at",),
                "verbose_name": "Asset Sync Change",
                "verbose_name_plural": "Asset Sync Changes",
            },
        ),
    ]

