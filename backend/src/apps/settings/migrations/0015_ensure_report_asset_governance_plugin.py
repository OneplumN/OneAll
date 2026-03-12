from __future__ import annotations

from django.db import migrations


def ensure_asset_governance_plugin(apps, schema_editor):
    PluginConfig = apps.get_model("settings", "PluginConfig")
    User = apps.get_model("core", "User")

    admin_user = User.objects.filter(is_superuser=True).order_by("date_joined").first()

    config, created = PluginConfig.objects.get_or_create(
        type="report_asset_governance",
        defaults={
            "name": "资产监控治理",
            "enabled": True,
            "config": {},
            "status": "unknown",
            "created_by": admin_user,
            "updated_by": admin_user,
        },
    )
    if not created and not config.name:
        config.name = "资产监控治理"
        config.save(update_fields=["name", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0014_systemsettings_certificate_thresholds"),
    ]

    operations = [
        migrations.RunPython(ensure_asset_governance_plugin, migrations.RunPython.noop),
    ]

