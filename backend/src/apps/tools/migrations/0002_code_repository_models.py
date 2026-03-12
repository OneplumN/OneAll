from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CodeDirectory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("key", models.SlugField(max_length=60, unique=True)),
                ("title", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("keywords", models.JSONField(blank=True, default=list)),
                ("builtin", models.BooleanField(default=False)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="codedirectory_created",
                        to="core.user",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="codedirectory_updated",
                        to="core.user",
                    ),
                ),
            ],
            options={
                "db_table": "tools_code_directory",
                "ordering": ("title",),
            },
        ),
        migrations.CreateModel(
            name="CodeRepository",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("name", models.CharField(max_length=150, unique=True)),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("python", "Python"),
                            ("shell", "Shell"),
                            ("powershell", "PowerShell"),
                            ("bash", "Bash"),
                            ("go", "Go"),
                            ("javascript", "JavaScript"),
                            ("typescript", "TypeScript"),
                            ("java", "Java"),
                            ("xml", "XML"),
                            ("yaml", "YAML"),
                            ("json", "JSON"),
                            ("sql", "SQL"),
                            ("other", "Other"),
                        ],
                        default="python",
                        max_length=40,
                    ),
                ),
                ("tags", models.JSONField(blank=True, default=list)),
                ("description", models.TextField(blank=True)),
                ("content", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="coderepository_created",
                        to="core.user",
                    ),
                ),
                (
                    "directory",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="repositories",
                        to="tools.codedirectory",
                    ),
                ),
            ],
            options={
                "db_table": "tools_code_repository",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="CodeRepositoryVersion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("version", models.CharField(max_length=40)),
                ("summary", models.CharField(blank=True, max_length=255)),
                ("change_log", models.TextField(blank=True)),
                ("content", models.TextField()),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="coderepositoryversion_created",
                        to="core.user",
                    ),
                ),
                (
                    "repository",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="versions",
                        to="tools.coderepository",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="coderepositoryversion_updated",
                        to="core.user",
                    ),
                ),
            ],
            options={
                "db_table": "tools_code_repository_version",
                "ordering": ("repository", "-created_at"),
            },
        ),
        migrations.AddField(
            model_name="coderepository",
            name="latest_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="+",
                to="tools.coderepositoryversion",
            ),
        ),
        migrations.AddConstraint(
            model_name="coderepository",
            constraint=models.UniqueConstraint(fields=("directory", "name"), name="tools_code_repository_directory_name"),
        ),
        migrations.AlterUniqueTogether(
            name="coderepositoryversion",
            unique_together={("repository", "version")},
        ),
        migrations.AddField(
            model_name="coderepository",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="coderepository_updated",
                to="core.user",
            ),
        ),
    ]
