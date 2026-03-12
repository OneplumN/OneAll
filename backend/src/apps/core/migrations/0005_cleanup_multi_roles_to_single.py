from __future__ import annotations

from django.db import migrations


def cleanup_multi_roles_to_single(apps, schema_editor):
    User = apps.get_model("core", "User")

    for user in User.objects.all().prefetch_related("roles"):
        roles = list(user.roles.all().order_by("name", "id"))
        if len(roles) <= 1:
            continue
        user.roles.set([roles[0]])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_user_auth_source"),
    ]

    operations = [
        migrations.RunPython(cleanup_multi_roles_to_single, migrations.RunPython.noop),
    ]

