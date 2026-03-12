from __future__ import annotations

from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution
from . import probe_alert_service


def record_result(
    *,
    schedule: ProbeSchedule,
    probe: ProbeNode,
    scheduled_at: datetime,
    status: str,
    response_time_ms: int | None,
    status_code: str | None,
    message: str | None,
    metadata: dict | None,
) -> ProbeScheduleExecution:
    scheduled_at = scheduled_at.replace(tzinfo=timezone.utc) if scheduled_at.tzinfo is None else scheduled_at
    finished_at = timezone.now()
    status = ProbeScheduleExecution.normalize_status(status)
    status = _apply_expected_status_codes(schedule, status, status_code)
    payload = {
        "status": status,
        "response_time_ms": response_time_ms,
        "status_code": status_code or "",
        "message": message or "",
        "metadata": metadata or {},
        "finished_at": finished_at,
    }
    with transaction.atomic():
        execution, _ = ProbeScheduleExecution.objects.get_or_create(
            schedule=schedule,
            probe=probe,
            scheduled_at=scheduled_at,
            defaults={
                "status": ProbeScheduleExecution.Status.RUNNING,
                "started_at": finished_at,
            },
        )
        for field, value in payload.items():
            setattr(execution, field, value)
        execution.save(
            update_fields=["status", "response_time_ms", "status_code", "message", "metadata", "finished_at", "updated_at"]
        )
        _update_schedule_runtime(schedule=schedule, scheduled_at=scheduled_at)
    probe_alert_service.evaluate_probe_alert(execution)
    return execution


def _update_schedule_runtime(*, schedule: ProbeSchedule, scheduled_at: datetime) -> None:
    interval_minutes = schedule.frequency_minutes or 1
    next_run = scheduled_at + timedelta(minutes=max(interval_minutes, 1))
    last_run_at = schedule.last_run_at
    should_update = last_run_at is None or scheduled_at >= last_run_at
    if not should_update:
        return
    schedule.last_run_at = scheduled_at
    schedule.next_run_at = next_run
    schedule.save(update_fields=["last_run_at", "next_run_at", "updated_at"])


def _apply_expected_status_codes(
    schedule: ProbeSchedule, status: str, status_code: str | None
) -> str:
    if status != ProbeScheduleExecution.Status.FAILED:
        return status
    metadata = schedule.metadata or {}
    expected_codes = metadata.get("expected_status_codes") or []
    if not expected_codes:
        return status
    try:
        numeric_code = int(status_code) if status_code is not None else None
    except (TypeError, ValueError):
        return status
    if numeric_code is None:
        return status
    if not 100 <= numeric_code <= 599:
        return status
    normalized = set()
    for value in expected_codes:
        try:
            code = int(value)
        except (TypeError, ValueError):
            continue
        if 100 <= code <= 599:
            normalized.add(code)
    if numeric_code in normalized:
        return ProbeScheduleExecution.Status.SUCCEEDED
    return status
