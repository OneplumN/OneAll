from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge", "0002_alter_knowledgearticle_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("key", models.SlugField(max_length=80, unique=True)),
                ("title", models.CharField(max_length=120)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("builtin", models.BooleanField(default=False)),
                ("display_order", models.PositiveIntegerField(default=0)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Knowledge Category",
                "verbose_name_plural": "Knowledge Categories",
                "db_table": "knowledge_category",
                "ordering": ("display_order", "title"),
            },
        ),
    ]
