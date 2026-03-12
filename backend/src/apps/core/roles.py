from __future__ import annotations

from typing import Any


def get_primary_role(user: Any):
    """Return the single effective role for a user.

    one-pro 约束：用户最多绑定一个角色模板；历史多角色数据按 name/id 排序取第一个作为保留项。
    """

    roles_manager = getattr(user, "roles", None)
    if not roles_manager or not hasattr(roles_manager, "order_by"):
        return None
    return roles_manager.order_by("name", "id").first()

