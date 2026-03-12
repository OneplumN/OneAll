from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_user_auth_source"),
        ("probes", "0010_normalize_execution_statuses"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProbeConfigRefreshRequest",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="probeconfigrefreshrequest_created",
                        to="core.user",
                    ),
                ),
                (
                    "probe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="config_refresh_requests",
                        to="probes.probenode",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="probeconfigrefreshrequest_updated",
                        to="core.user",
                    ),
                ),
            ],
            options={
                "db_table": "probes_config_refresh_request",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="probeconfigrefreshrequest",
            index=models.Index(fields=["probe", "processed_at"], name="probes_conf_probe_i_5a49c5_idx"),
        ),
    ]
