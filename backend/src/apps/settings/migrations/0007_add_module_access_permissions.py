from django.db import migrations


def add_module_access_permissions(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    for role in Role.objects.all():
        perms = role.permissions or []
        perm_set = set(perms)
        modules = {perm.split(".")[0] for perm in perms if "." in perm}
        changed = False
        for module_key in modules:
            access_perm = f"{module_key}.module.access"
            if access_perm not in perm_set:
                perm_set.add(access_perm)
                changed = True
        if changed:
            role.permissions = sorted(perm_set)
            role.save(update_fields=["permissions"])


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0006_alertchannel"),
    ]

    operations = [
        migrations.RunPython(add_module_access_permissions, migrations.RunPython.noop),
    ]
