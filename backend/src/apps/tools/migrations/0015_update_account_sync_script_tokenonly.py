from __future__ import annotations

from django.db import migrations

ACCOUNT_SYNC_SCRIPT = '''"""账号同步脚本：通过 LDAP 与 Zabbix API 同步账号"""
import os
import json
import requests
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE

CONFIG = globals().get("CONFIG", {}) or {}

LDAP_DOMAIN = os.getenv('XXX_LDAP_DOMAIN', '172.31.226.3:589')
LDAP_DC = os.getenv('XXX_LDAP_DC', 'ou=ou,dc=xxx,dc=com')
LDAP_USER = os.getenv('XXX_LDAP_USER', 'uid=xxxx,ou=ldapaccount,dc=xxx,dc=com')
LDAP_PWD = os.getenv('XXX_LDAP_PWD', 'passwd')

ZABBIX_URL = CONFIG.get('zabbix_url') or os.getenv('XXX_ZABBIX_URL', 'https://zabbix.example.com/api_jsonrpc.php')
ZABBIX_TOKEN = CONFIG.get('zabbix_token') or os.getenv('XXX_ZABBIX_TOKEN')
DEFAULT_ROLE_NAME = os.getenv('XXX_ZABBIX_ROLE_NAME', 'User role')
USERGROUP_KEYWORD = os.getenv('XXX_ZABBIX_USERGROUP_KEYWORD', 'LDAP')


def get_ldap_connection() -> Connection:
    server = Server(LDAP_DOMAIN, get_info=ALL, use_ssl=False, connect_timeout=5)
    conn = Connection(server, user=LDAP_USER, password=LDAP_PWD, auto_bind=True)
    return conn


def fetch_ldap_users() -> list[str]:
    conn = get_ldap_connection()
    conn.search(search_base=LDAP_DC, search_filter='(objectclass=inetorgperson)', attributes=ALL_ATTRIBUTES, search_scope=SUBTREE)
    users = []
    for entry in conn.entries:
        attrs = entry.entry_attributes_as_dict
        uid = attrs.get('uid', [''])[0]
        if uid and uid.isdigit():
            users.append(uid)
    conn.unbind()
    return users


def zabbix_request(session: requests.Session, method: str, params: dict, token: str) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
        "auth": token,
    }
    resp = session.post(ZABBIX_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get('error'):
        raise RuntimeError(data['error'])
    return data['result']


def ensure_token() -> str:
    if not ZABBIX_TOKEN:
        raise RuntimeError('请配置 Zabbix Token，可在界面或环境变量 XXX_ZABBIX_TOKEN 中设置')
    return ZABBIX_TOKEN


def query_ldap_group_id(session: requests.Session, token: str) -> str:
    groups = zabbix_request(session, "usergroup.get", {"output": "extend", "filter": {"name": USERGROUP_KEYWORD}}, token)
    if not groups:
        raise RuntimeError(f"未找到名称包含 {USERGROUP_KEYWORD} 的用户组")
    return groups[0]['usrgrpid']


def query_role_id(session: requests.Session, token: str) -> str:
    roles = zabbix_request(session, "role.get", {"output": "extend"}, token)
    for role in roles:
        if role['name'] == DEFAULT_ROLE_NAME:
            return role['roleid']
    raise RuntimeError(f"未找到角色 {DEFAULT_ROLE_NAME}")


def existing_usernames(session: requests.Session, token: str) -> set[str]:
    users = zabbix_request(session, "user.get", {"output": "extend"}, token)
    return {item['username'] for item in users}


def create_user(session: requests.Session, token: str, username: str, roleid: str, usrgrpid: str):
    params = {
        "username": username,
        "roleid": roleid,
        "usrgrps": [{"usrgrpid": usrgrpid}],
        "lang": "zh_CN",
    }
    zabbix_request(session, "user.create", params, token)
    print(f"用户 {username} 创建成功")


def sync_accounts():
    ldap_users = fetch_ldap_users()
    session = requests.Session()
    session.mount(ZABBIX_URL, requests.adapters.HTTPAdapter(max_retries=3))
    token = ensure_token()
    usrgrpid = query_ldap_group_id(session, token)
    roleid = query_role_id(session, token)
    existing = existing_usernames(session, token)

    created = 0
    for uid in ldap_users:
        if uid in existing:
            print(f"用户 {uid} 已存在，跳过")
            continue
        create_user(session, token, uid, roleid, usrgrpid)
        created += 1

    print(f"同步完成，共创建 {created} 个用户。")


def main(config=None):
    if config:
        CONFIG.update(config)
    global ZABBIX_URL, ZABBIX_TOKEN
    ZABBIX_URL = CONFIG.get('zabbix_url') or ZABBIX_URL
    ZABBIX_TOKEN = CONFIG.get('zabbix_token') or ZABBIX_TOKEN
    sync_accounts()


if __name__ == '__main__':
    main(CONFIG)
'''


def update_script(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")

    repo = CodeRepository.objects.filter(name="账号同步助手").first()
    plugin = ScriptPlugin.objects.filter(slug="account-sync").first()
    if not repo or not plugin:
        return

    version = CodeRepositoryVersion.objects.create(
        repository=repo,
        version="v1.5.0",
        summary="仅使用 Token 调用 Zabbix API",
        change_log="移除用户名/密码逻辑，改为 URL + Token",
        content=ACCOUNT_SYNC_SCRIPT,
    )
    repo.latest_version = version
    repo.content = version.content
    repo.save(update_fields=["latest_version", "content"])
    plugin.repository_version = version
    plugin.save(update_fields=["repository_version", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0014_zabbix_token_support"),
    ]

    operations = [
        migrations.RunPython(update_script, migrations.RunPython.noop),
    ]
