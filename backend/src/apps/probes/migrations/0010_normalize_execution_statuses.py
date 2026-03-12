from __future__ import annotations

from django.db import migrations

STATUS_MAPPING = {
    "success": "succeeded",
    "successes": "succeeded",
    "succeed": "succeeded",
    "timeout": "missed",
    "failure": "failed",
    "error": "failed",
}


def normalize_statuses(apps, schema_editor):
    Execution = apps.get_model("probes", "ProbeScheduleExecution")
    for old, new in STATUS_MAPPING.items():
        Execution.objects.filter(status__iexact=old).update(status=new)


class Migration(migrations.Migration):
    dependencies = [
        ("probes", "0009_probescheduleexecution"),
    ]

    operations = [
        migrations.RunPython(normalize_statuses, migrations.RunPython.noop),
    ]
