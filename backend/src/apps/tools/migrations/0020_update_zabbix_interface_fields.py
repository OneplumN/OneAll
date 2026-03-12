from __future__ import annotations

from django.db import migrations
from django.utils import timezone

SCRIPT_BODY = """\"\"\"资产信息 · Zabbix 主机同步脚本（扩展接口类型/可用性字段）。\"\"\"

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests

DEFAULT_ZABBIX_URL = "http://101.43.54.131/api_jsonrpc.php"
DEFAULT_ZABBIX_TOKEN = "90c8d1eef412c9ac00b233675f5ed6b86530659db5ae025bb713b75da63a387a"
DEFAULT_HEADERS = {"Content-Type": "application/json-rpc"}
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


def _resolve_config(config: Dict[str, Any]) -> Dict[str, Any]:
    def pick(key: str, envs: List[str], default: Any = None):
        if config.get(key):
            return config[key]
        for env_key in envs:
            val = os.getenv(env_key)
            if val:
                return val
        return default

    url = pick("zabbix_url", ["ASSET_SYNC_ZABBIX_URL", "ZABBIX_API_URL"], DEFAULT_ZABBIX_URL)
    token = pick("zabbix_token", ["ASSET_SYNC_ZABBIX_TOKEN", "ZABBIX_API_TOKEN"], DEFAULT_ZABBIX_TOKEN)
    if not url or not token:
        raise RuntimeError("缺少 Zabbix API URL 或 Token，无法同步主机。")
    timeout = int(pick("zabbix_timeout", ["ASSET_SYNC_ZABBIX_TIMEOUT", "ZABBIX_API_TIMEOUT"], 15))
    verify = pick("zabbix_verify", ["ASSET_SYNC_ZABBIX_VERIFY", "ZABBIX_VERIFY_TLS"], "true")
    verify = str(verify).lower() not in {"0", "false", "no"}
    output = pick("output_path", ["ASSET_SYNC_ZABBIX_FILE"], "./data/zabbix_hosts.json")
    return {"url": str(url).rstrip("/"), "token": token, "timeout": timeout, "verify": verify, "output": output}


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
    host_name = host.get("host") or host.get("name") or f"host-{host_id}"
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

    metadata = {
        "asset_type": "zabbix-host",
        "host_id": host.get("hostid"),
        "host_name": host_name,
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
        "status": host.get("status"),
        "available": host.get("available"),
        "maintenanceid": host.get("maintenanceid"),
        "maintenance_status": host.get("maintenance_status"),
    }
    status_label = "synced" if str(host.get("status")) == "0" else "disabled"
    return {
        "source": "Zabbix",
        "external_id": f"zbx:{host_id}",
        "name": host_name,
        "system_name": host.get("description") or "",
        "status": status_label,
        "metadata": metadata,
    }


def sync_zabbix_hosts(config: Dict[str, Any]) -> Path:
    ctx = _resolve_config(config)
    params = {
        "output": ["hostid", "host", "description", "status", "available", "maintenanceid", "maintenance_status"],
        "selectGroups": ["name"],
        "selectInterfaces": ["interfaceid", "ip", "available", "type", "port", "dns", "useip"],
    }
    hosts = _call_zabbix(ctx, "host.get", params)
    records = [_transform_host(item) for item in hosts]
    output_path = Path(str(ctx["output"])).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)
    print(f"[Zabbix] 同步完成，共写入 {len(records)} 条主机到 {output_path}")
    return output_path


def main(config=None):
    cfg = config or globals().get("CONFIG", {}) or {}
    sync_zabbix_hosts(cfg)
"""


def update_script(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")

    repo = CodeRepository.objects.filter(name="资产信息 · Zabbix 主机").first()
    if not repo:
        return

    version = CodeRepositoryVersion.objects.create(
        repository=repo,
        version=timezone.now().strftime("zabbix-sync-%Y%m%d%H%M"),
        summary="扩展接口类型与可用性字段",
        change_log="同步 Zabbix 主机时，记录接口类型/可用性标签，供前端展示。",
        content=SCRIPT_BODY,
    )
    repo.content = SCRIPT_BODY
    repo.latest_version = version
    repo.save(update_fields=["content", "latest_version", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0019_add_asset_script_labels"),
    ]

    operations = [
        migrations.RunPython(update_script, migrations.RunPython.noop),
    ]
