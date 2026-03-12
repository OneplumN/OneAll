from __future__ import annotations

from django.db import migrations


def update_ip_regex_plugin(apps, schema_editor):
    ScriptPlugin = apps.get_model("tools", "ScriptPlugin")
    plugin = ScriptPlugin.objects.filter(slug="ip-regex-helper").first()
    if not plugin:
        return
    plugin.route = plugin.route or "/tools/ip-regex"
    plugin.component = plugin.component or "IpRegexHelper.vue"
    plugin.summary = plugin.summary or "IP 与正则表达式互转助手，可调用代码管理中的脚本。"
    plugin.group = plugin.group or "tools"
    plugin.builtin = True
    metadata = dict(plugin.metadata or {})
    metadata.setdefault("runtime_script", "ip_regex")
    plugin.metadata = metadata
    plugin.save(update_fields=["route", "component", "summary", "group", "builtin", "metadata", "updated_at"])


def reverse_update(apps, schema_editor):
    # no-op
    return


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0008_scriptplugin_builtin_scriptplugin_component_and_more"),
    ]

    operations = [
        migrations.RunPython(update_ip_regex_plugin, reverse_update),
    ]
