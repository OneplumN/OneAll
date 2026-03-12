#!/usr/bin/env python3
"""资产信息 · IPMP 项目同步脚本.

脚本内直接填写接口与凭证配置，按需修改后运行即可。
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import requests


# ---- 固定配置：按需修改 ----
API_BASE_URL = "https://bk.tencent.com/docs/markdown/ZH/CMDB/3.10/APIDocs/cc/zh-hans/search_business.md"
APP_CODE = "cc-portal"
APP_SECRET = "73123127-f87a-4644-b70c-beb8sedsgw77dd"
USERNAME = "w-lih"
BK_TOKEN = ""
BK_OBJ_ID = "biz"
PAGE_LIMIT = 500
TIMEOUT = 30
FIELDS = [
    "sys_no",
    "bk_biz_name",
    "sys_shrt_eng_nm",
    "st",
    "satrp_ldrId",
    "inf_lv1",
    "bsn_knd",
]
# --------------------------------

ASSET_SOURCE = "IPMP"
ASSET_TYPE = "ipmp-project"

SYSTEM_ORIGIN_MAP = {
    "citicf": "中信期货",
    "citicgt": "寰球商贸",
    "citicfi": "信期国际",
    "citicyam": "盈时资管",
    "citics": "中信证券",
    "citicsc": "中证资本",
    "acct_term": "账号终端",
}
SYSTEM_ORIGIN_DEFAULT = SYSTEM_ORIGIN_MAP["citicf"]

SECURITY_LEVEL_MAP = {
    None: "未定级",
    "": "未定级",
    "0": "未定级",
    "1": "等保一级",
    "2": "等保二级",
    "3": "等保三级",
    "4": "等保四级",
    "5": "等保五级",
}

DEFAULT_OUTPUT = os.getenv(
    "ASSET_SYNC_IPMP_FILE",
    os.path.join("backend", "src", "integrations", "assets_sync", "samples", "ipmp_projects.json"),
)

logger = logging.getLogger("ipmp_sync")


def build_headers() -> Dict[str, str]:
    auth_payload = {
        "bk_app_code": APP_CODE,
        "bk_app_secret": APP_SECRET,
        "bk_username": USERNAME,
    }
    if BK_TOKEN:
        auth_payload["bk_token"] = BK_TOKEN
    return {
        "Content-Type": "application/json",
        "X-Bkapi-Authorization": json.dumps(auth_payload, ensure_ascii=False),
    }


def fetch_businesses() -> List[Dict[str, Any]]:
    endpoint = API_BASE_URL.rstrip("/")
    headers = build_headers()
    session = requests.Session()
    start = 0
    records: List[Dict[str, Any]] = []

    while True:
        payload = {
            "bk_obj_id": BK_OBJ_ID,
            "page": {"start": start, "limit": PAGE_LIMIT},
            "fields": FIELDS,
        }
        logger.info("请求业务数据: start=%s limit=%s", start, PAGE_LIMIT)
        response = session.post(endpoint, json=payload, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if not data.get("result"):
            raise RuntimeError(f"蓝鲸接口调用失败: {data.get('message') or data}")
        info = data.get("data", {}).get("info", [])
        records.extend(info)
        if len(info) < PAGE_LIMIT:
            break
        start += PAGE_LIMIT
    return records


def normalize_system_origin(value: Any) -> str:
    if value is None or value == "":
        return SYSTEM_ORIGIN_DEFAULT
    key = str(value).strip().lower()
    return SYSTEM_ORIGIN_MAP.get(key, str(value))


def normalize_security_level(value: Any) -> str:
    key = str(value).strip().lower() if value is not None else ""
    return SECURITY_LEVEL_MAP.get(key, "未定级")


def build_asset_record(entry: Dict[str, Any]) -> Dict[str, Any]:
    app_code = (entry.get("sys_no") or "").strip()
    app_name_cn = (entry.get("bk_biz_name") or app_code or "未命名项目").strip()
    owner = (entry.get("satrp_ldrId") or "").strip()
    record = {
        "source": ASSET_SOURCE,
        "external_id": app_code or f"bk_biz_{entry.get('bk_biz_id')}",
        "name": app_name_cn or app_code or "未命名项目",
        "system_name": app_name_cn,
        "status": "synced",
        "owners": [owner] if owner else [],
        "metadata": {
            "asset_type": ASSET_TYPE,
            "app_code": app_code,
            "app_name_cn": app_name_cn,
            "app_name_en": (entry.get("sys_shrt_eng_nm") or "").strip(),
            "app_status": (entry.get("st") or "").strip(),
            "owner": owner,
            "security_level": normalize_security_level(entry.get("inf_lv1")),
            "system_origin": normalize_system_origin(entry.get("bsn_knd")),
        },
    }
    return record


def write_output(records: List[Dict[str, Any]], output_path: str = DEFAULT_OUTPUT) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)
    logger.info("已写入 %s 条记录 -> %s", len(records), path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    logger.info("开始同步 IPMP 项目，目标输出 %s", DEFAULT_OUTPUT)
    businesses = fetch_businesses()
    logger.info("共拉取 %s 条业务记录", len(businesses))
    records = [build_asset_record(item) for item in businesses]
    write_output(records)


if __name__ == "__main__":
    main()
