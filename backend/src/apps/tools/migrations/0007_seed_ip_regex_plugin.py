from __future__ import annotations

from django.db import migrations


def seed_ip_regex_plugin(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")

    repository = CodeRepository.objects.filter(name="IP 正则助手").first()
    if repository is None:
        return

    version = repository.latest_version or CodeRepositoryVersion.objects.filter(repository=repository).order_by("-created_at").first()

    ScriptPlugin.objects.get_or_create(
        slug="ip-regex-helper",
        defaults={
            "name": "IP 正则助手",
            "description": "提供 IP ↔ 正则转换能力，可在代码管理中维护脚本。",
            "repository": repository,
            "repository_version": version,
            "metadata": {
                "compile_func": "ip_to_regex",
                "expand_func": "regex_to_ips",
            },
            "is_enabled": True,
        },
    )


def remove_ip_regex_plugin(apps, schema_editor):
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")
    ScriptPlugin.objects.filter(slug="ip-regex-helper").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0006_scriptplugin"),
    ]

    operations = [
        migrations.RunPython(seed_ip_regex_plugin, remove_ip_regex_plugin),
    ]
