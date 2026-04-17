from unittest import mock
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.alerts.models import AlertSchedule
from apps.alerts.services import ensure_schedule_for_probe_schedule
from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution
from apps.probes.services import schedule_execution_service


@pytest.mark.django_db
@mock.patch("apps.probes.services.schedule_execution_service.probe_alert_service.evaluate_probe_alert")
def test_record_result_overrides_status_when_code_matches(mock_alert):
    probe = ProbeNode.objects.create(
        name="node-1",
        location="shanghai",
        network_type="external",
        supported_protocols=["HTTPS"],
        status="online",
    )
    schedule = ProbeSchedule.objects.create(
        name="sch-1",
        target="https://example.com",
        protocol="HTTPS",
        frequency_minutes=1,
        metadata={"expected_status_codes": [200, 204]},
    )
    schedule.probes.add(probe)

    execution = schedule_execution_service.record_result(
        schedule=schedule,
        probe=probe,
        scheduled_at=timezone.now(),
        status=ProbeScheduleExecution.Status.FAILED,
        response_time_ms=120,
        status_code="200",
        message="ok",
        metadata={},
    )

    assert execution.status == ProbeScheduleExecution.Status.SUCCEEDED
    mock_alert.assert_called_once()


@pytest.mark.django_db
@mock.patch("apps.probes.services.schedule_execution_service.probe_alert_service.evaluate_probe_alert")
def test_record_result_keeps_failed_status_when_code_not_expected(mock_alert):
    probe = ProbeNode.objects.create(
        name="node-2",
        location="beijing",
        network_type="external",
        supported_protocols=["HTTPS"],
        status="online",
    )
    schedule = ProbeSchedule.objects.create(
        name="sch-2",
        target="https://example.org",
        protocol="HTTPS",
        frequency_minutes=1,
        metadata={"expected_status_codes": [200]},
    )
    schedule.probes.add(probe)

    execution = schedule_execution_service.record_result(
        schedule=schedule,
        probe=probe,
        scheduled_at=timezone.now(),
        status=ProbeScheduleExecution.Status.FAILED,
        response_time_ms=150,
        status_code="500",
        message="error",
        metadata={},
    )

    assert execution.status == ProbeScheduleExecution.Status.FAILED
    mock_alert.assert_called_once()


@pytest.mark.django_db
@mock.patch("apps.probes.services.schedule_execution_service.probe_alert_service.evaluate_probe_alert")
def test_record_result_syncs_alert_schedule_runtime_fields_for_manual_schedule(mock_alert):
    probe = ProbeNode.objects.create(
        name="node-3",
        location="guangzhou",
        network_type="internal",
        supported_protocols=["HTTP"],
        status="online",
    )
    schedule = ProbeSchedule.objects.create(
        name="manual-sch",
        target="http://127.0.0.1:8000/",
        protocol="HTTP",
        frequency_minutes=2,
        source_type=ProbeSchedule.Source.MANUAL,
    )
    schedule.probes.add(probe)
    mapping = ensure_schedule_for_probe_schedule(schedule)
    alert_schedule = mapping.schedule
    assert isinstance(alert_schedule, AlertSchedule)

    scheduled_at = timezone.now()
    schedule_execution_service.record_result(
        schedule=schedule,
        probe=probe,
        scheduled_at=scheduled_at,
        status=ProbeScheduleExecution.Status.SUCCEEDED,
        response_time_ms=42,
        status_code="404",
        message="ok",
        metadata={},
    )

    alert_schedule.refresh_from_db()
    assert alert_schedule.last_run_at == scheduled_at
    assert alert_schedule.next_run_at == scheduled_at + timedelta(minutes=2)
    mock_alert.assert_called_once()
