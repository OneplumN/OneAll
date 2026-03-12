import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0009_reset_script_channel_config"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlertTemplate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("channel_type", models.CharField(max_length=32)),
                ("name", models.CharField(max_length=64)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("subject", models.CharField(blank=True, max_length=200)),
                ("body", models.TextField()),
                ("is_default", models.BooleanField(default=False)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="alerttemplate_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="alerttemplate_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "settings_alert_template",
                "ordering": ("channel_type", "-is_default", "name"),
            },
        ),
        migrations.AlterUniqueTogether(
            name="alerttemplate",
            unique_together={("channel_type", "name")},
        ),
    ]
