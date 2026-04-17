from __future__ import annotations

from typing import Any, Dict

import pytest

from apps.assets.models import AssetRecord
from apps.assets.services import sync_service


@pytest.mark.django_db
def test_ingest_asset_snapshot_respects_unique_fields_override(monkeypatch) -> None:
    """当 SystemSettings.integrations 覆盖唯一字段时，应按覆盖规则生成 canonical_key。"""

    def fake_get_integration_settings(section: str) -> Dict[str, Any]:
        if section != "assets":
            return {}
        return {
            "types": {
                # 默认 cmdb-domain 使用 domain 字段，这里改为优先使用 system_name
                "cmdb-domain": {"unique_fields": ["system_name", "domain"]},
            }
        }

    monkeypatch.setattr(sync_service, "get_integration_settings", fake_get_integration_settings)

    records: list[Dict[str, Any]] = [
        {
            "source": "CMDB",
            "external_id": "domain:OneAll.cn",
            "name": "OneAll.cn",
            "system_name": "ONEALL-SERVICE",
            "metadata": {
                "asset_type": "cmdb-domain",
                "domain": "OneAll.cn",
            },
        }
    ]

    stats = sync_service.ingest_asset_snapshot(records, plugin="asset_cmdb_domain", full_snapshot=False, run=None)
    assert stats["created"] == 1

    stored = AssetRecord.objects.get(source="CMDB", external_id="domain:OneAll.cn")
    # asset_type 应按元数据识别
    assert stored.asset_type == "cmdb-domain"
    # canonical_key 应优先使用 system_name，并做小写归一化
    assert stored.canonical_key == "oneall-service"

