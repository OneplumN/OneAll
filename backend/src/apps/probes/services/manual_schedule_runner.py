from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeSchedule

from .probe_task_service import expect_status_from_metadata, timeout_from_metadata


def run_due_manual_schedules(*, now=None) -> tuple[int, int]:
    current = now or timezone.now()
    schedules = (
        ProbeSchedule.objects.prefetch_related("probes")
        .filter(
            status=ProbeSchedule.Status.ACTIVE,
            source_type=ProbeSchedule.Source.MANUAL,
            next_run_at__isnull=False,
            next_run_at__lte=current,
        )
        .order_by("next_run_at", "id")
    )

    processed = 0
    created = 0
    for schedule in schedules:
        processed += 1
        if _enqueue_schedule(schedule=schedule, now=current):
            created += 1

    return processed, created


def _enqueue_schedule(*, schedule: ProbeSchedule, now) -> bool:
    probes = list(schedule.probes.filter(status="online").order_by("name", "id"))

    created_any = False
    if probes:
        metadata = schedule.metadata or {}
        expected_codes = _normalize_expected_status_codes(metadata.get("expected_status_codes"))
        expect_status = expect_status_from_metadata(metadata)
        timeout_seconds = timeout_from_metadata(metadata)
        alert_threshold = _normalize_positive_int(metadata.get("alert_threshold"), default=1)

        payload = {
            "schedule_id": str(schedule.id),
            "expected_status_codes": expected_codes,
            "expect_status": expect_status,
            "timeout_seconds": timeout_seconds,
            "alert_threshold": alert_threshold,
            "config": {
                "expected_status_codes": expected_codes,
                "expect_status": expect_status,
                "timeout_seconds": timeout_seconds,
                "alert_threshold": alert_threshold,
            },
        }

        with transaction.atomic():
            DetectionTask.objects.create(
                target=schedule.target,
                protocol=schedule.protocol,
                probe=probes[0],
                status=DetectionTask.Status.SCHEDULED,
                metadata=payload,
            )
            _advance_schedule(schedule=schedule, now=now)
        created_any = True
    else:
        _advance_schedule(schedule=schedule, now=now)

    return created_any


def _advance_schedule(*, schedule: ProbeSchedule, now) -> None:
    interval = max(int(schedule.frequency_minutes or 1), 1)
    base_time = schedule.next_run_at or now
    schedule.next_run_at = base_time + timedelta(minutes=interval)
    schedule.save(update_fields=["next_run_at", "updated_at"])


def _normalize_expected_status_codes(value) -> list[int]:
    if isinstance(value, (int, str)):
        value = [value]
    if not isinstance(value, list):
        return [200]

    normalized: list[int] = []
    for item in value:
        try:
            code = int(item)
        except (TypeError, ValueError):
            continue
        if 100 <= code <= 599:
            normalized.append(code)
    return normalized or [200]


def _normalize_positive_int(value, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default

