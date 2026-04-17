from __future__ import annotations

import uuid

import pytest

from apps.alerts.models import AlertCheck
from apps.alerts.services import ensure_check_for_monitoring_request, ensure_check_for_probe_schedule
from apps.alerts.services.check_target_resolution_service import apply_resolution_snapshot
from apps.assets.models import AssetRecord
from apps.monitoring.models import MonitoringRequest
from apps.probes.models import ProbeSchedule


def _create_domain_asset(domain: str, *, system_name: str = "支付平台") -> AssetRecord:
    return AssetRecord.objects.create(
        source=AssetRecord.Source.CMDB,
        asset_type="cmdb-domain",
        external_id=f"domain:{domain}",
        name=domain,
        system_name=system_name,
        metadata={
            "asset_type": "cmdb-domain",
            "domain": domain,
        },
    )


@pytest.mark.django_db
def test_monitoring_request_check_applies_resolution_snapshot_for_url_target():
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
    request = MonitoringRequest.objects.create(
        title="Payment homepage",
        target="https://pay.demo.oneall.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
    )

    check = ensure_check_for_monitoring_request(request)

    assert check.resolved_domain == "pay.demo.oneall.com"
    assert check.resolved_system_name == "支付平台"
    assert check.asset_match_status == "matched"
    assert check.asset_record_id is not None


@pytest.mark.django_db
def test_apply_resolution_snapshot_resolves_bare_domain_target():
    _create_domain_asset("ops.demo.oneall.com", system_name="运维平台")
    check = AlertCheck.objects.create(
        name="Ops domain",
        target="OPS.DEMO.ONEALL.COM",
        protocol="HTTPS",
        source_type=AlertCheck.SourceType.AD_HOC,
        source_id=uuid.uuid4(),
    )

    apply_resolution_snapshot(check)
    check.refresh_from_db()

    assert check.resolved_domain == "ops.demo.oneall.com"
    assert check.resolved_system_name == "运维平台"
    assert check.asset_match_status == "matched"


@pytest.mark.django_db
def test_apply_resolution_snapshot_marks_missing_system_when_asset_has_no_system_name():
    _create_domain_asset("billing.demo.oneall.com", system_name="")
    check = AlertCheck.objects.create(
        name="Billing domain",
        target="https://billing.demo.oneall.com/status",
        protocol="HTTPS",
        source_type=AlertCheck.SourceType.AD_HOC,
        source_id=uuid.uuid4(),
    )

    apply_resolution_snapshot(check)
    check.refresh_from_db()

    assert check.resolved_domain == "billing.demo.oneall.com"
    assert check.resolved_system_name == ""
    assert check.asset_match_status == "missing_system"
    assert check.asset_record_id is not None


@pytest.mark.django_db
def test_apply_resolution_snapshot_marks_unmanaged_domain_when_no_asset_matches():
    check = AlertCheck.objects.create(
        name="Unmanaged domain",
        target="https://unknown.demo.oneall.com/status",
        protocol="HTTPS",
        source_type=AlertCheck.SourceType.AD_HOC,
        source_id=uuid.uuid4(),
    )

    apply_resolution_snapshot(check)
    check.refresh_from_db()

    assert check.resolved_domain == "unknown.demo.oneall.com"
    assert check.resolved_system_name == ""
    assert check.asset_match_status == "unmanaged"
    assert check.asset_record_id is None


@pytest.mark.django_db
def test_apply_resolution_snapshot_marks_invalid_target_for_ip_address():
    check = AlertCheck.objects.create(
        name="IP target",
        target="https://10.10.10.10:8443/health",
        protocol="HTTPS",
        source_type=AlertCheck.SourceType.AD_HOC,
        source_id=uuid.uuid4(),
    )

    apply_resolution_snapshot(check)
    check.refresh_from_db()

    assert check.resolved_domain == ""
    assert check.resolved_system_name == ""
    assert check.asset_match_status == "invalid_target"
    assert check.asset_record_id is None


@pytest.mark.django_db
def test_probe_schedule_resolution_snapshot_refreshes_when_target_changes():
    _create_domain_asset("cert.demo.oneall.com", system_name="证书平台")
    _create_domain_asset("gateway.demo.oneall.com", system_name="网关平台")
    schedule = ProbeSchedule.objects.create(
        name="Certificate monitor",
        description="test",
        target="https://cert.demo.oneall.com",
        protocol="HTTPS",
        frequency_minutes=5,
    )

    check = ensure_check_for_probe_schedule(schedule)
    assert check.resolved_domain == "cert.demo.oneall.com"
    assert check.resolved_system_name == "证书平台"
    assert check.asset_match_status == "matched"

    schedule.target = "https://gateway.demo.oneall.com"
    schedule.save(update_fields=["target", "updated_at"])

    updated_check = ensure_check_for_probe_schedule(schedule)
    assert updated_check.resolved_domain == "gateway.demo.oneall.com"
    assert updated_check.resolved_system_name == "网关平台"
    assert updated_check.asset_match_status == "matched"
