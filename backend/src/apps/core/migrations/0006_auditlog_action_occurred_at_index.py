from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_cleanup_multi_roles_to_single"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["action", "occurred_at"], name="core_auditlog_act_occ_idx"),
        ),
    ]
