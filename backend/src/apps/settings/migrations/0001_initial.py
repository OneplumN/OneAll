from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemSettings",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("platform_name", models.CharField(default="OneAll 智能运维平台", max_length=128)),
                ("default_timezone", models.CharField(default="Asia/Shanghai", max_length=64)),
                ("alert_escalation_threshold", models.PositiveIntegerField(default=60)),
                ("theme", models.CharField(default="light", max_length=32)),
                ("notification_channels", models.JSONField(blank=True, default=dict)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="systemsettings_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="systemsettings_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "System Settings",
                "verbose_name_plural": "System Settings",
                "db_table": "settings_system_settings",
            },
        ),
    ]
