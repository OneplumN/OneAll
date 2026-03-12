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
            name="KnowledgeArticle",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("category", models.CharField(blank=True, max_length=100)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("content", models.TextField()),
                ("attachments", models.JSONField(blank=True, default=list)),
                (
                    "visibility_scope",
                    models.CharField(
                        choices=[
                            ("internal", "内部可见"),
                            ("team", "团队内"),
                            ("public", "公开"),
                        ],
                        default="internal",
                        max_length=32,
                    ),
                ),
                ("last_edited_at", models.DateTimeField(auto_now=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="knowledgearticle_created",
                        to="core.user",
                    ),
                ),
                (
                    "last_editor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="edited_articles",
                        to="core.user",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="knowledgearticle_updated",
                        to="core.user",
                    ),
                ),
            ],
            options={
                "db_table": "knowledge_article",
                "ordering": ("-last_edited_at",),
            },
        ),
    ]
