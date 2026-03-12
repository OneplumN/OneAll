from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0002_systemsettings_integrations"),
        ("settings", "0004_alter_pluginconfig_created_by_and_more"),
    ]

    operations: list = []
