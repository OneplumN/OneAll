#!/usr/bin/env python3
"""资产信息 · Zabbix 主机导出脚本（用于仿测统计分析）.

用途：
1) 从 Zabbix API 拉取主机清单（含 Proxy / IP / 群组 / 可见名称 / 可用性）
2) 导出为本平台资产同步可直接读取的 JSON（list[record]）

默认输出：./data/zabbix_hosts.json
后端读取方式（两选一）：
- 设置环境变量：ASSET_SYNC_ZABBIX_FILE=./data/zabbix_hosts.json
- 或把文件放在仓库 data/ 目录（默认也会被尝试读取）

运行示例（推荐使用 API Token）：
ZABBIX_URL="https://zbx.example.com/api_jsonrpc.php" \
ZABBIX_TOKEN="******" \
python3 scripts/assets/export_zabbix_hosts.py --out ./data/zabbix_hosts.json

运行示例（账号密码登录）：
ZABBIX_URL="https://zbx.example.com/api_jsonrpc.php" \
ZABBIX_USER="Admin" \
ZABBIX_PASSWORD="******" \
python3 scripts/assets/export_zabbix_hosts.py --out ./data/zabbix_hosts.json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import requests


DEFAULT_OUT = "./data/zabbix_hosts.json"
DEFAULT_TIMEOUT = 30
DEFAULT_INTERFACE_TYPE = "1"  # 1=Agent

# ---- 固定配置：按需填写（也支持环境变量覆盖）----
# 推荐：仅填写 ZABBIX_URL + ZABBIX_TOKEN
ZABBIX_URL = ""  # 例如：https://zbx.example.com/api_jsonrpc.php
ZABBIX_TOKEN = ""  # 例如：xxxxxxxxxxxxxxxxxxxx
ZABBIX_USER = ""  # 可选：账号密码登录（不建议在脚本中长期存放）
ZABBIX_PASSWORD = ""  # 可选：账号密码登录
# -------------------------------------------

def _normalize_api_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if "api_jsonrpc.php" in url:
        return url
    if url.endswith("/"):
        return f"{url}api_jsonrpc.php"
    return f"{url}/api_jsonrpc.php"


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def zabbix_call(
    session: requests.Session,
    *,
    url: str,
    method: str,
    params: Mapping[str, Any],
    auth: Optional[str] = None,
    request_id: int = 1,
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:
    payload: Dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params, "id": request_id}
    if auth:
        payload["auth"] = auth
    resp = session.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    try:
        data = resp.json()
    except Exception:
        content_type = resp.headers.get("content-type", "")
        snippet = (resp.text or "")[:800]
        raise RuntimeError(
            "Zabbix API 返回不是 JSON，通常是 URL 写错或被网关重定向到登录页。\n"
            f"- method: {method}\n"
            f"- url: {resp.url}\n"
            f"- status: {resp.status_code}\n"
            f"- content-type: {content_type}\n"
            f"- body[:800]: {snippet}"
        )
    if "error" in data:
        raise RuntimeError(f"Zabbix API error: {data['error']}")
    return data.get("result")


def login(session: requests.Session, *, url: str, user: str, password: str, timeout: int) -> str:
    result = zabbix_call(
        session,
        url=url,
        method="user.login",
        params={"user": user, "password": password},
        timeout=timeout,
    )
    token = _safe_str(result)
    if not token:
        raise RuntimeError("Zabbix 登录失败：未返回 auth token")
    return token


def fetch_proxies(session: requests.Session, *, url: str, auth: str, timeout: int) -> Dict[str, str]:
    proxies = zabbix_call(
        session,
        url=url,
        method="proxy.get",
        auth=auth,
        params={"output": ["proxyid", "host", "name"]},
        timeout=timeout,
    ) or []
    mapping: Dict[str, str] = {}
    for proxy in proxies:
        proxyid = _safe_str(proxy.get("proxyid"))
        name = _safe_str(proxy.get("name") or proxy.get("host"))
        if proxyid and name:
            mapping[proxyid] = name
    return mapping


def _availability_label(value: Any) -> str:
    text = _safe_str(value)
    if text == "2":
        return "不可用"
    if text == "1":
        return "可用"
    return "未知"


def _pick_primary_interface(interfaces: List[Mapping[str, Any]]) -> Mapping[str, Any]:
    if not interfaces:
        return {}
    for item in interfaces:
        if _safe_str(item.get("main")) == "1":
            return item
    return interfaces[0]


def build_asset_record(
    *,
    host: Mapping[str, Any],
    proxy_map: Mapping[str, str],
    default_proxy_name: str,
) -> Dict[str, Any]:
    hostid = _safe_str(host.get("hostid"))
    host_name = _safe_str(host.get("host") or host.get("name"))
    visible_name = _safe_str(host.get("name") or host_name)

    groups = host.get("groups") or []
    group_names = [_safe_str(item.get("name")) for item in groups if isinstance(item, dict)]
    group_names = [name for name in group_names if name]

    interfaces = host.get("interfaces") or []
    if not isinstance(interfaces, list):
        interfaces = []
    primary = _pick_primary_interface([i for i in interfaces if isinstance(i, dict)])

    ip = _safe_str(primary.get("ip"))
    port = _safe_str(primary.get("port"))
    iface_type = _safe_str(primary.get("type")) or DEFAULT_INTERFACE_TYPE
    iface_available = _safe_str(primary.get("available"))
    iface_available_label = _availability_label(iface_available)

    proxyid = _safe_str(host.get("proxyid") or host.get("proxy_hostid"))
    proxy_name = _safe_str(proxy_map.get(proxyid)) or default_proxy_name

    # system_name：统计分析页按“IPMP 中文名-英文名”与主机群组对齐；这里先不强行赋值。
    return {
        "source": "Zabbix",
        "external_id": f"zbx:{hostid}" if hostid else f"zbx:{host_name}",
        "name": visible_name or host_name or hostid or "未命名主机",
        "system_name": "",
        "status": "synced",
        "metadata": {
            "asset_type": "zabbix-host",
            "ip": ip,
            "host_ip": ip,
            "host_name": host_name,
            "visible_name": visible_name,
            "host_groups": group_names,
            "proxy": proxy_name,
            "proxyid": proxyid,
            "interface_type": iface_type,
            "interface_type_label": "Agent" if iface_type == "1" else iface_type,
            "interface_available": iface_available,
            "interface_available_label": iface_available_label,
            "primary_interface": {
                "ip": ip,
                "port": port,
                "type": iface_type,
                "type_label": "Agent" if iface_type == "1" else iface_type,
                "available": iface_available,
                "available_label": iface_available_label,
            },
            "interfaces": [
                {
                    "ip": _safe_str(item.get("ip")),
                    "type": _safe_str(item.get("type")),
                    "available": _safe_str(item.get("available")),
                    "port": _safe_str(item.get("port")),
                    "main": _safe_str(item.get("main")),
                }
                for item in interfaces
                if isinstance(item, dict)
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=DEFAULT_OUT, help="输出 JSON 文件路径（默认 ./data/zabbix_hosts.json）")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="请求超时（秒）")
    parser.add_argument("--default-proxy", default="未分配", help="未绑定 proxy 的默认名称")
    parser.add_argument("--include-disabled", action="store_true", help="包含未监控主机（默认仅 status=0）")
    args = parser.parse_args()

    url = _normalize_api_url(os.getenv("ZABBIX_URL") or ZABBIX_URL)
    token = (os.getenv("ZABBIX_TOKEN") or ZABBIX_TOKEN).strip()
    user = (os.getenv("ZABBIX_USER") or ZABBIX_USER).strip()
    password = (os.getenv("ZABBIX_PASSWORD") or ZABBIX_PASSWORD).strip()
    if not url:
        raise SystemExit("请在脚本中填写 ZABBIX_URL，或设置环境变量 ZABBIX_URL")
    if not token and (not user or not password):
        raise SystemExit("请在脚本中填写 ZABBIX_TOKEN（推荐），或填写 ZABBIX_USER / ZABBIX_PASSWORD（或用环境变量覆盖）")

    session = requests.Session()
    auth = token or login(session, url=url, user=user, password=password, timeout=args.timeout)
    proxy_map = fetch_proxies(session, url=url, auth=auth, timeout=args.timeout)

    params: Dict[str, Any] = {
        "output": ["hostid", "host", "name", "proxyid", "proxy_hostid", "status", "flags"],
        "selectInterfaces": ["ip", "port", "type", "main", "available"],
        "selectGroups": ["name"],
    }
    if not args.include_disabled:
        params["filter"] = {"status": "0"}  # 0=monitored

    hosts = zabbix_call(session, url=url, method="host.get", auth=auth, params=params, timeout=args.timeout) or []

    records = [
        build_asset_record(host=item, proxy_map=proxy_map, default_proxy_name=args.default_proxy)
        for item in hosts
        if isinstance(item, dict)
    ]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已导出 {len(records)} 台主机 -> {out_path}")


if __name__ == "__main__":
    main()
