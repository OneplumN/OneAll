from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.core.roles import get_primary_role

PERMISSION_ALIASES: dict[str, str] = {
    "detection.oneoff.execute": "detection.oneoff.create",
    "detection.oneoff.manage_templates": "detection.oneoff.manage",
    "detection.schedules.submit": "detection.schedules.create",
    "detection.schedules.approve": "detection.schedules.manage",
    "probes.nodes.update": "probes.nodes.manage",
    "probes.nodes.rotate_token": "probes.nodes.manage",
    "assets.records.sync": "assets.records.manage",
    "assets.records.export": "assets.records.view",
    "tools.library.execute": "tools.library.manage",
    "tools.repository.commit": "tools.repository.create",
    "tools.repository.rollback": "tools.repository.manage",
    "settings.system.update": "settings.system.manage",
    "settings.users.assign_roles": "settings.users.manage",
    "settings.users.sync": "settings.users.manage",
    "settings.roles.update": "settings.roles.manage",
    "settings.roles.delete": "settings.roles.manage",
    "settings.audit_log.export": "settings.audit_log.manage",
}


def get_user_permissions(user) -> set[str]:
    perms = set()
    role = get_primary_role(user)
    if not role:
        return perms
    perms.update(role.permissions or [])
    if not perms:
        return perms
    expanded = _apply_aliases(perms)
    expanded = _apply_hierarchy(expanded)
    return expanded


def _apply_aliases(perms: set[str]) -> set[str]:
    expanded = set(perms)
    for perm in perms:
        alias = PERMISSION_ALIASES.get(perm)
        if alias:
            expanded.add(alias)
    return expanded


def _apply_hierarchy(perms: set[str]) -> set[str]:
    expanded = set(perms)
    for perm in list(perms):
        prefix, sep, action = perm.rpartition(".")
        if not sep:
            continue
        if action == "manage":
            expanded.add(f"{prefix}.create")
            expanded.add(f"{prefix}.view")
        elif action == "create":
            expanded.add(f"{prefix}.view")
    return expanded


class HasPermission(BasePermission):
    permission_code: str = ""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not self.permission_code:
            return False
        return self.permission_code in get_user_permissions(user)


def RequirePermission(permission: str):
    class _Permission(HasPermission):
        permission_code = permission

    return _Permission


def RequireAnyPermission(*permissions: str):
    class _Permission(BasePermission):
        permission_codes = tuple(permission for permission in permissions if permission)

        def has_permission(self, request, view):
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated or not self.permission_codes:
                return False
            user_permissions = get_user_permissions(user)
            return any(permission in user_permissions for permission in self.permission_codes)

    return _Permission
