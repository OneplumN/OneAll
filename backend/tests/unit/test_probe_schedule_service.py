from __future__ import annotations

import pytest

from apps.monitoring.models import MonitoringJob, MonitoringRequest
from apps.probes.api.serializers import ProbeScheduleSerializer
from apps.probes.models import ProbeNode
from apps.probes.services import probe_schedule_service


@pytest.mark.django_db
def test_sync_schedule_from_job_creates_schedule():
    probe = ProbeNode.objects.create(
        name="schedule-probe",
        location="Shanghai",
        network_type="internal",
        supported_protocols=["HTTPS"],
    )
    request = MonitoringRequest.objects.create(
        title="监控申请",
        target="https://example.com",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
        metadata={
            "probe_ids": [str(probe.id)],
            "expected_status_codes": [200],
        },
    )
    job = MonitoringJob.objects.create(request=request, frequency_minutes=3, status=MonitoringJob.Status.ACTIVE)

    schedule = probe_schedule_service.sync_schedule_from_job(job)

    assert schedule.monitoring_request == request
    assert schedule.monitoring_job == job
    assert schedule.frequency_minutes == 3
    assert schedule.probes.count() == 1
    assert schedule.probes.first().id == probe.id
    assert schedule.source_type == schedule.Source.MONITORING_REQUEST


@pytest.mark.django_db
def test_update_schedule_runtime_updates_timestamps():
    request = MonitoringRequest.objects.create(
        title="monitor",
        target="https://example.org",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
    )
    job = MonitoringJob.objects.create(request=request, frequency_minutes=5, status=MonitoringJob.Status.ACTIVE)
    schedule = probe_schedule_service.sync_schedule_from_job(job)
    last_run = schedule.updated_at
    next_run = schedule.updated_at

    probe_schedule_service.update_schedule_runtime(job, last_run_at=last_run, next_run_at=next_run)
    schedule.refresh_from_db()

    assert schedule.last_run_at == last_run
    assert schedule.next_run_at == next_run


@pytest.mark.django_db
def test_manual_schedule_defaults_next_run_at_creation():
    probe = ProbeNode.objects.create(
        name="manual-probe",
        location="Beijing",
        network_type="internal",
        supported_protocols=["HTTPS"],
    )
    payload = {
        "name": "自建调度",
        "target": "https://internal.example.com",
        "protocol": "HTTPS",
        "frequency_minutes": 10,
        "probe_ids": [probe.id],
        "description": ""
    }
    serializer = ProbeScheduleSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    schedule = serializer.save(source_type="manual", status="active", metadata={})
    assert schedule.start_at is not None
    assert schedule.next_run_at == schedule.start_at
