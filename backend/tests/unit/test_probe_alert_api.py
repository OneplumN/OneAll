from __future__ import annotations

import uuid

import pytest
from django.urls import reverse

from apps.core.models import AuditLog, User
from apps.probes.models import ProbeNode, ProbeSchedule


@pytest.mark.django_db
def test_recent_probe_alerts_api(client):
    user = User.objects.create_user(username="tester", password="dummy")
    client.force_login(user)

    probe = ProbeNode.objects.create(
        name="probe-api",
        location="sh-idc",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    schedule = ProbeSchedule.objects.create(
        name="baidu",
        description="api test",
        target="https://www.baidu.com",
        protocol="HTTPS",
        frequency_minutes=1,
        metadata={"alert_threshold": 1},
    )
    AuditLog.objects.create(
        action="probes.alert",
        metadata={
            "execution_id": str(uuid.uuid4()),
            "schedule_id": str(schedule.id),
            "probe_id": str(probe.id),
            "status": "failed",
            "threshold": 1,
            "alert_contacts": ["ops@example.com"],
            "message": "探针连续失败",
        },
    )

    response = client.get(reverse("probe-alerts-recent"))
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    entry = items[0]
    assert entry["schedule_name"] == "baidu"
    assert entry["probe_name"] == "probe-api"
    assert entry["severity"] == "critical"
