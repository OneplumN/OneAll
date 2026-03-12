from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0002_auditlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="ToolDefinition",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("name", models.CharField(max_length=150, unique=True)),
                ("category", models.CharField(blank=True, max_length=100)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("description", models.TextField(blank=True)),
                ("entry_point", models.CharField(blank=True, max_length=255)),
                ("default_parameters", models.JSONField(blank=True, default=dict)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="tooldefinition_created",
                        to="core.user",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="tooldefinition_updated",
                        to="core.user",
                    ),
                ),
            ],
            options={
                "db_table": "tools_tool_definition",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="ScriptVersion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("version", models.CharField(max_length=40)),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("python", "Python"),
                            ("shell", "Shell"),
                            ("powershell", "PowerShell"),
                            ("other", "Other"),
                        ],
                        default="python",
                        max_length=20,
                    ),
                ),
                ("repository_path", models.CharField(blank=True, max_length=255)),
                ("content", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("checksum", models.CharField(editable=False, max_length=64)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="scriptversion_created",
                        to="core.user",
                    ),
                ),
                (
                    "tool",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="versions",
                        to="tools.tooldefinition",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="scriptversion_updated",
                        to="core.user",
                    ),
                ),
            ],
            options={
                "db_table": "tools_script_version",
                "ordering": ("tool", "-created_at"),
            },
        ),
        migrations.AddField(
            model_name="tooldefinition",
            name="latest_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="latest_for_tools",
                to="tools.scriptversion",
            ),
        ),
        migrations.CreateModel(
            name="ToolExecution",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("run_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("succeeded", "Succeeded"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("parameters", models.JSONField(blank=True, default=dict)),
                ("output", models.TextField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="toolexecution_created",
                        to="core.user",
                    ),
                ),
                (
                    "script_version",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="executions",
                        to="tools.scriptversion",
                    ),
                ),
                (
                    "tool",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="executions",
                        to="tools.tooldefinition",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="toolexecution_updated",
                        to="core.user",
                    ),
                ),
            ],
            options={
                "db_table": "tools_tool_execution",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AlterUniqueTogether(name="scriptversion", unique_together={("tool", "version")}),
    ]
