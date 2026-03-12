from __future__ import annotations

from django.db import migrations

ACCOUNT_SYNC_SCRIPT = '''"""账号同步脚本：从 LDAP 同步用户至 Zabbix"""
import json
import logging
import os
from typing import Dict, List

import requests
from ldap3 import Connection, Server, ALL, SUBTREE

CONFIG = globals().get("CONFIG", {}) or {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("account_sync")


def get_config(key: str, default: str = "") -> str:
    value = CONFIG.get(key)
    if value in (None, ""):
        value = os.getenv(key.upper(), default)
    if isinstance(value, str):
        return value.strip()
    return str(value) if value is not None else default


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def _first(value):
    if isinstance(value, list):
        return value[0] if value else ""
    return value or ""


def fetch_ldap_users() -> List[Dict[str, str]]:
    host = get_config("ldap_host")
    base_dn = get_config("base_dn")
    bind_dn = get_config("bind_dn")
    bind_password = get_config("bind_password")
    search_filter = get_config("user_filter", "(objectClass=person)")
    uid_attr = get_config("ldap_uid_attr", "uid")
    name_attr = get_config("ldap_display_name_attr", "cn")
    email_attr = get_config("ldap_email_attr", "mail")
    use_ssl = parse_bool(get_config("ldap_use_ssl", "false"))

    if not host or not base_dn or not bind_dn:
        raise RuntimeError("LDAP 配置不完整，请检查 host/base_dn/bind_dn")

    logger.info("连接 LDAP: %s (SSL=%s)", host, use_ssl)
    server = Server(host, use_ssl=use_ssl, get_info=ALL)
    conn = Connection(server, user=bind_dn, password=bind_password, auto_bind=True)
    conn.search(search_base=base_dn, search_filter=search_filter, search_scope=SUBTREE, attributes=[uid_attr, name_attr, email_attr])

    users: List[Dict[str, str]] = []
    for entry in conn.entries:
        data = entry.entry_attributes_as_dict
        username = _first(data.get(uid_attr))
        if not username:
            continue
        users.append(
            {
                "username": username,
                "name": _first(data.get(name_attr)) or username,
                "email": _first(data.get(email_attr)) or "",
            }
        )
    conn.unbind()
    logger.info("LDAP 返回 %s 个用户", len(users))
    return users


def zabbix_request(session: requests.Session, url: str, method: str, params: Dict, token: str | None = None) -> Dict:
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    if token:
        payload["auth"] = token
    response = session.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"Zabbix API 错误: {data['error']}")
    return data["result"]


def zabbix_login(session: requests.Session, url: str) -> str:
    username = get_config("zabbix_username")
    password = get_config("zabbix_password")
    result = zabbix_request(session, url, "user.login", {"username": username, "password": password})
    logger.info("成功获取 Zabbix token")
    return result


def zabbix_existing_usernames(session: requests.Session, url: str, token: str) -> set[str]:
    result = zabbix_request(session, url, "user.get", {"output": ["username"]}, token)
    return {item.get("username") for item in result if item.get("username")}


def parse_group_ids() -> List[Dict[str, str]]:
    raw = get_config("zabbix_usergroup_ids", "")
    groups = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            groups.append({"usrgrpid": part})
    if not groups:
        raise RuntimeError("请配置至少一个 Zabbix 用户组 ID")
    return groups


def zabbix_create_user(session: requests.Session, url: str, token: str, user: Dict[str, str]):
    groups = parse_group_ids()
    payload = {
        "username": user["username"],
        "name": user["name"],
        "passwd": get_config("zabbix_default_password", "ChangeMe123"),
        "usrgrps": groups,
        "lang": "zh_CN",
    }
    role_id = get_config("zabbix_role_id")
    if role_id:
        payload["roleid"] = role_id
    email = user.get("email")
    if email:
        payload["user_medias"] = [
            {
                "mediatypeid": "1",
                "sendto": email,
                "active": 0,
                "severity": 63,
                "period": "1-7,00:00-24:00",
            }
        ]
    zabbix_request(session, url, "user.create", payload, token)
    logger.info("创建用户 %s 成功", user["username"])


def sync_users():
    zabbix_url = get_config("zabbix_url")
    if not zabbix_url:
        raise RuntimeError("请配置 Zabbix API 地址")

    ldap_users = fetch_ldap_users()
    session = requests.Session()
    session.verify = parse_bool(get_config("zabbix_verify_ssl", "true"))
    token = zabbix_login(session, zabbix_url)
    existing = zabbix_existing_usernames(session, zabbix_url, token)

    created = 0
    for user in ldap_users:
        if user["username"] in existing:
            continue
        zabbix_create_user(session, zabbix_url, token, user)
        created += 1

    logger.info("同步完成，新增用户 %s 个。", created)


def main(config: Dict[str, str] | None = None):
    if config:
        CONFIG.update(config)
    sync_users()


if __name__ == "__main__":
    main(CONFIG)
'''

CONFIG_FIELDS = [
    {"key": "ldap_host", "label": "LDAP 地址", "placeholder": "ldap://ldap.example.com"},
    {"key": "ldap_use_ssl", "label": "使用 SSL (true/false)", "placeholder": "false"},
    {"key": "bind_dn", "label": "绑定 DN"},
    {"key": "bind_password", "label": "绑定密码", "type": "password"},
    {"key": "base_dn", "label": "Base DN"},
    {"key": "user_filter", "label": "用户过滤器", "type": "textarea", "placeholder": "(objectClass=inetOrgPerson)"},
    {"key": "ldap_uid_attr", "label": "UID 属性", "placeholder": "uid"},
    {"key": "ldap_display_name_attr", "label": "显示名属性", "placeholder": "cn"},
    {"key": "ldap_email_attr", "label": "邮箱属性", "placeholder": "mail"},
    {"key": "zabbix_url", "label": "Zabbix API 地址", "placeholder": "https://zabbix/api_jsonrpc.php"},
    {"key": "zabbix_username", "label": "Zabbix 用户名"},
    {"key": "zabbix_password", "label": "Zabbix 密码", "type": "password"},
    {"key": "zabbix_usergroup_ids", "label": "用户组 IDs (逗号分隔)", "type": "textarea"},
    {"key": "zabbix_role_id", "label": "角色 ID", "placeholder": "可选"},
    {"key": "zabbix_default_password", "label": "新建用户初始密码", "placeholder": "ChangeMe123"},
    {"key": "zabbix_verify_ssl", "label": "验证 HTTPS 证书", "placeholder": "true"},
]

DEFAULT_METADATA = {
    "config_fields": CONFIG_FIELDS,
    "config_values": {},
    "logs": [],
    "runtime_script": "account_sync",
}


def update_account_sync_script(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")

    repo = CodeRepository.objects.filter(name="账号同步助手").first()
    plugin = ScriptPlugin.objects.filter(slug="account-sync").first()
    if not repo or not plugin:
        return

    version = CodeRepositoryVersion.objects.create(
        repository=repo,
        version="v1.1.0",
        summary="完善账号同步脚本",
        change_log="替换占位脚本并补充配置",
        content=ACCOUNT_SYNC_SCRIPT,
    )
    repo.latest_version = version
    repo.content = version.content
    repo.save(update_fields=["latest_version", "content"])

    plugin.repository_version = version
    metadata = dict(DEFAULT_METADATA)
    metadata["logs"] = (plugin.metadata or {}).get("logs", [])
    plugin.metadata = metadata
    plugin.route = "/tools/account-sync"
    plugin.component = "AccountSync.vue"
    plugin.summary = "配置 LDAP 与 Zabbix 信息后，一键同步员工账号"
    plugin.save(update_fields=["metadata", "repository_version", "route", "component", "summary", "updated_at"])


def reverse_update(apps, schema_editor):
    # No reversal needed
    return


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0010_seed_account_sync_plugin"),
    ]

    operations = [
        migrations.RunPython(update_account_sync_script, reverse_update),
    ]
