from __future__ import annotations

from typing import Iterable

from apps.alerts.services import ensure_schedule_for_probe_schedule
from apps.monitoring.models import MonitoringJob
from apps.probes.models import ProbeNode, ProbeSchedule


def sync_schedule_from_job(job: MonitoringJob) -> ProbeSchedule:
    request = job.request
    metadata = request.metadata or {}

    defaults = {
        "monitoring_request": request,
        "name": request.title,
        "description": request.description or "",
        "target": request.target,
        "protocol": request.protocol,
        "frequency_minutes": job.frequency_minutes or request.frequency_minutes,
        "metadata": metadata,
        "source_type": ProbeSchedule.Source.MONITORING_REQUEST,
        "source_id": request.id,
        "status": ProbeSchedule.Status.ACTIVE
        if request.status == request.Status.APPROVED
        else ProbeSchedule.Status.PAUSED,
    }

    schedule, _ = ProbeSchedule.objects.update_or_create(
        monitoring_job=job,
        defaults=defaults,
    )

    probe_ids = _extract_probe_ids(metadata.get("probe_ids"))
    if probe_ids:
        probes = list(ProbeNode.objects.filter(id__in=probe_ids))
        schedule.probes.set(probes)
    else:
        schedule.probes.clear()

    if job.next_run_at:
        schedule.next_run_at = job.next_run_at
    schedule.save(update_fields=[
        "monitoring_request",
        "name",
        "description",
        "target",
        "protocol",
        "frequency_minutes",
        "metadata",
        "source_type",
        "source_id",
        "status",
        "next_run_at",
        "updated_at",
    ])
    # Mirror probe schedule into alerts check/schedule
    ensure_schedule_for_probe_schedule(schedule)
    return schedule


def update_schedule_runtime(job: MonitoringJob, *, last_run_at, next_run_at) -> None:
    schedule = getattr(job, "probe_schedule", None)
    if not schedule:
        return
    schedule.last_run_at = last_run_at
    schedule.next_run_at = next_run_at
    schedule.save(update_fields=["last_run_at", "next_run_at", "updated_at"])


def _extract_probe_ids(raw: Iterable | None) -> list[str]:
    if not raw:
        return []
    normalized: list[str] = []
    for value in raw:
        if not value:
            continue
        normalized.append(str(value))
    return normalized
