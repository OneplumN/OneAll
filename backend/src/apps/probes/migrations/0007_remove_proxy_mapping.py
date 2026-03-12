from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("probes", "0006_probenode_runtime_metrics"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="probenode",
            name="proxy",
        ),
        migrations.DeleteModel(
            name="ProxyMapping",
        ),
    ]
