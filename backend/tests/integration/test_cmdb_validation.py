import pytest

from apps.monitoring.services import cmdb_checker
from apps.assets.models import AssetRecord


@pytest.mark.parametrize(
    'domain,record',
    [
        ('example.com', {'domain': 'example.com', 'status': 'active'}),
        ('demo.internal', {'domain': 'demo.internal', 'status': 'maintenance'}),
    ],
)
@pytest.mark.django_db
def test_cmdb_validation_ok(domain, record):
    AssetRecord.objects.create(
        source=AssetRecord.Source.CMDB,
        external_id=f"domain:{domain}",
        name=domain,
        system_name="OneAll 平台",
        owners=["张三"],
        contacts=["000123"],
        metadata={
            "asset_type": "cmdb-domain",
            "domain": domain,
            "network_type": "internet",
            "owner": "张三",
            "alert_contacts": ["000123"],
            "status": record["status"],
        },
        sync_status="synced",
    )

    result = cmdb_checker.validate_domain(domain)

    assert result.status == cmdb_checker.CMDBValidationStatus.OK
    assert result.record is not None
    assert result.record["domain"] == record["domain"]
    assert result.record["owner"] == "张三"
    assert result.record["contacts"] == ["000123"]


@pytest.mark.django_db
def test_cmdb_validation_not_found():
    result = cmdb_checker.validate_domain('missing.example')

    assert result.status == cmdb_checker.CMDBValidationStatus.NOT_FOUND
    assert result.record is None
    assert '本地资产' in (result.message or '')
