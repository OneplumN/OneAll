from __future__ import annotations

import pytest

from apps.assets.models import AssetSource, AssetSyncRun


@pytest.mark.django_db
def test_create_asset_source_minimal():
    source = AssetSource.objects.create(
        key="zabbix",
        name="Zabbix 主机资产",
        type=AssetSource.Type.MONITORING,
        is_enabled=False,
        config={"endpoint": "http://zabbix.example.com/api_jsonrpc.php"},
    )

    assert source.id is not None
    assert source.key == "zabbix"
    assert source.type == AssetSource.Type.MONITORING
    assert source.config["endpoint"].startswith("http://")


@pytest.mark.django_db
def test_assetsyncrun_can_reference_asset_source():
    source = AssetSource.objects.create(
        key="ipmp",
        name="IPMP 项目资产",
        type=AssetSource.Type.CMDB,
        is_enabled=True,
    )
    run = AssetSyncRun.objects.create(
        source=source,
        mode=AssetSyncRun.Mode.SYNC,
    )

    assert run.source == source
    # 反向关系也可用，便于后续按 Source 查询同步历史
    assert run in source.sync_runs.all()

