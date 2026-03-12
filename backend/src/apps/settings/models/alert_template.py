from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class AlertTemplate(BaseModel):
    channel_type = models.CharField(max_length=32)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "settings_alert_template"
        unique_together = ("channel_type", "name")
        ordering = ("channel_type", "-is_default", "name")

    def __str__(self) -> str:  # pragma: no cover - admin helper
        return f"{self.name} ({self.channel_type})"
