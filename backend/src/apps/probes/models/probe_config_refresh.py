from __future__ import annotations

from django.db import models
from django.utils import timezone

from apps.core.models.base import BaseModel


class ProbeConfigRefreshRequest(BaseModel):
    probe = models.ForeignKey(
        "probes.ProbeNode",
        on_delete=models.CASCADE,
        related_name="config_refresh_requests",
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "probes_config_refresh_request"
        indexes = [
            models.Index(fields=["probe", "processed_at"]),
        ]
        ordering = ("-created_at",)

    def mark_processed(self) -> None:
        if self.processed_at:
            return
        self.processed_at = timezone.now()
        self.save(update_fields=["processed_at", "updated_at"])
