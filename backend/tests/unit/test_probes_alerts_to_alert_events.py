from __future__ import annotations

from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from apps.alerts.models import AlertEvent
from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution
from apps.probes.services import probe_alert_service


@pytest.mark.django_db
@mock.patch("apps.probes.services.probe_alert_service.dispatch_alert_event.delay")
@mock.patch("apps.probes.services.probe_alert_service._dispatch_to_channel")
def test_probe_alert_creates_alert_event(mock_dispatch, mock_celery_delay):
    """Probe alert evaluation should emit an AlertEvent in the alerts domain."""

    probe = ProbeNode.objects.create(
        name="probe-node",
        location="shanghai",
        network_type="internal",
        supported_protocols=["HTTPS"],
        status="online",
    )
    schedule = ProbeSchedule.objects.create(
        name="baidu",
        description="test schedule",
        target="https://www.baidu.com",
        protocol="HTTPS",
        frequency_minutes=1,
        metadata={"alert_threshold": 1, "alert_contacts": ["ops@example.com"]},
    )
    schedule.probes.add(probe)

    scheduled_at = timezone.now() - timedelta(minutes=1)
    execution = ProbeScheduleExecution.objects.create(
        schedule=schedule,
        probe=probe,
        scheduled_at=scheduled_at,
        status=ProbeScheduleExecution.Status.FAILED,
        finished_at=timezone.now(),
        response_time_ms=1200,
        status_code="500",
        message="probe failure",
    )

    assert AlertEvent.objects.count() == 0

    probe_alert_service.evaluate_probe_alert(execution)

    assert AlertEvent.objects.count() == 1
    event = AlertEvent.objects.first()
    assert event is not None
    assert event.source == "probes"
    assert event.event_type == "probe_schedule_alert"
    assert event.related_task_id == schedule.id
    assert event.related_probe_id == probe.id
    assert event.context.get("execution_id") == str(execution.id)
    assert event.context.get("schedule_id") == str(schedule.id)
    assert event.context.get("probe_id") == str(probe.id)
    assert event.context.get("status") == execution.status

