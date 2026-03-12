from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("probes", "0005_probeschedule"),
    ]

    operations = [
        migrations.AddField(
            model_name="probenode",
            name="runtime_metrics",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
