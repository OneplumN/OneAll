from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge", "0004_populate_categories"),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeArticleVersion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("version", models.PositiveIntegerField()),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220)),
                ("category", models.CharField(blank=True, max_length=100)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("visibility_scope", models.CharField(max_length=32)),
                ("content", models.TextField()),
                ("summary", models.CharField(blank=True, max_length=255)),
                (
                    "article",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="knowledge.knowledgearticle"),
                ),
            ],
            options={
                "verbose_name": "Knowledge Article Version",
                "verbose_name_plural": "Knowledge Article Versions",
                "db_table": "knowledge_article_version",
                "ordering": ("-created_at",),
                "unique_together": {("article", "version")},
            },
        ),
    ]
