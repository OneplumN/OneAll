from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode


@pytest.mark.django_db
def test_probe_submit_result_marks_detection_succeeded_idempotently():
    probe = ProbeNode.objects.create(
        name="result-api-probe",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    probe.set_api_token("secret-result-token")

    task = DetectionTask.objects.create(
        probe=probe,
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.RUNNING,
        metadata={"execution_source": "one_off", "timeout_seconds": 10},
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="ProbeToken secret-result-token")
    url = reverse("probe-task-result", kwargs={"task_id": str(task.id)})
    payload = {
        "status": "success",
        "message": "ok",
        "response_time_ms": 123,
        "status_code": "200",
        "metadata": {"source": "probe"},
    }

    response = client.post(url, payload, format="json")
    assert response.status_code == 200
    assert response.json()["status"] == DetectionTask.Status.SUCCEEDED

    task.refresh_from_db()
    assert task.status == DetectionTask.Status.SUCCEEDED
    assert task.response_time_ms == 123

    again = client.post(url, payload, format="json")
    assert again.status_code == 200
    task.refresh_from_db()
    assert task.status == DetectionTask.Status.SUCCEEDED


@pytest.mark.django_db
def test_probe_submit_result_maps_deadline_exceeded_to_timeout():
    probe = ProbeNode.objects.create(
        name="result-timeout-probe",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    probe.set_api_token("secret-timeout-token")

    task = DetectionTask.objects.create(
        probe=probe,
        target="https://example.com/slow",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.RUNNING,
        metadata={"execution_source": "one_off", "timeout_seconds": 2},
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="ProbeToken secret-timeout-token")
    url = reverse("probe-task-result", kwargs={"task_id": str(task.id)})
    payload = {
        "status": "failed",
        "message": 'Get "https://example.com/slow": context deadline exceeded',
        "metadata": {"source": "probe"},
    }

    response = client.post(url, payload, format="json")
    assert response.status_code == 200
    assert response.json()["status"] == DetectionTask.Status.TIMEOUT

    task.refresh_from_db()
    assert task.status == DetectionTask.Status.TIMEOUT
    assert "context deadline exceeded" in task.error_message
