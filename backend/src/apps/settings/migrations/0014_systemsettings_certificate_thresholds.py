from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0013_systemsettings_platform_logo"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="certificate_expiry_threshold_critical_days",
            field=models.PositiveIntegerField(default=15),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="certificate_expiry_threshold_warning_days",
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="certificate_expiry_threshold_notice_days",
            field=models.PositiveIntegerField(default=45),
        ),
    ]

