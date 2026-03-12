from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0003_proxymapping"),
    ]

    operations = [
        migrations.AddField(
            model_name="assetrecord",
            name="is_removed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="assetrecord",
            name="removed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="assetrecord",
            name="last_seen_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

