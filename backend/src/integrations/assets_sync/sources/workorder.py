from __future__ import annotations

from typing import Any, Dict, List

from ..utils import load_records_from_env

ENV_VAR = "ASSET_SYNC_WORKORDER_FILE"


def fetch_workorder_hosts() -> List[Dict[str, Any]]:
    sample = [
        {
            "source": "Manual",
            "external_id": "workorder:10.30.1.5",
            "name": "payment-worker-01",
            "system_name": "支付调度",
            "status": "synced",
            "metadata": {
                "asset_type": "workorder-host",
                "ip": "10.30.1.5",
                "idc": "北京亦庄",
                "proxy": "itsi-bj-proxy",
                "port": 8080,
                "alert_contacts": ["001234"],
                "hostname": "payment-worker-01",
                "app_system": "支付调度",
                "owner": "陈七",
            },
        },
        {
            "source": "Manual",
            "external_id": "workorder:10.30.2.9",
            "name": "payment-worker-02",
            "system_name": "支付调度",
            "status": "synced",
            "metadata": {
                "asset_type": "workorder-host",
                "ip": "10.30.2.9",
                "idc": "上海张江",
                "proxy": "itsi-sh-proxy",
                "port": 8080,
                "alert_contacts": ["001235", "001236"],
                "hostname": "payment-worker-02",
                "app_system": "支付调度",
                "owner": "陈七",
            },
        },
    ]
    return load_records_from_env(ENV_VAR, sample, 'workorder_hosts.json')
