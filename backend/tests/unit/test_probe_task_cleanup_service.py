from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode
from apps.probes.services import probe_task_cleanup_service


@pytest.mark.django_db
def test_mark_stale_running_tasks_marks_timeouts():
    probe = ProbeNode.objects.create(
        name="probe-cleaner",
        location="Test",
        network_type="internal",
        supported_protocols=["HTTP"],
    )

    stale_task = DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        probe=probe,
        status=DetectionTask.Status.RUNNING,
        metadata={"timeout_seconds": 5},
    )
    fresh_task = DetectionTask.objects.create(
        target="https://example.net",
        protocol=DetectionTask.Protocol.HTTPS,
        probe=probe,
        status=DetectionTask.Status.RUNNING,
        metadata={"timeout_seconds": 15},
    )

    now = timezone.now()
    DetectionTask.objects.filter(id=stale_task.id).update(updated_at=now - timedelta(seconds=20))
    DetectionTask.objects.filter(id=fresh_task.id).update(updated_at=now - timedelta(seconds=2))

    cleaned = probe_task_cleanup_service.mark_stale_running_tasks(
        probe=probe,
        now=now,
        grace_seconds=2,
    )

    stale_task.refresh_from_db()
    fresh_task.refresh_from_db()

    assert cleaned == 1
    assert stale_task.status == DetectionTask.Status.TIMEOUT
    assert stale_task.error_message == "探针未在超时时间内回传结果"
    assert fresh_task.status == DetectionTask.Status.RUNNING
