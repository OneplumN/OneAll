from __future__ import annotations

from django.db import migrations


def ensure_plugin_configs(apps, schema_editor):
    from apps.settings.data import PLUGIN_DEFINITIONS

    PluginConfig = apps.get_model("settings", "PluginConfig")
    User = apps.get_model("core", "User")

    admin_user = (
        User.objects.filter(is_superuser=True)
        .order_by("date_joined")
        .first()
    )

    for definition in PLUGIN_DEFINITIONS:
        config, created = PluginConfig.objects.get_or_create(
            type=definition.key,
            defaults={
                "name": definition.name,
                "enabled": definition.builtin,
                "config": {},
                "status": "unknown",
                "created_by": admin_user,
                "updated_by": admin_user,
            },
        )
        if not created:
            updated = False
            if not config.name:
                config.name = definition.name
                updated = True
            if admin_user and config.created_by is None:
                config.created_by = admin_user
                updated = True
            if updated:
                config.save(update_fields=["name", "created_by", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0002_pluginconfig"),
    ]

    operations = [
        migrations.RunPython(ensure_plugin_configs, migrations.RunPython.noop),
    ]
