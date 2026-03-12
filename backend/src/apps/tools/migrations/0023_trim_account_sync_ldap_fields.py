from __future__ import annotations

from django.db import migrations

ACCOUNT_SYNC_SCRIPT = '''"""账号同步脚本：从 LDAP 同步用户至 Zabbix（Token 方式）

说明：
- 前端传入的 CONFIG 优先生效
- 仍兼容旧的环境变量 XXX_LDAP_* / XXX_ZABBIX_*
- 兼容旧的前端字段名（ldap_host/base_dn/bind_dn/bind_password）
"""

import json
import os
from typing import List

import requests
from ldap3 import ALL, ALL_ATTRIBUTES, SUBTREE, Connection, Server

CONFIG = globals().get("CONFIG", {}) or {}


def _config_first(*keys: str, default: str = "") -> str:
    for key in keys:
        value = CONFIG.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return default


def _env_first(*keys: str, default: str = "") -> str:
    for key in keys:
        value = os.getenv(key, "")
        if value not in (None, ""):
            return str(value).strip()
    return default


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def get_ldap_connection() -> Connection:
    ldap_domain = _config_first("ldap_domain", "ldap_host") or _env_first("XXX_LDAP_DOMAIN")
    ldap_user = _config_first("ldap_user", "bind_dn") or _env_first("XXX_LDAP_USER")
    ldap_pwd = _config_first("ldap_pwd", "bind_password") or _env_first("XXX_LDAP_PWD")
    use_ssl = _parse_bool(_config_first("ldap_use_ssl", default="false"))  # kept for compatibility

    if not ldap_domain or not ldap_user:
        raise RuntimeError("LDAP 配置不完整，请检查 ldap_domain/ldap_user")

    server = Server(ldap_domain, get_info=ALL, use_ssl=use_ssl, connect_timeout=5)
    return Connection(server, user=ldap_user, password=ldap_pwd, auto_bind=True)


def fetch_ldap_users() -> List[str]:
    ldap_dc = _config_first("ldap_dc", "base_dn") or _env_first("XXX_LDAP_DC")
    if not ldap_dc:
        raise RuntimeError("LDAP 配置不完整，请检查 ldap_dc")

    conn = get_ldap_connection()
    conn.search(
        search_base=ldap_dc,
        search_filter="(objectclass=inetorgperson)",
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
    token = _config_first("zabbix_token") or _env_first("XXX_ZABBIX_TOKEN")
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
    zabbix_url = _config_first("zabbix_url") or _env_first("XXX_ZABBIX_URL")
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
    {"key": "ldap_domain", "label": "LDAP 地址", "placeholder": "172.31.226.3:589"},
    {"key": "ldap_dc", "label": "LDAP Base DN", "placeholder": "ou=ou,dc=xxx,dc=com"},
    {"key": "ldap_user", "label": "LDAP 绑定 DN", "placeholder": "uid=xxxx,ou=ldapaccount,dc=xxx,dc=com"},
    {"key": "ldap_pwd", "label": "LDAP 绑定密码", "type": "password", "placeholder": "请输入密码"},
    {"key": "zabbix_url", "label": "Zabbix API 地址", "placeholder": "https://zabbix/api_jsonrpc.php"},
    {"key": "zabbix_token", "label": "Zabbix Token", "type": "password", "placeholder": "在界面中生成的 Token"},
]


def trim_fields(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")

    repo = CodeRepository.objects.filter(name="账号同步助手").first()
    plugin = ScriptPlugin.objects.filter(slug="account-sync").first()
    if not repo or not plugin:
        return

    version = CodeRepositoryVersion.objects.create(
        repository=repo,
        version="v1.6.1",
        summary="精简 LDAP 配置项",
        change_log="LDAP 仅保留 domain/dc/user/pwd 四项；脚本优先读取前端配置并兼容旧字段与环境变量。",
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
    plugin.save(update_fields=["metadata", "repository_version", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0022_update_account_sync_script_ldap_config"),
    ]

    operations = [
        migrations.RunPython(trim_fields, migrations.RunPython.noop),
    ]

