from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class AssetSource(BaseModel):
    """标识外部资产源（如 Zabbix、IPMP、工单系统等），并存储访问配置与同步策略。

    v2 中只提供模型与基础字段，具体同步逻辑与配置表单后续按需扩展。
    """

    class Type(models.TextChoices):
        CMDB = "cmdb", "CMDB"
        MONITORING = "monitoring", "监控平台"
        ITSM = "itsm", "工单/ITSM"
        OTHER = "other", "其他"

    # 稳定的唯一标识，用于代码和配置中引用（例如 'zabbix', 'ipmp', 'workorder-host'）
    key = models.CharField(max_length=64, unique=True)
    # 展示名称，例如「Zabbix 主机资产」「IPMP 项目资产」
    name = models.CharField(max_length=128)
    type = models.CharField(max_length=32, choices=Type.choices, default=Type.OTHER)
    is_enabled = models.BooleanField(default=False)
    # 连接与同步策略相关配置，具体结构由各 Source 自行约定
    config = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "assets_asset_source"
        ordering = ("key",)
        verbose_name = "Asset Source"
        verbose_name_plural = "Asset Sources"

    def __str__(self) -> str:
        return f"{self.key} ({self.name})"

