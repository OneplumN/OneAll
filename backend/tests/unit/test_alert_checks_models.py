from __future__ import annotations

import uuid

import pytest
from django.utils import timezone

from apps.alerts.models import AlertCheck, AlertCheckExecution, AlertSchedule


@pytest.mark.django_db
def test_alert_check_basic_fields():
    check = AlertCheck.objects.create(
        name="Homepage HTTPS",
        target="https://example.com/health",
        protocol="HTTPS",
        source_type=AlertCheck.SourceType.MONITORING_REQUEST,
        source_id=uuid.uuid4(),
        executor_type=AlertCheck.ExecutorType.DIRECT,
        executor_config={"timeout": 5},
    )

    assert check.id is not None
    assert check.name == "Homepage HTTPS"
    assert check.target.startswith("https://")
    assert check.protocol == "HTTPS"
    assert check.source_type == AlertCheck.SourceType.MONITORING_REQUEST
    assert check.executor_type == AlertCheck.ExecutorType.DIRECT


@pytest.mark.django_db
def test_alert_schedule_links_to_check():
    check = AlertCheck.objects.create(
        name="Probe schedule",
        target="https://probe.example.com/ping",
        protocol="HTTPS",
        source_type=AlertCheck.SourceType.PROBE_SCHEDULE,
    )

    schedule = AlertSchedule.objects.create(
        alert_check=check,
        frequency_minutes=5,
        status=AlertSchedule.Status.ACTIVE,
    )

    assert schedule.alert_check_id == check.id
    assert schedule.frequency_minutes == 5
    assert schedule.status == AlertSchedule.Status.ACTIVE


@pytest.mark.django_db
def test_alert_check_execution_links_to_schedule_and_defaults():
    check = AlertCheck.objects.create(
        name="Homepage HTTPS",
        target="https://example.com/health",
        protocol="HTTPS",
        source_type=AlertCheck.SourceType.MONITORING_REQUEST,
    )
    schedule = AlertSchedule.objects.create(alert_check=check, frequency_minutes=1)
    scheduled_at = timezone.now()

    execution = AlertCheckExecution.objects.create(
        schedule=schedule,
        scheduled_at=scheduled_at,
        status=AlertCheckExecution.Status.SCHEDULED,
    )

    assert execution.schedule_id == schedule.id
    assert execution.scheduled_at == scheduled_at
    assert execution.status == AlertCheckExecution.Status.SCHEDULED
    assert execution.executor_type in dict(AlertCheck.ExecutorType.choices)

