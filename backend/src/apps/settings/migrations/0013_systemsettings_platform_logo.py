from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0012_systemsettings_zabbix_refresh"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="platform_logo",
            field=models.TextField(blank=True, default=""),
        ),
    ]

