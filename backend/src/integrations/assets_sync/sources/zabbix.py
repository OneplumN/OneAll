from __future__ import annotations

from typing import Any, Dict, List

from ..utils import load_records_from_env

ENV_VAR = "ASSET_SYNC_ZABBIX_FILE"


def fetch_zabbix_hosts() -> List[Dict[str, Any]]:
    # 生产环境要求显式提供主机清单，避免未配置时把 demo 主机写入资产库。
    return load_records_from_env(ENV_VAR, [], None)
