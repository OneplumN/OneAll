from __future__ import annotations

from typing import Any, Dict, List

from ..utils import load_records_from_env


ENV_VAR = "ASSET_SYNC_CMDB_FILE"


def fetch_cmdb_domains() -> List[Dict[str, Any]]:
    sample = [
        {
            "source": "CMDB",
            "external_id": "domain:oneall.cn",
            "name": "oneall.cn",
            "system_name": "OneAll 平台",
            "owners": ["张三"],
            "contacts": ["000123"],
            "status": "synced",
            "metadata": {
                "asset_type": "cmdb-domain",
                "domain": "oneall.cn",
                "network_type": "internet",
                "owner": "张三",
                "alert_contacts": ["000123"],
            },
        },
        {
            "source": "CMDB",
            "external_id": "domain:internal.oneall",
            "name": "internal.oneall",
            "system_name": "内部调度系统",
            "owners": ["李四"],
            "contacts": ["000234", "000235"],
            "status": "synced",
            "metadata": {
                "asset_type": "cmdb-domain",
                "domain": "internal.oneall",
                "network_type": "internal",
                "owner": "李四",
                "alert_contacts": ["000234", "000235"],
            },
        },
    ]
    return load_records_from_env(ENV_VAR, sample, 'cmdb_domains.json')
