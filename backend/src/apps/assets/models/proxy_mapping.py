from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class ProxyMapping(BaseModel):
    """Zabbix Proxy 映射（英文编码 -> 中文展示名）."""

    proxy = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=256)
    remark = models.CharField(max_length=256, blank=True, default="")

    class Meta:
        db_table = "assets_proxy_mapping"
        ordering = ("-created_at",)
        verbose_name = "Proxy Mapping"
        verbose_name_plural = "Proxy Mappings"

    def __str__(self) -> str:
        return f"{self.proxy} -> {self.display_name}"
