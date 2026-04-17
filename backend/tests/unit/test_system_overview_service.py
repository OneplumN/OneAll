from __future__ import annotations

import pytest
from django.utils import timezone

from apps.alerts.services import (
    ensure_schedule_for_monitoring_job,
    ensure_schedule_for_probe_schedule,
)
from apps.alerts.services.system_overview_service import build_system_overview
from apps.monitoring.models import DetectionTask, MonitoringJob, MonitoringRequest
from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution


def _create_monitoring_check(
    *,
    title: str,
    target: str,
    resolved_domain: str,
    resolved_system_name: str,
    asset_match_status: str,
):
    request = MonitoringRequest.objects.create(
        title=title,
        target=target,
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
    )
    job = MonitoringJob.objects.create(
        request=request,
        frequency_minutes=5,
        schedule_cron="*/5 * * * *",
        status=MonitoringJob.Status.ACTIVE,
    )
    check = ensure_schedule_for_monitoring_job(job).check
    check.resolved_domain = resolved_domain
    check.resolved_system_name = resolved_system_name
    check.asset_match_status = asset_match_status
    check.save(
        update_fields=[
            "resolved_domain",
            "resolved_system_name",
            "asset_match_status",
            "updated_at",
        ]
    )
    return request, check


def _create_probe_check(
    *,
    name: str,
    target: str,
    resolved_domain: str,
    resolved_system_name: str,
    asset_match_status: str,
):
    probe = ProbeNode.objects.create(
        name=f"{name}-probe",
        location="Shanghai",
        network_type="internal",
        supported_protocols=["HTTPS"],
        status="online",
    )
    schedule = ProbeSchedule.objects.create(
        name=name,
        description="",
        target=target,
        protocol="HTTPS",
        frequency_minutes=5,
        source_type=ProbeSchedule.Source.MANUAL,
        status=ProbeSchedule.Status.ACTIVE,
        start_at=timezone.now(),
    )
    schedule.probes.set([probe])
    check = ensure_schedule_for_probe_schedule(schedule).check
    check.resolved_domain = resolved_domain
    check.resolved_system_name = resolved_system_name
    check.asset_match_status = asset_match_status
    check.save(
        update_fields=[
            "resolved_domain",
            "resolved_system_name",
            "asset_match_status",
            "updated_at",
        ]
    )
    return schedule, probe, check


def _create_detection_result(
    request: MonitoringRequest,
    *,
    status: str,
    minutes_ago: int = 0,
) -> DetectionTask:
    executed_at = timezone.now() - timezone.timedelta(minutes=minutes_ago)
    return DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=status,
        response_time_ms=120,
        status_code="200" if status == DetectionTask.Status.SUCCEEDED else "500",
        error_message="" if status == DetectionTask.Status.SUCCEEDED else "request failed",
        executed_at=executed_at,
        metadata={"request_id": str(request.id)},
    )


def _create_probe_result(
    schedule: ProbeSchedule,
    probe: ProbeNode,
    *,
    status: str,
    minutes_ago: int = 0,
) -> ProbeScheduleExecution:
    scheduled_at = timezone.now() - timezone.timedelta(minutes=minutes_ago)
    return ProbeScheduleExecution.objects.create(
        schedule=schedule,
        probe=probe,
        scheduled_at=scheduled_at,
        finished_at=scheduled_at,
        status=status,
        response_time_ms=150,
        status_code="200" if status == ProbeScheduleExecution.Status.SUCCEEDED else "500",
        message="" if status == ProbeScheduleExecution.Status.SUCCEEDED else "request failed",
    )


@pytest.mark.django_db
def test_build_system_overview_marks_system_success_when_latest_monitoring_result_is_healthy():
    request, _ = _create_monitoring_check(
        title="Payment domain",
        target="https://pay.demo.oneall.com/health",
        resolved_domain="pay.demo.oneall.com",
        resolved_system_name="支付平台",
        asset_match_status="matched",
    )
    _create_detection_result(request, status=DetectionTask.Status.SUCCEEDED)

    payload = build_system_overview()

    systems = {entry["system_name"]: entry for entry in payload["systems"]}
    assert systems["支付平台"]["status"] == "success"
    assert systems["支付平台"]["domain_count"] == 1
    assert systems["支付平台"]["abnormal_count"] == 0


@pytest.mark.django_db
def test_build_system_overview_marks_system_danger_when_latest_probe_result_is_abnormal():
    healthy_request, _ = _create_monitoring_check(
        title="Payment domain",
        target="https://pay.demo.oneall.com/health",
        resolved_domain="pay.demo.oneall.com",
        resolved_system_name="支付平台",
        asset_match_status="matched",
    )
    _create_detection_result(healthy_request, status=DetectionTask.Status.SUCCEEDED, minutes_ago=1)
    schedule, probe, _ = _create_probe_check(
        name="Gateway probe",
        target="https://gateway.demo.oneall.com/health",
        resolved_domain="gateway.demo.oneall.com",
        resolved_system_name="支付平台",
        asset_match_status="matched",
    )
    _create_probe_result(schedule, probe, status=ProbeScheduleExecution.Status.FAILED)

    payload = build_system_overview()

    systems = {entry["system_name"]: entry for entry in payload["systems"]}
    assert systems["支付平台"]["status"] == "danger"
    assert systems["支付平台"]["abnormal_count"] == 1


@pytest.mark.django_db
def test_build_system_overview_marks_system_idle_when_no_latest_result_exists():
    _create_monitoring_check(
        title="Portal domain",
        target="https://portal.demo.oneall.com/health",
        resolved_domain="portal.demo.oneall.com",
        resolved_system_name="门户平台",
        asset_match_status="matched",
    )

    payload = build_system_overview()

    systems = {entry["system_name"]: entry for entry in payload["systems"]}
    assert systems["门户平台"]["status"] == "idle"
    assert systems["门户平台"]["last_checked_at"] is None


@pytest.mark.django_db
def test_build_system_overview_groups_missing_system_checks_into_missing_system_bucket():
    request, _ = _create_monitoring_check(
        title="Billing domain",
        target="https://billing.demo.oneall.com/health",
        resolved_domain="billing.demo.oneall.com",
        resolved_system_name="",
        asset_match_status="missing_system",
    )
    _create_detection_result(request, status=DetectionTask.Status.SUCCEEDED)

    payload = build_system_overview()

    systems = {entry["system_name"]: entry for entry in payload["systems"]}
    assert systems["未配置系统"]["status"] == "success"
    assert payload["items"][0]["system_name"] == "未配置系统"


@pytest.mark.django_db
def test_build_system_overview_groups_unmanaged_and_invalid_targets_into_unmanaged_bucket():
    unmanaged_request, _ = _create_monitoring_check(
        title="Unknown domain",
        target="https://unknown.demo.oneall.com/health",
        resolved_domain="unknown.demo.oneall.com",
        resolved_system_name="",
        asset_match_status="unmanaged",
    )
    invalid_request, _ = _create_monitoring_check(
        title="IP target",
        target="https://10.10.10.10/health",
        resolved_domain="",
        resolved_system_name="",
        asset_match_status="invalid_target",
    )
    _create_detection_result(unmanaged_request, status=DetectionTask.Status.FAILED)
    DetectionTask.objects.create(
        target=invalid_request.target,
        protocol=invalid_request.protocol,
        status=DetectionTask.Status.SCHEDULED,
        metadata={"request_id": str(invalid_request.id)},
    )

    payload = build_system_overview()

    systems = {entry["system_name"]: entry for entry in payload["systems"]}
    assert systems["未纳管域名"]["status"] == "danger"
    assert systems["未纳管域名"]["domain_count"] == 2
    unmanaged_items = [item for item in payload["items"] if item["system_name"] == "未纳管域名"]
    assert len(unmanaged_items) == 2


@pytest.mark.django_db
def test_build_system_overview_ignores_monitoring_derived_probe_schedule_duplicates():
    request = MonitoringRequest.objects.create(
        title="Payment homepage",
        target="https://pay.demo.oneall.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
        metadata={"system_name": "支付平台"},
    )
    job = MonitoringJob.objects.create(
        request=request,
        frequency_minutes=5,
        schedule_cron="*/5 * * * *",
        status=MonitoringJob.Status.ACTIVE,
    )
    monitoring_check = ensure_schedule_for_monitoring_job(job).check
    monitoring_check.resolved_domain = "pay.demo.oneall.com"
    monitoring_check.resolved_system_name = "支付平台"
    monitoring_check.asset_match_status = "matched"
    monitoring_check.save(
        update_fields=["resolved_domain", "resolved_system_name", "asset_match_status", "updated_at"]
    )

    probe = ProbeNode.objects.create(
        name="derived-probe",
        location="Shanghai",
        network_type="internal",
        supported_protocols=["HTTPS"],
        status="online",
    )
    derived_schedule = ProbeSchedule.objects.create(
        monitoring_request=request,
        monitoring_job=job,
        name="Payment homepage",
        description="",
        target=request.target,
        protocol="HTTPS",
        frequency_minutes=5,
        metadata=dict(request.metadata or {}),
        source_type=ProbeSchedule.Source.MONITORING_REQUEST,
        source_id=request.id,
        status=ProbeSchedule.Status.ACTIVE,
    )
    derived_schedule.probes.set([probe])
    derived_check = ensure_schedule_for_probe_schedule(derived_schedule).check
    derived_check.resolved_domain = "pay.demo.oneall.com"
    derived_check.resolved_system_name = "支付平台"
    derived_check.asset_match_status = "matched"
    derived_check.save(
        update_fields=["resolved_domain", "resolved_system_name", "asset_match_status", "updated_at"]
    )

    _create_detection_result(request, status=DetectionTask.Status.SUCCEEDED)
    _create_probe_result(derived_schedule, probe, status=ProbeScheduleExecution.Status.SUCCEEDED)

    payload = build_system_overview()

    systems = {entry["system_name"]: entry for entry in payload["systems"]}
    assert systems["支付平台"]["matched_strategy_count"] == 1
    assert len(payload["items"]) == 1
