from __future__ import annotations

from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from apps.core.models import AuditLog
from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution
from apps.probes.services import probe_alert_service
from apps.settings.models import AlertChannel


@pytest.fixture
def probe() -> ProbeNode:
    return ProbeNode.objects.create(
        name="probe-node",
        location="shanghai",
        network_type="internal",
        supported_protocols=["HTTPS"],
        status="online",
    )


@pytest.fixture
def schedule(probe: ProbeNode) -> ProbeSchedule:
    schedule = ProbeSchedule.objects.create(
        name="baidu",
        description="test schedule",
        target="https://www.baidu.com",
        protocol="HTTPS",
        frequency_minutes=1,
        metadata={"alert_threshold": 2, "alert_contacts": ["ops@example.com"]},
    )
    schedule.probes.add(probe)
    return schedule


def _create_execution(
    schedule: ProbeSchedule,
    probe: ProbeNode,
    minutes_ago: int,
    status: str,
) -> ProbeScheduleExecution:
    scheduled_at = timezone.now() - timedelta(minutes=minutes_ago)
    return ProbeScheduleExecution.objects.create(
        schedule=schedule,
        probe=probe,
        scheduled_at=scheduled_at,
        status=status,
        finished_at=timezone.now(),
    )


@pytest.mark.django_db
@mock.patch("apps.probes.services.probe_alert_service.dispatch_alert_event.delay")
def test_alert_triggers_after_threshold(mock_celery_delay, schedule, probe):
    AlertChannel.objects.create(
        channel_type="http",
        name="callback",
        enabled=True,
        config={"url": "http://example.com/alert"},
    )
    _create_execution(schedule, probe, minutes_ago=3, status=ProbeScheduleExecution.Status.FAILED)
    current = _create_execution(schedule, probe, minutes_ago=1, status=ProbeScheduleExecution.Status.FAILED)

    probe_alert_service.evaluate_probe_alert(current)

    assert AuditLog.objects.filter(action="probes.alert").count() == 1
    mock_celery_delay.assert_called_once()


@pytest.mark.django_db
@mock.patch("apps.probes.services.probe_alert_service.dispatch_alert_event.delay")
def test_alert_skipped_when_threshold_not_met(mock_celery_delay, schedule, probe):
    metadata = dict(schedule.metadata or {})
    metadata["alert_threshold"] = 3
    schedule.metadata = metadata
    schedule.save(update_fields=["metadata"])

    current = _create_execution(schedule, probe, minutes_ago=1, status=ProbeScheduleExecution.Status.FAILED)

    probe_alert_service.evaluate_probe_alert(current)

    assert AuditLog.objects.filter(action="probes.alert").count() == 0
    mock_celery_delay.assert_not_called()


@pytest.mark.django_db
@mock.patch("apps.probes.services.probe_alert_service.dispatch_alert_event.delay")
def test_alert_not_duplicated_for_same_execution(mock_celery_delay, schedule, probe):
    AlertChannel.objects.create(
        channel_type="http",
        name="callback",
        enabled=True,
        config={"url": "http://example.com/alert"},
    )
    _create_execution(schedule, probe, minutes_ago=2, status=ProbeScheduleExecution.Status.FAILED)
    current = _create_execution(schedule, probe, minutes_ago=0, status=ProbeScheduleExecution.Status.FAILED)

    probe_alert_service.evaluate_probe_alert(current)
    probe_alert_service.evaluate_probe_alert(current)

    assert AuditLog.objects.filter(action="probes.alert").count() == 1
    mock_celery_delay.assert_called_once()


@pytest.mark.django_db
@mock.patch("apps.probes.services.probe_alert_service.dispatch_alert_event.delay")
def test_alert_record_includes_message(mock_celery_delay, schedule, probe):
    AlertChannel.objects.create(
        channel_type="email",
        name="mail",
        enabled=True,
        config={"smtp_host": "smtp.example.com", "from_email": "ops@example.com"},
    )
    metadata = dict(schedule.metadata or {})
    metadata["alert_threshold"] = 1
    schedule.metadata = metadata
    schedule.save(update_fields=["metadata"])

    current = _create_execution(schedule, probe, minutes_ago=0, status=ProbeScheduleExecution.Status.FAILED)

    probe_alert_service.evaluate_probe_alert(current)

    entry = AuditLog.objects.filter(action="probes.alert").latest("created_at")
    assert "目标：" in entry.metadata.get("message", "")


@pytest.mark.django_db
@mock.patch("apps.probes.services.probe_alert_service.logger")
@mock.patch("apps.probes.services.probe_alert_service.dispatch_alert_event.delay", side_effect=RuntimeError("redis down"))
def test_alert_dispatch_enqueue_failure_does_not_break_evaluation(
    mock_celery_delay,
    mock_logger,
    schedule,
    probe,
):
    metadata = dict(schedule.metadata or {})
    metadata["alert_threshold"] = 1
    schedule.metadata = metadata
    schedule.save(update_fields=["metadata"])

    current = _create_execution(schedule, probe, minutes_ago=0, status=ProbeScheduleExecution.Status.FAILED)

    probe_alert_service.evaluate_probe_alert(current)

    assert AuditLog.objects.filter(action="probes.alert").count() == 1
    mock_logger.exception.assert_called()
