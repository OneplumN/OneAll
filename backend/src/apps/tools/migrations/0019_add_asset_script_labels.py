from __future__ import annotations

from django.db import migrations

ASSET_REPOSITORY_LABELS = {
    "资产信息 · 域名同步": "assets_sync_domain",
    "资产信息 · Zabbix 主机": "assets_sync_zabbix_host",
    "资产信息 · IPMP 项目": "assets_sync_ipmp_project",
    "资产信息 · 工单主机": "assets_sync_workorder_host",
}


def add_asset_labels_to_tags(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")

    for name, label in ASSET_REPOSITORY_LABELS.items():
        repo = CodeRepository.objects.filter(name=name).first()
        if repo is None:
            continue
        tags = list(repo.tags or [])
        if label in tags:
            continue
        tags.append(label)
        repo.tags = tags
        repo.save(update_fields=["tags", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0018_update_zabbix_assets_script_defaults"),
    ]

    operations = [
        migrations.RunPython(add_asset_labels_to_tags, migrations.RunPython.noop),
    ]
