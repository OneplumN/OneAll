from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0003_alter_detectiontask_created_by_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="detectiontask",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
