from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode, ProbeSchedule
from apps.probes.services import manual_schedule_runner


@pytest.mark.django_db
def test_run_due_manual_schedules_creates_tasks():
    now = timezone.now()
    probe = ProbeNode.objects.create(
        name="manual-probe",
        location="广州",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    schedule = ProbeSchedule.objects.create(
        name="站点拨测",
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        frequency_minutes=5,
        status=ProbeSchedule.Status.ACTIVE,
        source_type=ProbeSchedule.Source.MANUAL,
        next_run_at=now - timedelta(minutes=1),
    )
    schedule.probes.add(probe)
    previous_next = schedule.next_run_at

    processed, created = manual_schedule_runner.run_due_manual_schedules(now=now)

    assert processed == 1
    assert created == 1
    detection = DetectionTask.objects.get()
    assert detection.metadata["schedule_id"] == str(schedule.id)
    schedule.refresh_from_db()
    assert schedule.next_run_at == previous_next + timedelta(minutes=5)


@pytest.mark.django_db
def test_run_due_manual_schedules_skips_without_probes():
    now = timezone.now()
    schedule = ProbeSchedule.objects.create(
        name="空调度",
        target="https://example.org",
        protocol=DetectionTask.Protocol.HTTPS,
        frequency_minutes=5,
        status=ProbeSchedule.Status.ACTIVE,
        source_type=ProbeSchedule.Source.MANUAL,
        next_run_at=now - timedelta(minutes=2),
    )
    previous_next = schedule.next_run_at

    processed, created = manual_schedule_runner.run_due_manual_schedules(now=now)

    assert processed == 1
    assert created == 0
    schedule.refresh_from_db()
    assert schedule.next_run_at == previous_next + timedelta(minutes=5)
