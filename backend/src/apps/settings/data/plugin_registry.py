from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True, slots=True)
class PluginDefinition:
    key: str
    name: str
    builtin: bool = False


PLUGIN_DEFINITIONS: List[PluginDefinition] = [
    # Monitoring
    PluginDefinition(key="monitoring_overview", name="驾驶舱", builtin=True),
    # Detection tools
    PluginDefinition(key="tool_domain_probe", name="域名拨测", builtin=True),
    PluginDefinition(key="tool_certificate", name="证书检测", builtin=True),
    PluginDefinition(key="tool_cmdb_check", name="CMDB 域名检测", builtin=True),
    # Assets
    PluginDefinition(key="asset_cmdb_domain", name="域名", builtin=True),
    PluginDefinition(key="asset_zabbix_host", name="Zabbix 主机"),
    PluginDefinition(key="asset_ipmp_project", name="IPMP 项目"),
    PluginDefinition(key="asset_workorder_host", name="工单纳管主机信息"),
]
