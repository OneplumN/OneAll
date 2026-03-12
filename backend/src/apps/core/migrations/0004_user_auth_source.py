from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alter_role_options_alter_user_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="auth_source",
            field=models.CharField(default="local", max_length=32),
        ),
        migrations.AddField(
            model_name="user",
            name="external_id",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="user",
            name="external_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
