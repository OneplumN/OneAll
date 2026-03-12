from django.db import migrations


def reset_script_config(apps, schema_editor):
    AlertChannel = apps.get_model("settings", "AlertChannel")
    try:
        channel = AlertChannel.objects.get(channel_type="script")
    except AlertChannel.DoesNotExist:
        return
    channel.config = {}
    channel.save(update_fields=["config"])


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0008_cleanup_integration_permissions"),
    ]

    operations = [
        migrations.RunPython(reset_script_config, migrations.RunPython.noop),
    ]
