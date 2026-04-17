from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any

from apps.monitoring.models import DetectionTask
from apps.monitoring.services import detection_service
from apps.probes.models import ProbeNode


TERMINAL_STATUSES = {
    DetectionTask.Status.SUCCEEDED,
    DetectionTask.Status.FAILED,
    DetectionTask.Status.TIMEOUT,
}

TIMEOUT_MESSAGE_PATTERNS = (
    re.compile(r"context deadline exceeded", re.IGNORECASE),
    re.compile(r"\btimeout\b", re.IGNORECASE),
    re.compile(r"timed out", re.IGNORECASE),
)


@dataclass
class DetectionResultPayload:
    status: str
    message: str
    response_time_ms: int | None
    status_code: str | int | None
    metadata: dict[str, Any]
    executed_at: Any


def submit_detection_result(
    *,
    probe: ProbeNode,
    detection_id: uuid.UUID,
    payload: DetectionResultPayload,
) -> DetectionTask:
    detection = DetectionTask.objects.get(id=detection_id)

    if detection.probe_id and detection.probe_id != probe.id:
        raise PermissionError("probe does not own detection task")

    if detection.status in TERMINAL_STATUSES:
        return detection

    normalized = (payload.status or "").strip().lower()
    if normalized in {"success", "succeeded"}:
        detection_service.mark_detection_succeeded(
            detection.id,
            response_time_ms=payload.response_time_ms,
            result_payload=payload.metadata or {},
            status_code=payload.status_code,
            message=payload.message,
            executed_at=payload.executed_at,
        )
    elif normalized in {"timeout", "timed_out", "missed"}:
        detection_service.mark_detection_timeout(
            detection.id,
            message=payload.message or "检测超时",
            response_time_ms=payload.response_time_ms,
            status_code=payload.status_code,
            result_payload=payload.metadata or {},
            executed_at=payload.executed_at,
        )
    else:
        if _looks_like_timeout(payload.message):
            detection_service.mark_detection_timeout(
                message=payload.message or "检测超时",
                detection_id=detection.id,
                response_time_ms=payload.response_time_ms,
                status_code=payload.status_code,
                result_payload=payload.metadata or {},
                executed_at=payload.executed_at,
            )
        else:
            detection_service.mark_detection_failed(
                detection.id,
                payload.message or "检测失败",
                response_time_ms=payload.response_time_ms,
                status_code=payload.status_code,
                result_payload=payload.metadata or {},
                executed_at=payload.executed_at,
            )

    detection.refresh_from_db()
    return detection


def _looks_like_timeout(message: str) -> bool:
    if not message:
        return False
    return any(pattern.search(message) for pattern in TIMEOUT_MESSAGE_PATTERNS)
