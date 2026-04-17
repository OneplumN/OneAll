from __future__ import annotations

import pytest

from apps.monitoring.models import DetectionTask
from apps.monitoring.services.detection_claim_service import claim_one_off_detection
from apps.probes.models import ProbeNode


@pytest.mark.django_db
def test_claim_one_off_detection_marks_running_and_returns_payload():
    probe = ProbeNode.objects.create(
        name="claim-probe",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    task = DetectionTask.objects.create(
        probe=probe,
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.SCHEDULED,
        metadata={"execution_source": "one_off", "timeout_seconds": 10, "expect_status": 200},
    )

    claimed = claim_one_off_detection(probe=probe)

    assert claimed is not None
    assert claimed.task_id == str(task.id)
    assert claimed.timeout_seconds == 10
    assert claimed.expected_status == 200

    task.refresh_from_db()
    assert task.status == DetectionTask.Status.RUNNING
    assert task.claimed_at is not None
    assert task.published_at is not None
