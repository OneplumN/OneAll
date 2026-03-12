from __future__ import annotations

from django.db import migrations

ACCOUNT_SYNC_SCRIPT = '''"""账号同步脚本：从 LDAP 同步用户至 Zabbix（Token 方式）"""
import json
import os
from typing import List

import requests
from ldap3 import ALL, ALL_ATTRIBUTES, SUBTREE, Connection, Server

CONFIG = globals().get("CONFIG", {}) or {}


def _get_config(key: str, default: str = "", env_key: str | None = None) -> str:
    value = CONFIG.get(key)
    if value in (None, ""):
        if env_key:
            value = os.getenv(env_key, "")
        if not value:
            value = os.getenv(key.upper(), "")
    if value in (None, ""):
        return default
    if isinstance(value, str):
        return value.strip()
    return str(value)


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def get_ldap_connection() -> Connection:
    host = _get_config("ldap_host", env_key="XXX_LDAP_DOMAIN")
    bind_dn = _get_config("bind_dn", env_key="XXX_LDAP_USER")
    bind_password = _get_config("bind_password", env_key="XXX_LDAP_PWD")
    use_ssl = _parse_bool(_get_config("ldap_use_ssl", "false"))

    if not host or not bind_dn:
        raise RuntimeError("LDAP 配置不完整，请检查 ldap_host/bind_dn")

    server = Server(host, get_info=ALL, use_ssl=use_ssl, connect_timeout=5)
    return Connection(server, user=bind_dn, password=bind_password, auto_bind=True)


def fetch_ldap_users() -> List[str]:
    base_dn = _get_config("base_dn", env_key="XXX_LDAP_DC")
    search_filter = _get_config("user_filter", "(objectclass=inetorgperson)")
    if not base_dn:
        raise RuntimeError("LDAP 配置不完整，请检查 base_dn")

    conn = get_ldap_connection()
    conn.search(
        search_base=base_dn,
        search_filter=search_filter,
        attributes=ALL_ATTRIBUTES,
        search_scope=SUBTREE,
    )
    users: List[str] = []
    for entry in conn.entries:
        attrs = entry.entry_attributes_as_dict
        uid = (attrs.get("uid") or [""])[0]
        uid = str(uid).strip()
        if uid and uid.isdigit():
            users.append(uid)
    conn.unbind()
    return users


def zabbix_request(session: requests.Session, url: str, method: str, params: dict, token: str) -> dict:
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1, "auth": token}
    resp = session.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data["result"]


def ensure_token() -> str:
    token = _get_config("zabbix_token", env_key="XXX_ZABBIX_TOKEN")
    if not token:
        raise RuntimeError("请配置 Zabbix Token（zabbix_token）")
    return token


def query_ldap_group_id(session: requests.Session, url: str, token: str) -> str:
    keyword = os.getenv("XXX_ZABBIX_USERGROUP_KEYWORD", "LDAP")
    groups = zabbix_request(session, url, "usergroup.get", {"output": "extend", "filter": {"name": keyword}}, token)
    if not groups:
        raise RuntimeError(f"未找到名称包含 {keyword} 的用户组")
    return groups[0]["usrgrpid"]


def query_role_id(session: requests.Session, url: str, token: str) -> str:
    role_name = os.getenv("XXX_ZABBIX_ROLE_NAME", "User role")
    roles = zabbix_request(session, url, "role.get", {"output": "extend"}, token)
    for role in roles:
        if role.get("name") == role_name:
            return role["roleid"]
    raise RuntimeError(f"未找到角色 {role_name}")


def existing_usernames(session: requests.Session, url: str, token: str) -> set[str]:
    users = zabbix_request(session, url, "user.get", {"output": "extend"}, token)
    return {item["username"] for item in users if item.get("username")}


def create_user(session: requests.Session, url: str, token: str, username: str, roleid: str, usrgrpid: str):
    params = {
        "username": username,
        "roleid": roleid,
        "usrgrps": [{"usrgrpid": usrgrpid}],
        "lang": "zh_CN",
    }
    zabbix_request(session, url, "user.create", params, token)
    print(f"用户 {username} 创建成功")


def sync_accounts():
    zabbix_url = _get_config("zabbix_url", env_key="XXX_ZABBIX_URL")
    if not zabbix_url:
        raise RuntimeError("请配置 Zabbix API 地址（zabbix_url）")

    ldap_users = fetch_ldap_users()
    session = requests.Session()
    session.mount(zabbix_url, requests.adapters.HTTPAdapter(max_retries=3))
    token = ensure_token()
    usrgrpid = query_ldap_group_id(session, zabbix_url, token)
    roleid = query_role_id(session, zabbix_url, token)
    existing = existing_usernames(session, zabbix_url, token)

    created = 0
    for uid in ldap_users:
        if uid in existing:
            print(f"用户 {uid} 已存在，跳过")
            continue
        create_user(session, zabbix_url, token, uid, roleid, usrgrpid)
        created += 1

    print(f"同步完成，共创建 {created} 个用户。")


def main(config=None):
    if config:
        CONFIG.update(config)
    sync_accounts()


if __name__ == "__main__":
    main(CONFIG)
'''

CONFIG_FIELDS = [
    {"key": "ldap_host", "label": "LDAP 地址", "placeholder": "ldap://ldap.example.com"},
    {"key": "ldap_use_ssl", "label": "LDAP 使用 SSL (true/false)", "placeholder": "false"},
    {"key": "bind_dn", "label": "绑定 DN", "placeholder": "uid=sync,ou=service,dc=example,dc=com"},
    {"key": "bind_password", "label": "绑定密码", "type": "password", "placeholder": "请输入密码"},
    {"key": "base_dn", "label": "搜索 Base DN", "placeholder": "ou=users,dc=example,dc=com"},
    {"key": "user_filter", "label": "用户过滤器", "type": "textarea", "placeholder": "(objectClass=inetOrgPerson)"},
    {"key": "zabbix_url", "label": "Zabbix API 地址", "placeholder": "https://zabbix/api_jsonrpc.php"},
    {"key": "zabbix_token", "label": "Zabbix Token", "type": "password", "placeholder": "在界面中生成的 Token"},
]


def update_account_sync(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")

    repo = CodeRepository.objects.filter(name="账号同步助手").first()
    plugin = ScriptPlugin.objects.filter(slug="account-sync").first()
    if not repo or not plugin:
        return

    version = CodeRepositoryVersion.objects.create(
        repository=repo,
        version="v1.6.0",
        summary="支持在前端配置 LDAP 信息",
        change_log="将 LDAP 参数改为可通过插件配置传入；Zabbix 仍使用 URL + Token。",
        content=ACCOUNT_SYNC_SCRIPT,
    )
    repo.latest_version = version
    repo.content = version.content
    repo.save(update_fields=["latest_version", "content"])

    metadata = dict(plugin.metadata or {})
    metadata["config_fields"] = CONFIG_FIELDS
    metadata.setdefault("config_values", {})
    metadata.setdefault("logs", [])
    metadata["runtime_script"] = "account_sync"

    plugin.repository_version = version
    plugin.metadata = metadata
    plugin.summary = "配置 LDAP 与 Zabbix 信息后，一键触发同步任务"
    plugin.save(update_fields=["metadata", "repository_version", "summary", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0021_update_ipmp_sync_script"),
    ]

    operations = [
        migrations.RunPython(update_account_sync, migrations.RunPython.noop),
    ]

