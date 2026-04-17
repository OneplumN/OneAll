from __future__ import annotations

from typing import Any

import pytest
from django.utils import timezone

from apps.assets.models import AssetRecord
from apps.assets.services.conflict_resolver import AssetConflictResolver


@pytest.mark.django_db
def test_resolve_marks_canonical_conflicts() -> None:
    """当存在相同 asset_type + canonical_key 的多条记录时，后续记录应被标记为 conflict。"""

    now = timezone.now()

    other = AssetRecord.objects.create(
        source=AssetRecord.Source.MANUAL,
        asset_type="cmdb-domain",
        canonical_key="oneall.cn",
        external_id="manual:oneall.cn",
        name="oneall.cn",
        system_name="ONEALL-SERVICE",
        metadata={"asset_type": "cmdb-domain", "domain": "oneall.cn"},
        sync_status="synced",
        synced_at=now,
    )

    anchor = AssetRecord.objects.create(
        source=AssetRecord.Source.CMDB,
        asset_type="cmdb-domain",
        canonical_key="oneall.cn",
        external_id="domain:oneall.cn",
        name="oneall.cn",
        system_name="ONEALL-SERVICE",
        metadata={"asset_type": "cmdb-domain", "domain": "oneall.cn"},
        sync_status="synced",
        synced_at=now + timezone.timedelta(minutes=5),
    )

    resolver = AssetConflictResolver()
    summary: dict[str, Any] = resolver.resolve()

    anchor.refresh_from_db()
    other.refresh_from_db()

    # anchor 保持原状态，其他记录被标记为 conflict
    assert anchor.sync_status == "synced"
    assert other.sync_status == "conflict"

    # 冲突日志中包含 canonical_duplicate 信息
    log = (other.metadata or {}).get("conflict_log") or []
    assert isinstance(log, list) and log, "conflict_log 应包含至少一条记录"
    last_entry = log[-1]
    assert last_entry.get("type") == "canonical_duplicate"
    assert last_entry.get("asset_type") == "cmdb-domain"
    assert last_entry.get("canonical_key") == "oneall.cn"
    assert str(anchor.id) in (last_entry.get("anchor") or "")

    # 汇总信息中包含 canonical_conflicts 计数
    assert summary["canonical_conflicts"] >= 1
    assert summary["conflicts"] >= summary["canonical_conflicts"]
