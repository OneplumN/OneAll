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
    # 广义资产类型，例如 domain / zabbix-host / ipmp-project / workorder-host 等
    asset_type = models.CharField(max_length=64, blank=True)
    # 业务唯一键的规范化表示，用于跨源/多次同步时避免重复
    canonical_key = models.CharField(max_length=256, blank=True)
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

    @property
    def resolved_asset_type(self) -> str:
        """Return a normalized asset_type for consumers.

        优先使用显式的 asset_type 字段；兼容旧数据时会回退到 metadata.asset_type，
        再退回到 source 名称，保证调用方总能拿到一个可用的资产类型 key。
        """

        if self.asset_type:
            return self.asset_type
        metadata_type = (self.metadata or {}).get("asset_type") or ""
        if metadata_type:
            return str(metadata_type)
        return str(self.source)

    def mark_synced(self, status: str, metadata: dict | None = None) -> None:
        self.sync_status = status
        if metadata:
            self.metadata.update(metadata)
        self.is_removed = False
        self.removed_at = None
        self.last_seen_at = timezone.now()
        self.save(update_fields=["sync_status", "metadata", "is_removed", "removed_at", "last_seen_at", "updated_at"])
