from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import requests

from ..utils import load_records_from_env

ENV_VAR = "ASSET_SYNC_ZABBIX_FILE"
logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {"Content-Type": "application/json-rpc"}
HOST_STATUS_LABELS = {"0": "启用", "1": "停用"}
INTERFACE_TYPE_LABELS = {
    "1": "Agent",
    "2": "SNMP",
    "3": "IPMI",
    "4": "JMX",
}
INTERFACE_AVAILABILITY_LABELS = {
    "0": "未知",
    "1": "可用",
    "2": "不可用",
}


def fetch_zabbix_hosts() -> List[Dict[str, Any]]:
    api_context = _resolve_api_context()
    if api_context:
        try:
            return _fetch_zabbix_hosts_from_api(api_context)
        except Exception as exc:  # pragma: no cover - graceful degradation path
            logger.warning("Failed to fetch Zabbix hosts from API, falling back to file mode: %s", exc)

    # 生产环境要求显式提供主机清单，避免未配置时把 demo 主机写入资产库。
    return load_records_from_env(ENV_VAR, [], None)


def _resolve_api_context() -> Dict[str, Any] | None:
    url = _pick_env("ASSET_SYNC_ZABBIX_URL", "ZABBIX_API_URL")
    token = _pick_env("ASSET_SYNC_ZABBIX_TOKEN", "ZABBIX_API_TOKEN")
    if not url or not token:
        return None

    timeout_raw = _pick_env("ASSET_SYNC_ZABBIX_TIMEOUT", "ZABBIX_API_TIMEOUT")
    verify_raw = _pick_env("ASSET_SYNC_ZABBIX_VERIFY", "ZABBIX_VERIFY_TLS")
    timeout = int(timeout_raw or 15)
    verify = str(verify_raw or "true").lower() not in {"0", "false", "no"}
    return {
        "url": url.rstrip("/"),
        "token": token,
        "timeout": timeout,
        "verify": verify,
    }


def _pick_env(*names: str) -> str:
    for name in names:
        value = str(os.getenv(name) or "").strip()
        if value:
            return value
    return ""


def _fetch_zabbix_hosts_from_api(ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    params = {
        "output": [
            "hostid",
            "host",
            "name",
            "description",
            "status",
            "available",
            "maintenanceid",
            "maintenance_status",
            "proxy_hostid",
        ],
        "selectGroups": ["name"],
        "selectInterfaces": ["interfaceid", "ip", "available", "type", "port", "dns", "useip"],
    }
    hosts = _call_zabbix(ctx, "host.get", params)
    return [_transform_host(item) for item in hosts]


def _call_zabbix(ctx: Dict[str, Any], method: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1,
        "auth": ctx["token"],
    }
    response = requests.post(
        ctx["url"],
        json=payload,
        timeout=ctx["timeout"],
        verify=ctx["verify"],
        headers=DEFAULT_HEADERS,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"Zabbix API error: {err.get('message')} - {err.get('data')}")
    result = data.get("result") or []
    return result if isinstance(result, list) else []


def _interface_label(value: Any, mapping: Dict[str, str], default: str = "未知") -> str:
    if value is None:
        return default
    return mapping.get(str(value), default)


def _transform_host(host: Dict[str, Any]) -> Dict[str, Any]:
    host_id = host.get("hostid") or host.get("host") or host.get("name") or "unknown"
    technical_name = str(host.get("host") or "").strip()
    visible_name = str(host.get("name") or "").strip()
    host_name = technical_name or visible_name or f"host-{host_id}"
    display_name = visible_name or host_name

    groups = [
        group.get("name")
        for group in host.get("groups", [])
        if isinstance(group, dict) and group.get("name")
    ]

    interfaces = host.get("interfaces") or []
    primary_interface = {}
    ip_address = ""
    for interface in interfaces:
        ip = interface.get("ip")
        if ip:
            ip_address = ip
            primary_interface = interface
            break
    if not primary_interface and interfaces:
        primary_interface = interfaces[0]
        ip_address = primary_interface.get("ip") or ""

    interface_type = primary_interface.get("type") if isinstance(primary_interface, dict) else None
    interface_available = primary_interface.get("available") if isinstance(primary_interface, dict) else None
    host_status = host.get("status")
    host_status_text = "" if host_status is None else str(host_status)

    metadata = {
        "asset_type": "zabbix-host",
        "host_id": host.get("hostid"),
        "host_name": host_name,
        "visible_name": visible_name,
        "host_groups": groups,
        "ip": ip_address,
        "interfaces": interfaces,
        "primary_interface": {
            "ip": primary_interface.get("ip") if isinstance(primary_interface, dict) else "",
            "port": primary_interface.get("port") if isinstance(primary_interface, dict) else "",
            "type": interface_type,
            "type_label": _interface_label(interface_type, INTERFACE_TYPE_LABELS),
            "available": interface_available,
            "available_label": _interface_label(interface_available, INTERFACE_AVAILABILITY_LABELS),
        },
        "interface_type": interface_type,
        "interface_type_label": _interface_label(interface_type, INTERFACE_TYPE_LABELS),
        "interface_available": interface_available,
        "interface_available_label": _interface_label(interface_available, INTERFACE_AVAILABILITY_LABELS),
        "proxy_hostid": host.get("proxy_hostid"),
        "status": host_status,
        "host_status": host_status_text,
        "host_status_label": HOST_STATUS_LABELS.get(host_status_text, "未知"),
        "available": host.get("available"),
        "maintenanceid": host.get("maintenanceid"),
        "maintenance_status": host.get("maintenance_status"),
    }

    status_label = "synced" if host_status_text == "0" else "disabled"
    return {
        "source": "Zabbix",
        "external_id": f"zbx:{host_id}",
        "name": display_name,
        "system_name": host.get("description") or "",
        "status": status_label,
        "metadata": metadata,
    }
