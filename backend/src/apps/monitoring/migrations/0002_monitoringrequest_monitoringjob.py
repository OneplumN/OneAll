from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MonitoringRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("title", models.CharField(max_length=128)),
                ("target", models.CharField(max_length=512)),
                (
                    "protocol",
                    models.CharField(
                        choices=[
                            ("HTTP", "HTTP"),
                            ("HTTPS", "HTTPS"),
                            ("Telnet", "Telnet"),
                            ("WSS", "WebSocket Secure"),
                            ("CERTIFICATE", "Certificate"),
                        ],
                        default="HTTPS",
                        max_length=16,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending Approval"), ("approved", "Approved"), ("rejected", "Rejected"), ("cancelled", "Cancelled")],
                        default="pending",
                        max_length=32,
                    ),
                ),
                ("frequency_minutes", models.PositiveIntegerField(default=15)),
                ("schedule_cron", models.CharField(blank=True, max_length=64)),
                ("itsm_ticket_id", models.CharField(blank=True, max_length=64)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="monitoringrequest_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="monitoringrequest_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Monitoring Request",
                "verbose_name_plural": "Monitoring Requests",
                "db_table": "monitoring_request",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="MonitoringJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("schedule_cron", models.CharField(blank=True, max_length=64)),
                ("frequency_minutes", models.PositiveIntegerField(default=15)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("paused", "Paused"), ("archived", "Archived")],
                        default="active",
                        max_length=16,
                    ),
                ),
                ("last_run_at", models.DateTimeField(blank=True, null=True)),
                ("next_run_at", models.DateTimeField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="monitoringjob_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="jobs",
                        to="monitoring.monitoringrequest",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="monitoringjob_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Monitoring Job",
                "verbose_name_plural": "Monitoring Jobs",
                "db_table": "monitoring_job",
                "ordering": ("-created_at",),
            },
        ),
    ]
