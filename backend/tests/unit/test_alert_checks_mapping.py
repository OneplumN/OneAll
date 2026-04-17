from __future__ import annotations

import pytest
from django.utils import timezone

from apps.alerts.models import AlertCheck, AlertSchedule
from apps.alerts.services import (
    ensure_check_for_monitoring_request,
    ensure_schedule_for_monitoring_job,
    ensure_schedule_for_probe_schedule,
)
from apps.monitoring.services.monitoring_job_service import create_job_for_request
from apps.monitoring.models import MonitoringJob, MonitoringRequest
from apps.probes.models import ProbeNode, ProbeSchedule


@pytest.mark.django_db
def test_monitoring_request_creates_alert_check():
    request = MonitoringRequest.objects.create(
        title="Homepage",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
    )

    check = ensure_check_for_monitoring_request(request)

    assert AlertCheck.objects.count() == 1
    assert check.name == request.title
    assert check.target == request.target
    assert check.protocol == request.protocol
    assert check.source_type == AlertCheck.SourceType.MONITORING_REQUEST
    assert check.source_id == request.id


@pytest.mark.django_db
def test_monitoring_job_creates_alert_schedule_and_syncs_changes():
    request = MonitoringRequest.objects.create(
        title="Job request",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=10,
    )
    job = MonitoringJob.objects.create(
        request=request,
        frequency_minutes=10,
        schedule_cron="*/10 * * * *",
        status=MonitoringJob.Status.ACTIVE,
    )

    result = ensure_schedule_for_monitoring_job(job)

    assert result.check is not None
    assert result.schedule is not None
    schedule = result.schedule
    assert schedule.alert_check_id == result.check.id
    assert schedule.frequency_minutes == job.frequency_minutes
    assert schedule.cron_expression == job.schedule_cron
    assert schedule.status == AlertSchedule.Status.ACTIVE

    # Update job and ensure schedule is synced
    job.frequency_minutes = 20
    job.status = MonitoringJob.Status.PAUSED
    job.last_run_at = timezone.now()
    job.next_run_at = timezone.now()
    job.metadata = {"foo": "bar"}
    job.save()

    updated = ensure_schedule_for_monitoring_job(job).schedule
    assert updated.frequency_minutes == 20
    assert updated.status == AlertSchedule.Status.PAUSED
    assert updated.last_run_at == job.last_run_at
    assert updated.next_run_at == job.next_run_at
    assert updated.metadata == job.metadata


@pytest.mark.django_db
def test_create_job_for_request_initializes_metadata_and_next_run():
    probe = ProbeNode.objects.create(
        name="job-probe",
        location="Shanghai",
        network_type="internal",
        supported_protocols=["HTTPS"],
        status="online",
    )
    request = MonitoringRequest.objects.create(
        title="Approved request",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
        metadata={
            "probe_ids": [str(probe.id)],
            "alert_threshold": 2,
            "alert_contacts": ["ops@example.com"],
        },
    )

    before = timezone.now()
    job = create_job_for_request(request)

    assert job.metadata == request.metadata
    assert job.next_run_at is not None
    assert job.next_run_at >= before


@pytest.mark.django_db
def test_probe_schedule_creates_alert_check_and_schedule():
    schedule = ProbeSchedule.objects.create(
        name="Probe check",
        description="test",
        target="https://probe.example.com/ping",
        protocol="HTTPS",
        frequency_minutes=3,
    )

    result = ensure_schedule_for_probe_schedule(schedule)
    check = result.check
    alert_schedule = result.schedule

    assert check is not None
    assert check.source_type == AlertCheck.SourceType.PROBE_SCHEDULE
    assert check.source_id == schedule.id
    assert check.target == schedule.target
    assert check.protocol == schedule.protocol

    assert alert_schedule is not None
    assert alert_schedule.alert_check_id == check.id
    assert alert_schedule.frequency_minutes == schedule.frequency_minutes
    assert alert_schedule.status == AlertSchedule.Status.ACTIVE

    # Update schedule and verify sync
    schedule.frequency_minutes = 7
    schedule.status = ProbeSchedule.Status.PAUSED
    schedule.last_run_at = timezone.now()
    schedule.next_run_at = timezone.now()
    schedule.metadata = {"threshold": 3}
    schedule.save()

    updated = ensure_schedule_for_probe_schedule(schedule).schedule
    assert updated.frequency_minutes == 7
    assert updated.status == AlertSchedule.Status.PAUSED
    assert updated.last_run_at == schedule.last_run_at
    assert updated.next_run_at == schedule.next_run_at
    assert updated.metadata == schedule.metadata
