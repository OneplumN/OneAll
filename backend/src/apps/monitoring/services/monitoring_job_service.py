from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from apps.alerts.services import ensure_schedule_for_monitoring_job
from apps.monitoring.models import MonitoringJob, MonitoringRequest
from apps.probes.services.probe_schedule_service import sync_schedule_from_job


def create_job_for_request(request: MonitoringRequest, schedule_cron: Optional[str] = None) -> MonitoringJob:
    job = MonitoringJob.objects.create(
        request=request,
        schedule_cron=schedule_cron or request.schedule_cron,
        frequency_minutes=request.frequency_minutes,
        status=MonitoringJob.Status.ACTIVE,
        metadata=_build_job_metadata(request),
        next_run_at=_initial_next_run_at(),
    )
    # Keep existing probe schedule in sync
    sync_schedule_from_job(job)
    # Mirror job into alerts check/schedule for central scheduling
    ensure_schedule_for_monitoring_job(job)
    return job


def sync_job_from_request(job: MonitoringJob, request: MonitoringRequest) -> MonitoringJob:
    update_fields: list[str] = []

    if job.schedule_cron != request.schedule_cron:
        job.schedule_cron = request.schedule_cron
        update_fields.append("schedule_cron")
    if job.frequency_minutes != request.frequency_minutes:
        job.frequency_minutes = request.frequency_minutes
        update_fields.append("frequency_minutes")

    metadata = _build_job_metadata(request)
    if (job.metadata or {}) != metadata:
        job.metadata = metadata
        update_fields.append("metadata")

    if job.next_run_at is None:
        job.next_run_at = _initial_next_run_at()
        update_fields.append("next_run_at")

    if update_fields:
        job.save(update_fields=[*update_fields, "updated_at"])
    return job


def schedule_next_run(job: MonitoringJob) -> None:
    if job.frequency_minutes:
        job.next_run_at = datetime.now(timezone.utc) + timedelta(minutes=job.frequency_minutes)
        job.save(update_fields=["next_run_at", "updated_at"])


def _build_job_metadata(request: MonitoringRequest) -> dict:
    return dict(request.metadata or {})


def _initial_next_run_at():
    return datetime.now(timezone.utc)
