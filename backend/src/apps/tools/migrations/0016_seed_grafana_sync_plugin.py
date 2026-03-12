from __future__ import annotations

from django.db import migrations

GRAFANA_SCRIPT = '''"""Grafana 账号同步脚本：从 Zabbix 获取账号并同步到 Grafana"""
import os
import json
import requests

CONFIG = globals().get("CONFIG", {}) or {}

ZABBIX_URL = CONFIG.get("zabbix_url") or os.getenv("XXX_ZABBIX_URL")
ZABBIX_TOKEN = CONFIG.get("zabbix_token") or os.getenv("XXX_ZABBIX_TOKEN")
GRAFANA_URL = CONFIG.get("grafana_url") or os.getenv("XXX_GRAFANA_URL")
GRAFANA_TOKEN = CONFIG.get("grafana_token") or os.getenv("XXX_GRAFANA_TOKEN")


def zabbix_request(session: requests.Session, method: str, params: dict) -> dict:
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1, "auth": ZABBIX_TOKEN}
    resp = session.post(ZABBIX_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data["result"]


def grafana_request(session: requests.Session, method: str, path: str, payload: dict | None = None):
    headers = {"Authorization": f"Bearer {GRAFANA_TOKEN}", "Content-Type": "application/json"}
    url = f"{GRAFANA_URL.rstrip('/')}{path}"
    resp = session.request(method, url, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(resp.text)
    return resp.json()


def sync_accounts():
    if not (ZABBIX_URL and ZABBIX_TOKEN and GRAFANA_URL and GRAFANA_TOKEN):
        raise RuntimeError("请配置 Zabbix/Grafana URL 与 Token")

    session = requests.Session()
    session.mount(ZABBIX_URL, requests.adapters.HTTPAdapter(max_retries=3))
    users = zabbix_request(session, "user.get", {"output": ["username", "name", "surname", "alias"]})
    existing = {u.get("login"): u for u in grafana_request(session, "GET", "/api/users")}

    created = 0
    for user in users:
        login = user.get("username") or user.get("alias")
        if not login:
            continue
        if login in existing:
            print(f"Grafana 用户 {login} 已存在，跳过")
            continue
        payload = {
            "name": user.get("name") or login,
            "login": login,
            "password": os.getenv("XXX_GRAFANA_DEFAULT_PASSWORD", "ChangeMe123"),
            "email": f"{login}@example.com"
        }
        grafana_request(session, "POST", "/api/admin/users", payload)
        created += 1
        print(f"Grafana 用户 {login} 创建成功")

    print(f"同步完成，新增 Grafana 用户 {created} 个。")


def main(config=None):
    if config:
        CONFIG.update(config)
    global ZABBIX_URL, ZABBIX_TOKEN, GRAFANA_URL, GRAFANA_TOKEN
    ZABBIX_URL = CONFIG.get("zabbix_url") or ZABBIX_URL
    ZABBIX_TOKEN = CONFIG.get("zabbix_token") or ZABBIX_TOKEN
    GRAFANA_URL = CONFIG.get("grafana_url") or GRAFANA_URL
    GRAFANA_TOKEN = CONFIG.get("grafana_token") or GRAFANA_TOKEN
    sync_accounts()


if __name__ == "__main__":
    main(CONFIG)
'''

CONFIG_FIELDS = [
    {"key": "zabbix_url", "label": "Zabbix API 地址", "placeholder": "https://zabbix/api_jsonrpc.php"},
    {"key": "zabbix_token", "label": "Zabbix Token", "type": "password"},
    {"key": "grafana_url", "label": "Grafana API 地址", "placeholder": "https://grafana/api"},
    {"key": "grafana_token", "label": "Grafana Token", "type": "password"},
]


def seed_grafana_plugin(apps, schema_editor):
    CodeDirectory = apps.get_model("tools", "CodeDirectory")
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")

    directory, _ = CodeDirectory.objects.get_or_create(
        key="network-utilities",
        defaults={
            "title": "网络工具",
            "description": "内置网络脚本",
            "keywords": ["network"],
            "builtin": True,
        },
    )

    repository, _ = CodeRepository.objects.get_or_create(
        name="Grafana 同步助手",
        defaults={
            "language": "python",
            "tags": ["grafana", "zabbix"],
            "description": "从 Zabbix 账号创建 Grafana 用户",
            "directory": directory,
            "content": GRAFANA_SCRIPT,
        },
    )

    version = repository.latest_version
    if version is None:
        version = CodeRepositoryVersion.objects.create(
            repository=repository,
            version="v1.0.0",
            summary="初始化脚本",
            change_log="自动创建",
            content=GRAFANA_SCRIPT,
        )
        repository.latest_version = version
        repository.content = version.content
        repository.save(update_fields=["latest_version", "content"])

    ScriptPlugin.objects.get_or_create(
        slug="grafana-sync",
        defaults={
            "name": "Grafana 账号同步",
            "description": "基于 Zabbix 用户列表自动创建 Grafana 用户",
            "summary": "填写两端 API 地址与 Token 后即可执行。",
            "group": "tools",
            "route": "/tools/grafana-sync",
            "component": "GrafanaSync.vue",
            "builtin": False,
            "is_enabled": False,
            "repository": repository,
            "repository_version": version,
            "metadata": {
                "config_fields": CONFIG_FIELDS,
                "config_values": {},
                "logs": [],
                "runtime_script": "grafana_sync",
            },
        },
    )


def remove_grafana_plugin(apps, schema_editor):
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")
    CodeRepository = apps.get_model("tools", "CodeRepository")
    ScriptPlugin.objects.filter(slug="grafana-sync").delete()
    CodeRepository.objects.filter(name="Grafana 同步助手").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0015_update_account_sync_script_tokenonly"),
    ]

    operations = [
        migrations.RunPython(seed_grafana_plugin, remove_grafana_plugin),
    ]
