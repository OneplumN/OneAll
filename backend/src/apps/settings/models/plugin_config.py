from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class PluginConfig(BaseModel):
    name = models.CharField(max_length=128, unique=True)
    type = models.CharField(max_length=64)
    enabled = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, default="unknown")
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_message = models.TextField(blank=True)

    class Meta:
        db_table = "settings_plugin_config"
        verbose_name = "Monitoring Plugin Config"
        verbose_name_plural = "Monitoring Plugin Configs"
