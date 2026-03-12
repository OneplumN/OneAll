from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.monitoring.models import DetectionTask, MonitoringJob
from apps.probes.models import ProbeNode


def enqueue_due_jobs(*, now=None) -> tuple[int, int]:
    current = now or timezone.now()
    jobs = (
        MonitoringJob.objects.select_related("request")
        .filter(status=MonitoringJob.Status.ACTIVE, next_run_at__isnull=False, next_run_at__lte=current)
        .order_by("next_run_at", "id")
    )

    processed = 0
    created = 0

    for job in jobs:
        processed += 1
        if _enqueue_single_job(job=job, now=current):
            created += 1

    return processed, created


def _enqueue_single_job(*, job: MonitoringJob, now) -> bool:
    request = job.request
    metadata = request.metadata or {}
    probe = _pick_probe(metadata)

    if probe is None:
        _update_next_run(job=job, now=now)
        return False

    expected_codes = _normalize_expected_status_codes(metadata.get("expected_status_codes"))
    expect_status = _pick_expect_status(metadata, expected_codes)
    timeout_seconds = _normalize_positive_int(metadata.get("timeout_seconds"), default=30)
    alert_threshold = _normalize_positive_int(metadata.get("alert_threshold"), default=1)

    payload = {
        "job_id": str(job.id),
        "request_id": str(request.id),
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
            target=request.target,
            protocol=request.protocol,
            probe=probe,
            status=DetectionTask.Status.SCHEDULED,
            metadata=payload,
        )
        _update_next_run(job=job, now=now)
    return True


def _pick_probe(metadata: dict) -> ProbeNode | None:
    probe_ids = metadata.get("probe_ids") or []
    if not isinstance(probe_ids, list):
        probe_ids = [probe_ids]

    normalized_ids = [str(probe_id) for probe_id in probe_ids if probe_id]
    if normalized_ids:
        probe_map = {str(node.id): node for node in ProbeNode.objects.filter(id__in=normalized_ids, status="online")}
        for probe_id in normalized_ids:
            if probe_id in probe_map:
                return probe_map[probe_id]

    return ProbeNode.objects.filter(status="online").order_by("name", "id").first()


def _update_next_run(*, job: MonitoringJob, now) -> None:
    interval = max(int(job.frequency_minutes or 1), 1)
    base_time = job.next_run_at or now
    job.last_run_at = now
    job.next_run_at = base_time + timedelta(minutes=interval)
    job.save(update_fields=["last_run_at", "next_run_at", "updated_at"])


def _normalize_positive_int(value, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


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


def _pick_expect_status(metadata: dict, expected_codes: list[int]) -> int:
    explicit = metadata.get("expect_status")
    try:
        parsed = int(explicit)
    except (TypeError, ValueError):
        parsed = None

    if parsed is not None and 100 <= parsed <= 599:
        return parsed
    return expected_codes[0]

