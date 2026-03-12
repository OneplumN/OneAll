from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("action", models.CharField(max_length=128)),
                ("target_type", models.CharField(blank=True, max_length=128)),
                ("target_id", models.CharField(blank=True, max_length=128)),
                ("result", models.CharField(default="success", max_length=32)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "core_audit_log",
                "ordering": ("-occurred_at", "-created_at"),
                "verbose_name": "Audit Log",
                "verbose_name_plural": "Audit Logs",
            },
        ),
    ]
