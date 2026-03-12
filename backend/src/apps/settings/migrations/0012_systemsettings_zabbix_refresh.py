from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0011_alter_alerttemplate_created_by_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="zabbix_dashboard_refresh_seconds",
            field=models.PositiveIntegerField(
                choices=[(30, 30), (60, 60), (300, 300), (900, 900), (1800, 1800), (3600, 3600)],
                default=60,
            ),
        ),
    ]
