from django.db import migrations


MAPPING = {
    "integrations.overview.view": "integrations.hub.view",
    "integrations.plugins.view": "integrations.hub.view",
    "integrations.plugins.toggle": "integrations.hub.toggle",
    "integrations.plugins.configure": "integrations.hub.configure",
}

PREFIXES = ("integrations.plugin_",)


def migrate_permissions(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    for role in Role.objects.all():
        perms = role.permissions or []
        changed = False
        result: set[str] = set()
        for perm in perms:
            if perm.startswith(PREFIXES):
                changed = True
                continue
            mapped = MAPPING.get(perm)
            if mapped:
                result.add(mapped)
                changed = True
            else:
                result.add(perm)
        if changed:
            role.permissions = sorted(result)
            role.save(update_fields=["permissions"])


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0007_add_module_access_permissions"),
    ]

    operations = [
        migrations.RunPython(migrate_permissions, migrations.RunPython.noop),
    ]
