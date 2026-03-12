from __future__ import annotations

from django.db import migrations
from django.utils import timezone


def seed_code_repositories(apps, schema_editor):
    CodeDirectory = apps.get_model("tools", "CodeDirectory")
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")

    assets_dir, _ = CodeDirectory.objects.update_or_create(
        key="assets",
        defaults={
            "title": "资产信息",
            "description": "资产同步与巡检脚本目录",
            "keywords": ["资产", "domain", "zabbix", "ipmp", "工单"],
            "builtin": True,
        },
    )

    scripts = [
        {
            "name": "资产信息 · 域名同步",
            "language": "python",
            "tags": ["资产", "域名"],
            "description": "同步 CMDB 域名并校验负责人映射。",
            "content": "def sync_domains():\n    pass",
        },
        {
            "name": "资产信息 · Zabbix 主机",
            "language": "python",
            "tags": ["资产", "zabbix"],
            "description": "同步 Zabbix 主机与 Proxy 映射关系。",
            "content": "def sync_zabbix_hosts():\n    pass",
        },
        {
            "name": "资产信息 · IPMP 项目",
            "language": "python",
            "tags": ["资产", "ipmp"],
            "description": "同步 IPMP 项目元数据并补齐归属信息。",
            "content": "def sync_ipmp_projects():\n    pass",
        },
        {
            "name": "资产信息 · 工单主机",
            "language": "python",
            "tags": ["资产", "工单"],
            "description": "同步工单纳管主机并更新告警联系人。",
            "content": "def sync_workorder_hosts():\n    pass",
        },
    ]

    for script in scripts:
        repo, created = CodeRepository.objects.update_or_create(
            name=script["name"],
            defaults={
                "language": script["language"],
                "tags": script["tags"],
                "description": script["description"],
                "directory": assets_dir,
                "content": script["content"],
                "updated_at": timezone.now(),
            },
        )
        version, _ = CodeRepositoryVersion.objects.get_or_create(
            repository=repo,
            version="v1.0.0",
            defaults={
                "summary": "初始化脚本",
                "change_log": "初始化版本",
                "content": script["content"],
            },
        )
        repo.latest_version = version
        repo.save(update_fields=["latest_version"])


def remove_seed(apps, schema_editor):
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeDirectory = apps.get_model("tools", "CodeDirectory")
    CodeRepository.objects.filter(name__startswith="资产信息 ·").delete()
    CodeDirectory.objects.filter(key="assets").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0002_code_repository_models"),
    ]

    operations = [
        migrations.RunPython(seed_code_repositories, remove_seed),
    ]
