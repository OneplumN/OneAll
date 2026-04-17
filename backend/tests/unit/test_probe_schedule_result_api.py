from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution


@pytest.mark.django_db
def test_probe_submit_schedule_result_records_execution_and_updates_runtime():
    probe = ProbeNode.objects.create(
        name="schedule-result-probe",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    probe.set_api_token("secret-schedule-result-token")

    scheduled_at = timezone.now() - timedelta(minutes=1)
    schedule = ProbeSchedule.objects.create(
        name="HTTPS monitor",
        target="https://example.com",
        protocol="HTTPS",
        frequency_minutes=5,
        status=ProbeSchedule.Status.ACTIVE,
        source_type=ProbeSchedule.Source.MANUAL,
        next_run_at=scheduled_at,
        metadata={"expected_status_codes": [200]},
    )
    schedule.probes.add(probe)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="ProbeToken secret-schedule-result-token")

    response = client.post(
        reverse("probe-schedule-result", kwargs={"schedule_id": str(schedule.id)}),
        {
            "probe_id": str(probe.id),
            "scheduled_at": scheduled_at.isoformat(),
            "status": "success",
            "message": "ok",
            "response_time_ms": 120,
            "status_code": "200",
            "metadata": {"source": "scheduler"},
        },
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ProbeScheduleExecution.Status.SUCCEEDED
    assert body["schedule_id"] == str(schedule.id)
    assert body["probe_id"] == str(probe.id)

    execution = ProbeScheduleExecution.objects.get(schedule=schedule, probe=probe, scheduled_at=scheduled_at)
    assert execution.status == ProbeScheduleExecution.Status.SUCCEEDED
    assert execution.response_time_ms == 120

    schedule.refresh_from_db()
    assert schedule.last_run_at == scheduled_at
    assert schedule.next_run_at == scheduled_at + timedelta(minutes=5)


@pytest.mark.django_db
def test_probe_submit_schedule_result_rejects_unassigned_probe():
    assigned_probe = ProbeNode.objects.create(
        name="assigned-probe",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    assigned_probe.set_api_token("assigned-token")
    other_probe = ProbeNode.objects.create(
        name="other-probe",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    other_probe.set_api_token("other-token")

    schedule = ProbeSchedule.objects.create(
        name="HTTPS monitor",
        target="https://example.com",
        protocol="HTTPS",
        frequency_minutes=5,
        status=ProbeSchedule.Status.ACTIVE,
        source_type=ProbeSchedule.Source.MANUAL,
        metadata={},
    )
    schedule.probes.add(assigned_probe)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="ProbeToken other-token")
    response = client.post(
        reverse("probe-schedule-result", kwargs={"schedule_id": str(schedule.id)}),
        {
            "probe_id": str(other_probe.id),
            "scheduled_at": timezone.now().isoformat(),
            "status": "failed",
            "message": "not allowed",
        },
        format="json",
    )

    assert response.status_code == 403
    assert ProbeScheduleExecution.objects.count() == 0
