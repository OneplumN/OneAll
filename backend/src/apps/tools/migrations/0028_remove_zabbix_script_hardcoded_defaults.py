from __future__ import annotations

import re

from django.db import migrations
from django.utils import timezone


SCRIPT_NAME = "资产信息 · Zabbix 主机"

SCRIPT_BODY = """\"\"\"资产信息 · Zabbix 主机同步脚本（直接返回记录并由平台入库）。\"\"\"

import os
from typing import Any, Dict, List

import requests

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


def _resolve_config(config: Dict[str, Any]) -> Dict[str, Any]:
    def pick(key: str, envs: List[str], default: Any = None):
        if config.get(key):
            return config[key]
        for env_key in envs:
            val = os.getenv(env_key)
            if val:
                return val
        return default

    url = pick("zabbix_url", ["ASSET_SYNC_ZABBIX_URL", "ZABBIX_API_URL"], "")
    token = pick("zabbix_token", ["ASSET_SYNC_ZABBIX_TOKEN", "ZABBIX_API_TOKEN"], "")
    if not url or not token:
        raise RuntimeError("缺少 Zabbix API URL 或 Token，请显式配置后再执行。")
    timeout = int(pick("zabbix_timeout", ["ASSET_SYNC_ZABBIX_TIMEOUT", "ZABBIX_API_TIMEOUT"], 15))
    verify = pick("zabbix_verify", ["ASSET_SYNC_ZABBIX_VERIFY", "ZABBIX_VERIFY_TLS"], "true")
    verify = str(verify).lower() not in {"0", "false", "no"}
    return {"url": str(url).rstrip("/"), "token": token, "timeout": timeout, "verify": verify}


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


def sync_zabbix_hosts(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    ctx = _resolve_config(config)
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
        ],
        "selectGroups": ["name"],
        "selectInterfaces": ["interfaceid", "ip", "available", "type", "port", "dns", "useip"],
    }
    hosts = _call_zabbix(ctx, "host.get", params)
    records = [_transform_host(item) for item in hosts]
    print(f"[Zabbix] 拉取完成，共 {len(records)} 条主机，将由平台入库。")
    return records


def main(config=None):
    cfg = config or globals().get("CONFIG", {}) or {}
    records = sync_zabbix_hosts(cfg)
    globals()["RESULT"] = records
    return records
"""


def _sanitize_content(content: str) -> str:
    sanitized = content or ""
    sanitized = re.sub(r'DEFAULT_ZABBIX_URL = ".*?"', 'DEFAULT_ZABBIX_URL = ""', sanitized)
    sanitized = re.sub(r'DEFAULT_ZABBIX_TOKEN = ".*?"', 'DEFAULT_ZABBIX_TOKEN = ""', sanitized)
    sanitized = re.sub(r"^\s*URL:\s*.+$\n?", "", sanitized, flags=re.MULTILINE)
    sanitized = re.sub(r"^\s*TOKEN:\s*.+$\n?", "", sanitized, flags=re.MULTILINE)
    sanitized = re.sub(r"资产信息 · Zabbix 主机同步脚本（内置默认 API 参数）。", "资产信息 · Zabbix 主机同步脚本（要求显式配置 API 参数）。", sanitized)
    sanitized = re.sub(r"若 CONFIG / 环境变量未提供 zabbix_url、zabbix_token，则使用脚本内置默认值：", "请通过 CONFIG / 环境变量显式提供 zabbix_url、zabbix_token。", sanitized)
    sanitized = sanitized.replace("缺少 Zabbix API URL 或 Token，无法同步主机。", "缺少 Zabbix API URL 或 Token，请显式配置后再执行。")
    return sanitized


def update_script(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")
    ToolDefinition = apps.get_model("tools", "ToolDefinition")
    ScriptVersion = apps.get_model("tools", "ScriptVersion")

    repo = CodeRepository.objects.filter(name=SCRIPT_NAME).first()
    if not repo:
        return

    for version in CodeRepositoryVersion.objects.filter(repository=repo):
        sanitized_content = _sanitize_content(version.content)
        if sanitized_content != version.content:
            version.content = sanitized_content
            version.save(update_fields=["content", "updated_at"])

    if repo.content:
        repo.content = _sanitize_content(repo.content)
        repo.save(update_fields=["content", "updated_at"])

    repo_id = str(repo.id)
    tool_ids = list(
        ToolDefinition.objects.filter(metadata__repository_id=repo_id).values_list("id", flat=True)
    )
    script_version_ids = set(
        ScriptVersion.objects.filter(metadata__repository_id=repo_id).values_list("id", flat=True)
    )
    if tool_ids:
        script_version_ids.update(
            ScriptVersion.objects.filter(tool_id__in=tool_ids).values_list("id", flat=True)
        )
    for script_version in ScriptVersion.objects.filter(id__in=script_version_ids):
        sanitized_content = _sanitize_content(script_version.content)
        if sanitized_content != script_version.content:
            script_version.content = sanitized_content
            script_version.save(update_fields=["content", "updated_at"])

    version = CodeRepositoryVersion.objects.create(
        repository=repo,
        version=timezone.now().strftime("zbx-sync-sanitized-%Y%m%d%H%M%S"),
        summary="移除 Zabbix 默认地址与默认 Token",
        change_log="要求通过 CONFIG 或环境变量显式提供 Zabbix API URL/Token，并清洗历史版本中的硬编码默认值。",
        content=SCRIPT_BODY,
    )
    repo.content = SCRIPT_BODY
    repo.latest_version = version
    repo.save(update_fields=["content", "latest_version", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0027_update_cmdb_domain_script_return_records"),
    ]

    operations = [
        migrations.RunPython(update_script, migrations.RunPython.noop),
    ]
