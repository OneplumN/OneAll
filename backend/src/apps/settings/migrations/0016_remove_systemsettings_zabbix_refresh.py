from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0015_ensure_report_asset_governance_plugin"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="systemsettings",
            name="zabbix_dashboard_refresh_seconds",
        ),
    ]

