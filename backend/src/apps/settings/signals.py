from __future__ import annotations

from django.db.models.signals import post_migrate
from django.dispatch import receiver

from apps.core.models import Role
from apps.settings.utils import get_all_permissions


@receiver(post_migrate)
def ensure_default_roles(sender, **kwargs):
    if sender.label != "settings":
        return
    all_perms = sorted(get_all_permissions())
    if not all_perms:
        return
    Role.objects.get_or_create(
        name="系统管理员",
        defaults={
            "description": "拥有全部权限，可管理系统参数、探针与集成",
            "permissions": sorted(all_perms),
        },
    )
    readonly_perms = sorted(
        perm for perm in all_perms if perm.endswith(".view") or perm.endswith(".access")
    )
    Role.objects.get_or_create(
        name="只读观察者",
        defaults={
            "description": "仅查看页面和数据，无管理权限",
            "permissions": readonly_perms,
        },
    )
