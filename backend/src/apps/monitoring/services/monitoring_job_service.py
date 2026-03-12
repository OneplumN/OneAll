from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from apps.monitoring.models import MonitoringJob, MonitoringRequest
from apps.probes.services.probe_schedule_service import sync_schedule_from_job


def create_job_for_request(request: MonitoringRequest, schedule_cron: Optional[str] = None) -> MonitoringJob:
    job = MonitoringJob.objects.create(
        request=request,
        schedule_cron=schedule_cron or request.schedule_cron,
        frequency_minutes=request.frequency_minutes,
        status=MonitoringJob.Status.ACTIVE,
    )
    sync_schedule_from_job(job)
    return job


def schedule_next_run(job: MonitoringJob) -> None:
    if job.frequency_minutes:
        job.next_run_at = datetime.now(timezone.utc) + timedelta(minutes=job.frequency_minutes)
        job.save(update_fields=["next_run_at", "updated_at"])
