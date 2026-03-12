from __future__ import annotations

from django.db import migrations

ACCOUNT_SYNC_SCRIPT = """print('account sync placeholder')"""

CONFIG_FIELDS = [
    {
        "key": "ldap_host",
        "label": "LDAP 地址",
        "type": "input",
        "placeholder": "ldap://ldap.example.com",
    },
    {
        "key": "bind_dn",
        "label": "绑定 DN",
        "type": "input",
        "placeholder": "uid=sync,ou=service,dc=example,dc=com",
    },
    {
        "key": "bind_password",
        "label": "绑定密码",
        "type": "password",
        "placeholder": "请输入密码",
    },
    {
        "key": "base_dn",
        "label": "搜索 Base DN",
        "type": "input",
        "placeholder": "ou=users,dc=example,dc=com",
    },
    {
        "key": "user_filter",
        "label": "用户过滤器",
        "type": "textarea",
        "placeholder": "(objectClass=inetOrgPerson)",
    },
    {
        "key": "default_roles",
        "label": "默认角色 ID",
        "type": "textarea",
        "placeholder": "role-uuid-1,role-uuid-2",
    },
]

DEFAULT_METADATA = {
    "config_fields": CONFIG_FIELDS,
    "config_values": {},
    "logs": [],
    "runtime_script": "account_sync",
}


def seed_account_sync_plugin(apps, schema_editor):
    CodeDirectory = apps.get_model("tools", "CodeDirectory")
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")

    directory, _ = CodeDirectory.objects.get_or_create(
        key="network-utilities",
        defaults={
            "title": "网络工具",
            "description": "内置网络脚本",
            "keywords": ["network", "script"],
            "builtin": True,
        },
    )

    repository, _ = CodeRepository.objects.get_or_create(
        name="账号同步助手",
        defaults={
            "language": "python",
            "tags": ["ldap", "zabbix", "sync"],
            "description": "将 LDAP 账号同步至 Zabbix 的脚本助手",
            "directory": directory,
            "content": ACCOUNT_SYNC_SCRIPT,
        },
    )

    version = repository.latest_version
    if version is None:
        version = CodeRepositoryVersion.objects.create(
            repository=repository,
            version="v1.0.0",
            summary="初始化账号同步脚本",
            change_log="自动创建",
            content=ACCOUNT_SYNC_SCRIPT,
        )
        repository.latest_version = version
        repository.content = version.content
        repository.save(update_fields=["latest_version", "content"])

    ScriptPlugin.objects.get_or_create(
        slug="account-sync",
        defaults={
            "name": "账号同步",
            "description": "将 LDAP 账号与权限同步到 Zabbix。",
            "summary": "支持配置 LDAP、过滤器、默认角色等参数并一键触发同步。",
            "group": "tools",
            "route": "/tools/account-sync",
            "component": "AccountSync.vue",
            "builtin": False,
            "is_enabled": True,
            "repository": repository,
            "repository_version": version,
            "metadata": DEFAULT_METADATA,
        },
    )


def remove_account_sync_plugin(apps, schema_editor):
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")
    CodeRepository = apps.get_model("tools", "CodeRepository")
    repo = CodeRepository.objects.filter(name="账号同步助手").first()
    ScriptPlugin.objects.filter(slug="account-sync").delete()
    if repo:
        repo.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0009_update_ip_regex_plugin_fields"),
    ]

    operations = [
        migrations.RunPython(seed_account_sync_plugin, remove_account_sync_plugin),
    ]
