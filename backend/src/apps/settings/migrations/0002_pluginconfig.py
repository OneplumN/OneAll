from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PluginConfig",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("name", models.CharField(max_length=128, unique=True)),
                ("type", models.CharField(max_length=64)),
                ("enabled", models.BooleanField(default=True)),
                ("config", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(default="unknown", max_length=32)),
                ("last_checked_at", models.DateTimeField(blank=True, null=True)),
                ("last_message", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="pluginconfig_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="pluginconfig_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Monitoring Plugin Config",
                "verbose_name_plural": "Monitoring Plugin Configs",
                "db_table": "settings_plugin_config",
            },
        ),
    ]
