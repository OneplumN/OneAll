from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models.user import Role
from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution


def _make_user_with_perms(username: str, *permissions: str):
    user_model = get_user_model()
    user = user_model.objects.create_user(username=username, password="pass1234")
    role = Role.objects.create(name=f"{username}-role", permissions=list(permissions))
    user.roles.set([role])
    return user


@pytest.mark.django_db
def test_probe_nodes_health_falls_back_to_schedule_executions_without_timescale():
    user = _make_user_with_perms("probe_health_viewer", "probes.nodes.view")
    probe = ProbeNode.objects.create(
        name="health-node",
        location="Shanghai",
        network_type="internal",
        supported_protocols=["HTTP"],
        status="online",
        last_heartbeat_at=timezone.now(),
    )
    schedule = ProbeSchedule.objects.create(
        name="health-schedule",
        target="http://127.0.0.1:8000/",
        protocol="HTTP",
        frequency_minutes=1,
        source_type=ProbeSchedule.Source.MANUAL,
    )
    schedule.probes.add(probe)
    ProbeScheduleExecution.objects.create(
        schedule=schedule,
        probe=probe,
        scheduled_at=timezone.now(),
        started_at=timezone.now(),
        finished_at=timezone.now(),
        status=ProbeScheduleExecution.Status.SUCCEEDED,
        response_time_ms=88,
        status_code="404",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("probe-node-health"))

    assert response.status_code == 200, response.json()
    items = response.json()["items"]
    item = next(row for row in items if row["id"] == str(probe.id))
    assert item["status"] == "online"
    assert item["executions"] == 1
    assert item["success"] == 1
    assert item["failed"] == 0
    assert item["success_rate"] == 100.0
    assert item["avg_latency_ms"] == 88.0
