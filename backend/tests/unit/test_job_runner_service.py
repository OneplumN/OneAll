from datetime import timedelta

import pytest
from django.utils import timezone

from apps.monitoring.models import DetectionTask, MonitoringJob, MonitoringRequest
from apps.monitoring.services.job_runner_service import enqueue_due_jobs
from apps.probes.models import ProbeNode


@pytest.mark.django_db
def test_enqueue_due_jobs_creates_detection_tasks():
    probe = ProbeNode.objects.create(
        name="probe-auto",
        location="hz-idc",
        network_type="external",
        status="online",
        supported_protocols=["HTTP"],
    )
    monitoring_request = MonitoringRequest.objects.create(
        title="API 可用性",
        target="https://status.example.com",
        protocol="HTTPS",
        frequency_minutes=5,
        metadata={
            "probe_ids": [str(probe.id)],
            "expected_status_codes": [200],
            "timeout_seconds": 20,
        },
    )
    now = timezone.now()
    job = MonitoringJob.objects.create(
        request=monitoring_request,
        frequency_minutes=5,
        status=MonitoringJob.Status.ACTIVE,
        next_run_at=now - timedelta(minutes=1),
    )
    previous_next = job.next_run_at

    jobs_processed, created = enqueue_due_jobs(now=now)

    assert jobs_processed == 1
    assert created == 1
    detection = DetectionTask.objects.get()
    assert detection.probe_id == probe.id
    assert detection.metadata["job_id"] == str(job.id)
    assert detection.metadata["expect_status"] == 200
    assert detection.metadata["alert_threshold"] == 1
    job.refresh_from_db()
    assert job.last_run_at == now
    assert job.next_run_at == previous_next + timedelta(minutes=5)


@pytest.mark.django_db
def test_enqueue_due_jobs_skips_offline_probes():
    offline_probe = ProbeNode.objects.create(
        name="probe-offline",
        location="bj-idc",
        network_type="external",
        status="offline",
        supported_protocols=["HTTP"],
    )
    online_probe = ProbeNode.objects.create(
        name="probe-online",
        location="sh-idc",
        network_type="external",
        status="online",
        supported_protocols=["HTTP"],
    )
    monitoring_request = MonitoringRequest.objects.create(
        title="外网拨测",
        target="https://portal.example.com",
        protocol="HTTPS",
        frequency_minutes=10,
        metadata={
            "probe_ids": [str(offline_probe.id), str(online_probe.id)],
            "expected_status_codes": [200, 204],
        },
    )
    now = timezone.now()
    job = MonitoringJob.objects.create(
        request=monitoring_request,
        frequency_minutes=10,
        status=MonitoringJob.Status.ACTIVE,
        next_run_at=now - timedelta(minutes=2),
    )
    previous_next = job.next_run_at

    jobs_processed, created = enqueue_due_jobs(now=now)

    assert jobs_processed == 1
    assert created == 1
    detection = DetectionTask.objects.get()
    assert detection.probe_id == online_probe.id
    assert detection.metadata["expected_status_codes"] == [200, 204]
    assert detection.metadata["expect_status"] == 200
    job.refresh_from_db()
    assert job.last_run_at == now
    assert job.next_run_at == previous_next + timedelta(minutes=10)
