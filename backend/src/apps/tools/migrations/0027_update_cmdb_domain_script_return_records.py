from __future__ import annotations

from django.db import migrations
from django.utils import timezone


SCRIPT_NAME = "资产信息 · 域名同步"

SCRIPT_BODY = """\"\"\"资产信息 · 域名同步脚本（直接返回 records 并由平台入库）。

说明：
- 平台会调用 main(CONFIG) 并读取其返回值（List[dict]）做入库与全量对账（软删除）。
- 不要写 `if __name__ == "__main__": main()`，平台执行器会额外调用一次 main()，避免重复执行。
- 你可以在脚本里直接请求 CMDB API 并做字段映射，最终返回标准 records。

标准 record（最小字段）：
{
  "source": "CMDB",
  "external_id": "domain:example.com",
  "name": "example.com",
  "system_name": "业务系统",
  "status": "synced",
  "owners": ["张三"],
  "contacts": ["000123"],
  "metadata": {
    "asset_type": "cmdb-domain",
    "domain": "example.com",
    "network_type": "internet",
    "owner": "张三",
    "alert_contacts": ["000123"]
  }
}
\"\"\"

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests


def _get_system_cmdb_config() -> Dict[str, Any]:
    # 可选：从系统设置读取 integrations.cmdb（避免把 token 明文写进脚本）
    try:
        from apps.settings.models import SystemSettings  # type: ignore
    except Exception:
        return {}
    settings = SystemSettings.objects.order_by("-updated_at").first()
    if not settings:
        return {}
    integrations = getattr(settings, "integrations", None) or {}
    cmdb = integrations.get("cmdb") if isinstance(integrations, dict) else {}
    return cmdb if isinstance(cmdb, dict) else {}


def _pick(config: Dict[str, Any], key: str, envs: List[str], default: Any = None):
    if config.get(key):
        return config[key]
    for env_key in envs:
        val = os.getenv(env_key)
        if val:
            return val
    return default


def _normalize_domain_record(item: Any) -> Dict[str, Any]:
    if isinstance(item, str):
        domain = item.strip()
        system_name = ""
        network_type = "internet"
        owner = ""
        alert_contacts: List[str] = []
    elif isinstance(item, dict):
        domain = str(item.get("domain") or item.get("name") or "").strip()
        system_name = str(item.get("system_name") or item.get("system") or "").strip()
        network_type = str(item.get("network_type") or item.get("network") or "internet").strip()
        owner = str(item.get("owner") or item.get("owner_name") or "").strip()
        alert_contacts = item.get("alert_contacts") or item.get("contacts") or []
        if isinstance(alert_contacts, str):
            alert_contacts = [x.strip() for x in alert_contacts.split(",") if x.strip()]
        if not isinstance(alert_contacts, list):
            alert_contacts = []
        alert_contacts = [str(x).strip() for x in alert_contacts if str(x).strip()]
    else:
        raise RuntimeError(f"Unsupported domain record: {type(item)}")

    if not domain:
        raise RuntimeError("domain 不能为空")

    owners = [owner] if owner else []
    contacts = list(alert_contacts)
    return {
        "source": "CMDB",
        "external_id": f"domain:{domain}",
        "name": domain,
        "system_name": system_name,
        "status": "synced",
        "owners": owners,
        "contacts": contacts,
        "metadata": {
            "asset_type": "cmdb-domain",
            "domain": domain,
            "system_name": system_name,
            "network_type": network_type,
            "owner": owner,
            "alert_contacts": alert_contacts,
        },
    }


def fetch_domains_from_api(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    # 约定：CMDB endpoint 返回：
    # - list（每项可以是 str 或 dict），或
    # - dict，包含 records/items 字段（list）
    cmdb_cfg = _get_system_cmdb_config()
    endpoint = _pick(config, "endpoint", ["CMDB_API_ENDPOINT"], cmdb_cfg.get("endpoint") if cmdb_cfg else "")
    token = _pick(config, "token", ["CMDB_API_TOKEN"], cmdb_cfg.get("token") if cmdb_cfg else "")
    if not endpoint:
        raise RuntimeError("未配置 CMDB endpoint（系统设置-全局设置 integrations.cmdb.endpoint 或环境变量 CMDB_API_ENDPOINT）")
    timeout = int(_pick(config, "timeout", ["CMDB_API_TIMEOUT"], 20))

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(str(endpoint).rstrip("/"), headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("records") or data.get("items") or []
    else:
        items = []

    if not isinstance(items, list):
        raise RuntimeError("CMDB 接口返回格式不正确：records/items 不是 list")

    records: List[Dict[str, Any]] = []
    for item in items:
        records.append(_normalize_domain_record(item))
    return records


def main(config=None):
    cfg = config or globals().get("CONFIG", {}) or {}
    records = fetch_domains_from_api(cfg)
    print(f"[CMDB] 拉取完成，共 {len(records)} 条域名，将由平台入库。")
    globals()["RESULT"] = records
    return records
"""


def update_script(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")

    repo = CodeRepository.objects.filter(name=SCRIPT_NAME).first()
    if not repo:
        return

    version = CodeRepositoryVersion.objects.create(
        repository=repo,
        version=timezone.now().strftime("cmdb-domain-%Y%m%d%H%M%S%f"),
        summary="域名脚本直接返回 records",
        change_log="不再依赖写入 JSON 临时文件；脚本返回 records，由平台在脚本执行成功后自动入库，并做全量对账软删除。",
        content=SCRIPT_BODY,
    )
    repo.content = SCRIPT_BODY
    repo.latest_version = version
    repo.save(update_fields=["content", "latest_version", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0026_update_ipmp_assets_script_return_records"),
    ]

    operations = [
        migrations.RunPython(update_script, migrations.RunPython.noop),
    ]
