from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode
from apps.probes.services import probe_task_service


@dataclass
class ClaimedDetection:
    task_id: str
    target: str
    protocol: str
    timeout_seconds: int
    expected_status: int
    metadata: dict[str, Any]
    scheduled_at: str


def claim_one_off_detection(*, probe: ProbeNode) -> ClaimedDetection | None:
    with transaction.atomic():
        detection = (
            DetectionTask.objects.select_for_update(skip_locked=True)
            .filter(
                probe=probe,
                status=DetectionTask.Status.SCHEDULED,
                metadata__execution_source="one_off",
            )
            .order_by("created_at", "id")
            .first()
        )
        if detection is None:
            return None

        metadata = _build_metadata(detection.metadata)
        now = timezone.now()
        detection.mark_running(published_at=now, claimed_at=now)

        return ClaimedDetection(
            task_id=str(detection.id),
            target=detection.target,
            protocol=detection.protocol,
            timeout_seconds=probe_task_service.timeout_from_metadata(metadata),
            expected_status=probe_task_service.expect_status_from_metadata(metadata),
            metadata=metadata,
            scheduled_at=detection.created_at.isoformat(),
        )


def _build_metadata(metadata: dict | None) -> dict[str, Any]:
    payload = dict(metadata or {})
    config = payload.get("config")
    if isinstance(config, dict):
        for key, value in config.items():
            payload.setdefault(key, value)
    return payload
