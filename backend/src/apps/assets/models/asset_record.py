from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models.base import BaseModel


class AssetRecord(BaseModel):
    class Source(models.TextChoices):
        CMDB = "CMDB", "CMDB"
        ZABBIX = "Zabbix", "Zabbix"
        PROMETHEUS = "Prometheus", "Prometheus"
        IPMP = "IPMP", "IPMP"
        MANUAL = "Manual", "Manual"

    source = models.CharField(max_length=32, choices=Source.choices)
    external_id = models.CharField(max_length=128)
    name = models.CharField(max_length=256)
    system_name = models.CharField(max_length=128, blank=True)
    owners = models.JSONField(default=list, blank=True)
    contacts = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    synced_at = models.DateTimeField(auto_now=True)
    sync_status = models.CharField(max_length=32, default="unknown")
    is_removed = models.BooleanField(default=False)
    removed_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "assets_asset_record"
        ordering = ("-synced_at",)
        verbose_name = "Asset Record"
        verbose_name_plural = "Asset Records"
        unique_together = ("source", "external_id")

    def mark_synced(self, status: str, metadata: dict | None = None) -> None:
        self.sync_status = status
        if metadata:
            self.metadata.update(metadata)
        self.is_removed = False
        self.removed_at = None
        self.last_seen_at = timezone.now()
        self.save(update_fields=["sync_status", "metadata", "is_removed", "removed_at", "last_seen_at", "updated_at"])
