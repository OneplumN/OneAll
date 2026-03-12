from __future__ import annotations

from typing import Any, Dict, List

from ..utils import load_records_from_env

ENV_VAR = "ASSET_SYNC_ZABBIX_FILE"


def fetch_zabbix_hosts() -> List[Dict[str, Any]]:
    sample = [
        {
            "source": "Zabbix",
            "external_id": "zbx:redis-master",
            "name": "Redis 主节点",
            "system_name": "缓存平台",
            "status": "synced",
            "metadata": {
                "asset_type": "zabbix-host",
                "host_status": "0",
                "host_status_label": "启用",
                "status": "0",
                "ip": "10.10.1.21",
                "host_name": "redis-master",
                "host_groups": ["cache", "production"],
                "proxy": "beijing-proxy",
                "interface_type": "1",
                "interface_type_label": "Agent",
                "interface_available": "1",
                "interface_available_label": "可用",
                "primary_interface": {
                    "ip": "10.10.1.21",
                    "port": "10050",
                    "type": "1",
                    "type_label": "Agent",
                    "available": "1",
                    "available_label": "可用",
                },
                "interfaces": [
                    {
                        "ip": "10.10.1.21",
                        "type": "1",
                        "available": "1",
                        "port": "10050",
                    }
                ],
            },
        },
        {
            "source": "Zabbix",
            "external_id": "zbx:web-node-01",
            "name": "Web Node 01",
            "system_name": "门户系统",
            "status": "disabled",
            "metadata": {
                "asset_type": "zabbix-host",
                "host_status": "1",
                "host_status_label": "停用",
                "status": "1",
                "ip": "10.20.5.11",
                "host_name": "web-node-01",
                "host_groups": ["web", "blue-team"],
                "proxy": "shanghai-proxy",
                "interface_type": "1",
                "interface_type_label": "Agent",
                "interface_available": "2",
                "interface_available_label": "不可用",
                "primary_interface": {
                    "ip": "10.20.5.11",
                    "port": "10050",
                    "type": "1",
                    "type_label": "Agent",
                    "available": "2",
                    "available_label": "不可用",
                },
                "interfaces": [
                    {
                        "ip": "10.20.5.11",
                        "type": "1",
                        "available": "2",
                        "port": "10050",
                    }
                ],
            },
        },
    ]
    return load_records_from_env(ENV_VAR, sample, 'zabbix_hosts.json')
