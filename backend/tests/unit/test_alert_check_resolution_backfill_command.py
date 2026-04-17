from __future__ import annotations

import uuid

import pytest
from django.core.management import call_command

from apps.alerts.models import AlertCheck
from apps.assets.models import AssetRecord


@pytest.mark.django_db
def test_backfill_check_resolution_command_updates_existing_checks():
    AssetRecord.objects.create(
        source=AssetRecord.Source.CMDB,
        asset_type="cmdb-domain",
        external_id="domain:pay.demo.oneall.com",
        name="pay.demo.oneall.com",
        system_name="支付平台",
        metadata={
            "asset_type": "cmdb-domain",
            "domain": "pay.demo.oneall.com",
        },
    )
    check = AlertCheck.objects.create(
        name="Payment homepage",
        target="https://pay.demo.oneall.com/health",
        protocol="HTTPS",
        source_type=AlertCheck.SourceType.MONITORING_REQUEST,
        source_id=uuid.uuid4(),
        resolved_domain="",
        resolved_system_name="",
        asset_record_id=None,
        asset_match_status="",
    )

    call_command("backfill_check_resolution", batch_size=50)
    check.refresh_from_db()

    assert check.resolved_domain == "pay.demo.oneall.com"
    assert check.resolved_system_name == "支付平台"
    assert check.asset_match_status == "matched"
    assert check.asset_record_id is not None
