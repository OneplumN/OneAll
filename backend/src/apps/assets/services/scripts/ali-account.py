"""
阿里云账号资产同步脚本

当前脚本提供一个可直接改造的 HTTP JSON 同步骨架：
1. 配置 API_URL / 请求头后可直接拉取外部接口。
2. 如需对接其他来源，可直接替换 fetch_source_rows() 中的逻辑。
3. 未完成配置时会明确报错，避免将示例数据写入正式资产库。
"""

from typing import Any, Dict, List

import requests


API_URL = ""
REQUEST_HEADERS: Dict[str, str] = {
    # "Authorization": "Bearer <token>",
}
REQUEST_TIMEOUT_SECONDS = 15
VERIFY_TLS = True
SOURCE_NAME = "Manual"


def fetch_source_rows() -> List[Dict[str, Any]]:
    if not API_URL.strip():
        raise ValueError("ali-account 脚本尚未配置真实数据源，请先填写 API_URL 或改写 fetch_source_rows()")

    response = requests.get(
        API_URL,
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT_SECONDS,
        verify=VERIFY_TLS,
    )
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("items") or payload.get("data") or payload.get("rows") or payload.get("results") or []
    else:
        raise ValueError(f"ali-account 源接口返回值类型不支持：{type(payload).__name__}")

    if not isinstance(rows, list):
        raise ValueError("ali-account 源接口未解析出列表数据，请检查 fetch_source_rows()")
    return rows


def map_row(raw: Dict[str, Any], asset_type: str) -> Dict[str, Any]:
    external_id = str(raw.get("acc_id") or raw.get("id") or "").strip()
    if not external_id:
        raise ValueError("ali-account 存在缺少 acc_id 的记录，请检查字段映射")

    return {
        "asset_type": asset_type,
        "source": SOURCE_NAME,
        "external_id": external_id,
        "metadata": {
            "acc_id": raw.get("acc_id", ""),
            "acc_owner": raw.get("acc_owner", ""),
            "acc_ip": raw.get("acc_ip", ""),
        },
    }


def run(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    asset_type = str(context.get("asset_type") or "ali-account")
    raw_rows = fetch_source_rows()
    return [map_row(row, asset_type) for row in raw_rows]
