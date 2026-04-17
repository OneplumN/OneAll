from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence


@dataclass(frozen=True, slots=True)
class AssetTypeDefinition:
    """定义单一资产类型的元数据。

    注意：这里不直接依赖 Django 模型，避免在应用加载/迁移阶段引入循环引用，
    source 使用字符串形式（例如 'CMDB' / 'Zabbix'）。

    fields 用于描述该资产类型在 metadata 中常见的业务字段集合，
    unique_fields 则是在这些字段中用于构成业务唯一键的子集。
    """

    key: str
    label: str
    category: str
    default_source: str
    unique_fields: List[str]
    fields: List[str]

    def all_fields(self) -> List[str]:
        """返回该资产类型的字段集合（目前直接等同于 fields）。"""

        return list(self.fields)


ASSET_TYPES: Dict[str, AssetTypeDefinition] = {
    # CMDB 域名资产
    "cmdb-domain": AssetTypeDefinition(
        key="cmdb-domain",
        label="CMDB 域名",
        category="domain",
        default_source="CMDB",
        unique_fields=["domain"],
        # 与前端资产中心 CMDB 域名模型字段保持一致
        fields=["domain", "system_name", "network_type", "owner", "alert_contacts"],
    ),
    # Zabbix 主机资产
    "zabbix-host": AssetTypeDefinition(
        key="zabbix-host",
        label="Zabbix 主机",
        category="host",
        default_source="Zabbix",
        unique_fields=["ip", "host_name"],  # 优先 IP，缺失时回退 host_name
        # 与前端资产中心 Zabbix 主机模型字段保持一致
        fields=[
            "ip",
            "host_name",
            "visible_name",
            "host_group",
            "proxy",
            "interface_type",
            "interface_available",
        ],
    ),
    # IPMP 应用项目
    "ipmp-project": AssetTypeDefinition(
        key="ipmp-project",
        label="IPMP 项目",
        category="application",
        default_source="IPMP",
        unique_fields=["app_code"],
        # 与前端资产中心 IPMP 项目模型字段保持一致
        fields=[
            "app_code",
            "app_name_cn",
            "app_name_en",
            "app_status",
            "owner",
            "security_level",
            "system_origin",
        ],
    ),
    # 工单导入的主机资产
    "workorder-host": AssetTypeDefinition(
        key="workorder-host",
        label="工单纳管主机",
        category="host",
        default_source="Manual",
        unique_fields=["ip"],
        # 与前端资产中心工单纳管主机模型字段保持一致
        fields=[
            "ip",
            "online_status",
            "idc",
            "proxy",
            "port",
            "alert_contacts",
            "hostname",
            "app_system",
            "owner",
        ],
    ),
}


def list_asset_types() -> List[AssetTypeDefinition]:
    """按 key 排序返回所有资产类型定义。"""

    return [ASSET_TYPES[key] for key in sorted(ASSET_TYPES.keys())]


def get_asset_type(key: str) -> AssetTypeDefinition | None:
    return ASSET_TYPES.get(key)
