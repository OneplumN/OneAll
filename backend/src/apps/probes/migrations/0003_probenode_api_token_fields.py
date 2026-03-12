from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("probes", "0002_alter_probenode_options_alter_proxymapping_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="probenode",
            name="api_token_hash",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="probenode",
            name="api_token_hint",
            field=models.CharField(blank=True, default="", max_length=8),
        ),
        migrations.AddField(
            model_name="probenode",
            name="last_authenticated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
