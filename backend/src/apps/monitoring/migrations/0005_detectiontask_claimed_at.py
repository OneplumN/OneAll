from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0004_detectiontask_published_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="detectiontask",
            name="claimed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
