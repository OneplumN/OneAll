from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class AlertChannel(BaseModel):
    channel_type = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    enabled = models.BooleanField(default=False)
    config = models.JSONField(default=dict, blank=True)
    last_test_status = models.CharField(max_length=32, default="unknown")
    last_test_at = models.DateTimeField(null=True, blank=True)
    last_test_message = models.TextField(blank=True)

    class Meta:
        db_table = "settings_alert_channel"
        verbose_name = "Alert Channel"
        verbose_name_plural = "Alert Channels"

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.name} ({self.channel_type})"
