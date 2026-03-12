from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog, Role
from apps.settings.services.system_settings_service import get_integration_settings
from apps.settings.utils import get_all_permissions
from core.auth import ldap_client

User = get_user_model()


LDAP_ROLE_SPECS = [
    {
        "name": "一次性检测",
        "description": "访问一次性拨测并创建/管理任务",
        "permissions": [
            "detection.oneoff.view",
            "detection.oneoff.create",
            "detection.oneoff.manage",
        ],
    },
    {
        "name": "拨测申请",
        "description": "提交与维护拨测调度申请",
        "permissions": [
            "detection.schedules.view",
            "detection.schedules.create",
            "detection.schedules.manage",
        ],
    },
]


class LDAPSyncError(Exception):
    """Raised when LDAP sync cannot be completed."""


@dataclass
class LDAPSyncResult:
    total: int
    created: int
    updated: int
    skipped: int
    assigned_roles: int

    def to_dict(self) -> Dict[str, int]:
        return {
            "total": self.total,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "assigned_roles": self.assigned_roles,
        }


def resolve_default_roles() -> List[Role]:
    config = get_integration_settings("ldap")
    if isinstance(config, dict):
        role_ids = config.get("default_role_ids")
        if role_ids:
            roles = list(Role.objects.filter(id__in=role_ids))
            if roles:
                return roles
    return _ensure_builtin_roles()


def _ensure_builtin_roles() -> List[Role]:
    allowed = get_all_permissions()
    ensured: List[Role] = []
    for spec in LDAP_ROLE_SPECS:
        perms = [perm for perm in spec["permissions"] if perm in allowed]
        if not perms:
            continue
        defaults = {
            "description": spec["description"],
            "permissions": perms,
        }
        role, created = Role.objects.get_or_create(name=spec["name"], defaults=defaults)
        if not created:
            updated_fields: List[str] = []
            if sorted(role.permissions or []) != sorted(perms):
                role.permissions = perms
                updated_fields.append("permissions")
            if role.description != spec["description"]:
                role.description = spec["description"]
                updated_fields.append("description")
            if updated_fields:
                role.save(update_fields=updated_fields)
        ensured.append(role)
    return ensured


def assign_default_roles(
    *,
    user: User,
    actor: User | None,
    reason: str,
    ip_address: str | None,
    user_agent: str,
) -> List[Role]:
    roles = resolve_default_roles()
    if not roles:
        return []

    # 单角色模板策略：若用户已绑定角色则不重复分配；否则仅分配一个默认角色。
    if user.roles.exists():
        return []

    role = roles[0]
    user.roles.set([role])
    AuditLog.objects.create(
        actor=actor or user,
        action="user.roles.auto_assign",
        target_type="User",
        target_id=str(user.id),
        metadata={
            "reason": reason,
            "role_ids": [str(role.id)],
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return [role]


def sync_ldap_users(
    *,
    actor: User | None,
    ip_address: str | None,
    user_agent: str,
) -> Dict[str, int]:
    config = get_integration_settings("ldap")
    if not config.get("enabled"):
        raise LDAPSyncError("LDAP 未启用或未配置")

    username_attr = config.get("username_attr") or "uid"
    display_attr = config.get("display_name_attr") or "cn"
    email_attr = config.get("email_attr") or "mail"
    search_filter = config.get("sync_filter") or config.get("user_filter") or "(uid=*)"
    size_limit = config.get("sync_size_limit") or config.get("sync_limit")
    try:
        limit = int(size_limit)
        if limit <= 0:
            limit = None
    except (TypeError, ValueError):
        limit = None

    attributes = sorted({username_attr, display_attr, email_attr})

    try:
        entries = ldap_client.fetch_directory_entries(
            search_filter=search_filter,
            attributes=attributes,
            size_limit=limit,
        )
    except ldap_client.LDAPConfigurationError as exc:
        raise LDAPSyncError(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise LDAPSyncError("LDAP 查询失败，请检查配置") from exc

    stats = LDAPSyncResult(total=len(entries), created=0, updated=0, skipped=0, assigned_roles=0)
    now = timezone.now()

    for entry in entries:
        attr_map = entry["attributes"]
        username_values = attr_map.get(username_attr) or []
        username = (username_values[0] or "").strip() if username_values else ""
        if not username:
            stats.skipped += 1
            continue

        display_values = attr_map.get(display_attr) or []
        email_values = attr_map.get(email_attr) or []
        display_name = (display_values[0] or username).strip()
        email = (email_values[0] or "").strip()

        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(username=username)
                created = False
            except User.DoesNotExist:
                user = User(username=username)
                created = True

            if not created and user.auth_source not in ("ldap", ""):
                stats.skipped += 1
                continue

            changed = False
            if created:
                user.set_unusable_password()
                stats.created += 1
                changed = True
            else:
                stats.updated += 1

            if user.display_name != display_name:
                user.display_name = display_name
                changed = True
            if email and user.email != email:
                user.email = email
                changed = True

            user.auth_source = "ldap"
            user.external_id = entry["dn"]
            user.external_synced_at = now
            if changed:
                user.save()
            else:
                user.save(update_fields=["auth_source", "external_id", "external_synced_at"])

        assigned = assign_default_roles(
            user=user,
            actor=actor,
            reason="ldap_sync",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        stats.assigned_roles += len(assigned)

    AuditLog.objects.create(
        actor=actor,
        action="ldap.sync_users",
        target_type="LDAP",
        target_id="sync",
        metadata=stats.to_dict(),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return stats.to_dict()
