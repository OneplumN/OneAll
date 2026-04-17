from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode


@pytest.mark.django_db
def test_probe_can_claim_one_off_detection():
    probe = ProbeNode.objects.create(
        name="claim-api-probe",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    probe.set_api_token("secret-claim-token")
    task = DetectionTask.objects.create(
        probe=probe,
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.SCHEDULED,
        metadata={"execution_source": "one_off", "timeout_seconds": 10},
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="ProbeToken secret-claim-token")

    response = client.post(
        reverse("probe-task-claim"),
        {"probe_id": str(probe.id), "limit": 1},
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == str(task.id)
    assert body["timeout_seconds"] == 10

    task.refresh_from_db()
    assert task.status == DetectionTask.Status.RUNNING
    assert task.claimed_at is not None
