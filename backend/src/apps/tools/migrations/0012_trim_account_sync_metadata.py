from __future__ import annotations

from django.db import migrations

NEW_CONFIG_FIELDS = [
    {"key": "zabbix_url", "label": "Zabbix API 地址", "placeholder": "https://zabbix/api_jsonrpc.php"},
    {"key": "zabbix_username", "label": "Zabbix 用户名", "placeholder": "Admin"},
    {"key": "zabbix_password", "label": "Zabbix 密码", "type": "password"},
]

ACCOUNT_SYNC_SCRIPT = '''"""账号同步脚本：将 LDAP 用户同步到 Zabbix"""
import json
import logging
import os
from typing import Dict, List

import requests
from ldap3 import Connection, Server, ALL, SUBTREE

CONFIG = globals().get("CONFIG", {}) or {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("account_sync")

# 默认配置，若界面未提供参数，可直接在此处修改
DEFAULTS = {
    "ldap_host": "ldap://ldap.example.com",
    "ldap_use_ssl": "false",
    "bind_dn": "uid=sync,ou=service,dc=example,dc=com",
    "bind_password": "password",
    "base_dn": "ou=users,dc=example,dc=com",
    "user_filter": "(objectClass=inetOrgPerson)",
    "ldap_uid_attr": "uid",
    "ldap_display_name_attr": "cn",
    "ldap_email_attr": "mail",
    "zabbix_url": "https://zabbix.example.com/api_jsonrpc.php",
    "zabbix_username": "Admin",
    "zabbix_password": "zabbix",
    "zabbix_usergroup_ids": "23",
    "zabbix_role_id": "",
    "zabbix_default_password": "ChangeMe123",
    "zabbix_verify_ssl": "true",
}


def get_config(key: str, default: str = "") -> str:
    value = CONFIG.get(key)
    if value in (None, ""):
        value = os.getenv(key.upper()) or DEFAULTS.get(key, default)
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
        raise RuntimeError("LDAP 配置不完整，请在脚本中更新默认配置。")

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
        raise RuntimeError("请在脚本中配置 Zabbix 用户组 ID")
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


def update_metadata(apps, schema_editor):
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")

    plugin = ScriptPlugin.objects.filter(slug="account-sync").first()
    repo = CodeRepository.objects.filter(name="账号同步助手").first()
    if not plugin or not repo:
        return

    version = CodeRepositoryVersion.objects.create(
        repository=repo,
        version="v1.2.0",
        summary="精简配置字段，仅暴露 Zabbix 连接信息",
        change_log="更新脚本默认配置，保留 LDAP 参数在脚本内",
        content=ACCOUNT_SYNC_SCRIPT,
    )
    repo.latest_version = version
    repo.content = version.content
    repo.save(update_fields=["latest_version", "content"])

    metadata = dict(plugin.metadata or {})
    metadata["config_fields"] = NEW_CONFIG_FIELDS
    metadata.setdefault("config_values", {})
    metadata["config_values"] = {
        **{field["key"]: metadata.get("config_values", {}).get(field["key"], "") for field in NEW_CONFIG_FIELDS}
    }
    metadata.setdefault("logs", [])
    metadata["runtime_script"] = "account_sync"

    plugin.metadata = metadata
    plugin.repository_version = version
    plugin.save(update_fields=["metadata", "repository_version", "updated_at"])


def reverse_metadata(apps, schema_editor):
    # No automatic rollback
    return


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0011_update_account_sync_script"),
    ]

    operations = [
        migrations.RunPython(update_metadata, reverse_metadata),
    ]
