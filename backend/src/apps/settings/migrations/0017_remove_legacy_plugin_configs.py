from __future__ import annotations

from django.db import migrations


LEGACY_PLUGIN_TYPES = [
    "monitoring_zabbix",
    "monitoring_prometheus",
    "report_detection",
    "report_asset_governance",
    "tool_plugin_center",
]


def remove_legacy_plugin_configs(apps, schema_editor):
    PluginConfig = apps.get_model("settings", "PluginConfig")
    PluginConfig.objects.filter(type__in=LEGACY_PLUGIN_TYPES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0016_remove_systemsettings_zabbix_refresh"),
    ]

    operations = [
        migrations.RunPython(remove_legacy_plugin_configs, migrations.RunPython.noop),
    ]
