from __future__ import annotations

from typing import Any, Dict, List

from ..utils import load_records_from_env

ENV_VAR = "ASSET_SYNC_IPMP_FILE"


def fetch_ipmp_projects() -> List[Dict[str, Any]]:
    # 生产环境使用真实台账/接口数据，不默认回退内置样例，避免误将示例项目写入资产库。
    return load_records_from_env(ENV_VAR, [], None)
