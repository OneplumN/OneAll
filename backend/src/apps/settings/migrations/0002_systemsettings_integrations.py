from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="integrations",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
