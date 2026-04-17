from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from django.db import transaction
from django.utils import timezone

from datetime import timedelta

from apps.alerts.models import AlertCheckExecution, AlertEvent, AlertSchedule
from apps.alerts.services import CheckResult, evaluate_and_raise
from apps.alerts.tasks import dispatch_alert_event
from apps.monitoring.models import DetectionTask
from apps.monitoring.repositories import detection_metrics
from apps.probes.models import ProbeNode
from apps.monitoring.services.detection_scheduler import DetectionScheduler, ProbeCapacityError, ProbeUnavailableError

logger = logging.getLogger(__name__)


class DetectionStatus(str, Enum):
    SCHEDULED = DetectionTask.Status.SCHEDULED
    RUNNING = DetectionTask.Status.RUNNING
    SUCCEEDED = DetectionTask.Status.SUCCEEDED
    FAILED = DetectionTask.Status.FAILED
    TIMEOUT = DetectionTask.Status.TIMEOUT


@dataclass
class DetectionRequest:
    target: str
    protocol: str
    probe_id: Optional[str]
    timeout_seconds: int
    metadata: dict[str, Any]


def _get_probe(probe_id: Optional[str]) -> Optional[ProbeNode]:
    if not probe_id:
        return None
    try:
        return ProbeNode.objects.get(id=probe_id)
    except ProbeNode.DoesNotExist as exc:  # pragma: no cover
        raise ValueError("指定的探针不存在") from exc


def schedule_one_off_detection(request: DetectionRequest) -> DetectionTask:
    if request.protocol not in DetectionTask.Protocol.values:
        raise ValueError("不支持的拨测协议")

    probe = _get_probe(request.probe_id)

    scheduler = DetectionScheduler()
    scheduler.guard_probe(probe, request.protocol)
    requested_by = None
    metadata = _normalize_one_off_metadata(request)
    if metadata.get("initiated_by"):
        try:
            requested_by = uuid.UUID(str(metadata["initiated_by"]))
        except (ValueError, TypeError):
            requested_by = None

    with transaction.atomic():
        detection = DetectionTask.objects.create(
            target=request.target,
            protocol=request.protocol,
            probe=probe,
            status=DetectionTask.Status.SCHEDULED,
            metadata=metadata,
            requested_by=requested_by,
        )
    _schedule_one_off_detection_timeout(detection.id, request.timeout_seconds)

    return detection


def mark_detection_timeout(
    detection_id: uuid.UUID,
    *,
    message: str = "探针未在超时时间内回传结果",
    response_time_ms: int | None = None,
    status_code: str | int | None = None,
    result_payload: Optional[dict[str, Any]] = None,
    executed_at=None,
) -> None:
    try:
        detection = DetectionTask.objects.get(id=detection_id)
    except DetectionTask.DoesNotExist:  # pragma: no cover
        return

    if detection.status not in {DetectionTask.Status.SCHEDULED, DetectionTask.Status.RUNNING}:
        return

    detection.mark_timeout(
        message=message,
        response_time_ms=response_time_ms,
        status_code=status_code,
        result_payload=result_payload,
        executed_at=executed_at,
    )
    _store_detection_metrics(detection)
    _record_alert_check_execution_for_detection(detection)
    _maybe_raise_aggregated_alert_for_job(detection)


def mark_detection_failed(
    detection_id: uuid.UUID,
    message: str,
    *,
    response_time_ms: int | None = None,
    status_code: str | int | None = None,
    result_payload: Optional[dict[str, Any]] = None,
    executed_at=None,
) -> None:
    try:
        detection = DetectionTask.objects.get(id=detection_id)
    except DetectionTask.DoesNotExist:  # pragma: no cover
        return

    if detection.status not in {DetectionTask.Status.SCHEDULED, DetectionTask.Status.RUNNING}:
        return

    detection.mark_failed(
        message,
        response_time_ms=response_time_ms,
        status_code=status_code,
        result_payload=result_payload,
        executed_at=executed_at,
    )
    _store_detection_metrics(detection)
    _record_alert_check_execution_for_detection(detection)
    _maybe_raise_aggregated_alert_for_job(detection)


def mark_detection_succeeded(
    detection_id: uuid.UUID,
    response_time_ms: Optional[int],
    result_payload: Optional[dict[str, Any]] = None,
    *,
    status_code: str | int | None = None,
    message: str = "",
    executed_at=None,
) -> None:
    try:
        detection = DetectionTask.objects.get(id=detection_id)
    except DetectionTask.DoesNotExist:  # pragma: no cover
        return

    if detection.status not in {DetectionTask.Status.SCHEDULED, DetectionTask.Status.RUNNING}:
        return

    detection.mark_succeeded(
        response_time_ms,
        result_payload or {},
        status_code=status_code,
        message=message,
        executed_at=executed_at,
    )
    _store_detection_metrics(detection)
    _record_alert_check_execution_for_detection(detection)


def _normalize_one_off_metadata(request: DetectionRequest) -> dict[str, Any]:
    metadata = dict(request.metadata or {})
    metadata["execution_source"] = "one_off"
    metadata["timeout_seconds"] = request.timeout_seconds

    config = metadata.get("config")
    if not isinstance(config, dict):
        config = {}
    else:
        config = dict(config)
    config.setdefault("timeout_seconds", request.timeout_seconds)
    metadata["config"] = config
    return metadata


def _schedule_one_off_detection_timeout(detection_id: uuid.UUID, timeout_seconds: int) -> None:
    try:
        from apps.monitoring.tasks.execute_detection import expire_detection_task

        expire_detection_task.apply_async(
            args=[str(detection_id)],
            countdown=max(int(timeout_seconds or 0), 1),
        )
    except Exception:  # pragma: no cover - broker degradation should not block task creation
        logger.exception("Failed to enqueue one-off detection timeout", extra={"detection_id": str(detection_id)})


def _store_detection_metrics(detection: DetectionTask) -> None:
    detection_metrics.store_detection_result(
        detection_id=detection.id,
        probe_id=detection.probe_id,
        protocol=detection.protocol,
        target=detection.target,
        status=detection.status,
        response_time_ms=detection.response_time_ms,
        metadata=detection.result_payload,
        recorded_at=detection.executed_at or detection.updated_at or timezone.now(),
    )


def _maybe_raise_aggregated_alert_for_job(detection: DetectionTask) -> Optional[AlertEvent]:
    """Raise an aggregated alert when a monitoring job repeatedly fails.

    Rules:
    - Scope: only scheduled monitoring jobs (DetectionTask.metadata['job_id'] present)
    - Window: last 3 minutes
    - Threshold: at least 2 failed/timeout executions within the window
    - De-duplication: at most one AlertEvent per job within the window
    """

    # Only consider failed/timeout detections as candidates
    if detection.status not in (DetectionTask.Status.FAILED, DetectionTask.Status.TIMEOUT):
        return None

    metadata = detection.metadata or {}
    job_id_raw = metadata.get("job_id")
    if not job_id_raw:
        # One-off detections don't participate in aggregated job alerts
        return None

    try:
        job_id = uuid.UUID(str(job_id_raw))
    except (ValueError, TypeError):
        # Malformed job id, skip alerting instead of raising
        return None

    now = timezone.now()
    window_start = now - timedelta(minutes=3)

    # Count failures for this job within the window
    failing_qs = DetectionTask.objects.filter(
        metadata__job_id=str(job_id),
        status__in=[DetectionTask.Status.FAILED, DetectionTask.Status.TIMEOUT],
        created_at__gte=window_start,
    ).order_by("-created_at")

    failure_count = failing_qs.count()
    if failure_count < 2:
        return None

    # Window-level de-duplication: if we've already raised an alert for this job
    # in the same window, do nothing.
    if AlertEvent.objects.filter(
        source="monitoring",
        related_task_id=job_id,
        created_at__gte=window_start,
    ).exists():
        return None

    last_detection = failing_qs.first() or detection
    last_failure_reason = last_detection.error_message
    last_failure_at = last_detection.executed_at or last_detection.created_at
    target = last_detection.target

    if last_failure_at:
        last_failure_ts = last_failure_at.strftime("%Y-%m-%d %H:%M:%S")
        message = f"任务 {target} 在过去 3 分钟内失败了 {failure_count} 次（最近一次失败时间：{last_failure_ts}）。"
    else:
        message = f"任务 {target} 在过去 3 分钟内失败了 {failure_count} 次。"

    context = {
        "window_minutes": 3,
        "failure_threshold": 2,
        "failure_count": failure_count,
        "last_failure_reason": last_failure_reason,
        "last_failure_at": last_failure_at.isoformat() if last_failure_at else None,
        "target": target,
        "job_id": str(job_id),
        "probe_id": str(last_detection.probe_id) if last_detection.probe_id else None,
    }

    result = CheckResult(
        source="monitoring",
        event_type="monitoring_check_failed_aggregated",
        severity="critical",
        title="监控任务连续失败告警",
        message=message,
        status="failed",
        task_id=str(job_id),
        asset_id=None,
        probe_id=str(last_detection.probe_id) if last_detection.probe_id else None,
        context=context,
    )

    event = evaluate_and_raise(result)
    # Fire-and-forget async dispatch; real delivery will be implemented later
    _enqueue_alert_dispatch(str(event.id))
    return event


def _enqueue_alert_dispatch(event_id: str) -> None:
    try:
        dispatch_alert_event.delay(event_id)
    except Exception:  # pragma: no cover - broker degradation should not break detection state transitions
        logger.exception("Failed to enqueue monitoring alert event %s", event_id)


def _record_alert_check_execution_for_detection(detection: DetectionTask) -> None:
    """Mirror a DetectionTask into AlertCheckExecution for unified alert handling."""

    metadata = detection.metadata or {}
    # Historically we stored both job_id and request_id in metadata. AlertCheck /
    # AlertSchedule are keyed off the MonitoringRequest id, so we resolve the
    # schedule via request_id here to keep the mapping stable even if job ids
    # change or multiple jobs exist for the same request.
    request_id_raw = metadata.get("request_id")
    if not request_id_raw:
        # One-off detections or legacy tasks without request_id are not yet
        # mirrored into AlertCheckExecution.
        return

    try:
        request_id = uuid.UUID(str(request_id_raw))
    except (ValueError, TypeError):
        return

    try:
        schedule = AlertSchedule.objects.get(alert_check__source_id=request_id)
    except AlertSchedule.DoesNotExist:
        return

    status = detection.status
    scheduled_at = detection.created_at or timezone.now()
    started_at = detection.executed_at
    finished_at = detection.executed_at

    AlertCheckExecution.objects.update_or_create(
        source_type="detection_task",
        source_id=detection.id,
        defaults={
            "schedule": schedule,
            "executor_type": AlertCheckExecution.executor_type.field.default,
            "executor_ref": str(detection.probe_id) if detection.probe_id else "",
            "scheduled_at": scheduled_at,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "response_time_ms": detection.response_time_ms,
            "status_code": detection.status_code,
            "error_message": detection.error_message,
            "result_payload": detection.result_payload or {},
        },
    )
