from __future__ import annotations

import copy

from apps.settings.constants import AVAILABLE_PERMISSIONS


def build_permission_catalog():
    return copy.deepcopy(AVAILABLE_PERMISSIONS)


def flatten_permissions(catalog):
    entries: set[str] = set()
    for module in catalog:
        module_key = module["key"]
        for child in module.get("children", []):
            child_key = child["key"]
            for action in child.get("actions", []):
                entries.add(f"{module_key}.{child_key}.{action}")
    return entries


def get_all_permissions() -> set[str]:
    return flatten_permissions(build_permission_catalog())
