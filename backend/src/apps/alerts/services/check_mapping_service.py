from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.db import transaction

from apps.alerts.models import AlertCheck, AlertSchedule
from apps.monitoring.models import MonitoringJob, MonitoringRequest
from apps.probes.models import ProbeSchedule

from .check_target_resolution_service import apply_resolution_snapshot


@dataclass
class MappingResult:
    check: AlertCheck
    schedule: Optional[AlertSchedule] = None


@transaction.atomic
def ensure_check_for_monitoring_request(request: MonitoringRequest) -> AlertCheck:
    """Get or create an AlertCheck for the given MonitoringRequest."""

    # Target/protocol come directly from the request
    defaults = {
        "name": request.title,
        "target": request.target,
        "protocol": request.protocol,
        "executor_type": AlertCheck.ExecutorType.DIRECT,
    }
    check, _ = AlertCheck.objects.get_or_create(
        source_type=AlertCheck.SourceType.MONITORING_REQUEST,
        source_id=request.id,
        defaults=defaults,
    )
    # Keep basic fields in sync on subsequent calls
    updated = False
    if check.name != request.title:
        check.name = request.title
        updated = True
    if check.target != request.target:
        check.target = request.target
        updated = True
    if check.protocol != request.protocol:
        check.protocol = request.protocol
        updated = True
    if updated:
        check.save(update_fields=["name", "target", "protocol", "updated_at"])
    return apply_resolution_snapshot(check)


@transaction.atomic
def ensure_schedule_for_monitoring_job(job: MonitoringJob) -> MappingResult:
    """Get or create AlertCheck/AlertSchedule for a MonitoringJob."""

    check = ensure_check_for_monitoring_request(job.request)

    defaults = {
        "cron_expression": job.schedule_cron,
        "frequency_minutes": job.frequency_minutes,
        "status": map_status(job.status),
        "start_at": None,
        "end_at": None,
        "last_run_at": job.last_run_at,
        "next_run_at": job.next_run_at,
        "metadata": dict(job.metadata or {}),
    }
    schedule, _ = AlertSchedule.objects.get_or_create(
        alert_check=check,
        # A MonitoringJob maps 1:1 to an AlertSchedule
        defaults=defaults,
    )

    # Sync mutable fields on subsequent calls
    updated_fields = []
    if schedule.cron_expression != job.schedule_cron:
        schedule.cron_expression = job.schedule_cron
        updated_fields.append("cron_expression")
    if schedule.frequency_minutes != job.frequency_minutes:
        schedule.frequency_minutes = job.frequency_minutes
        updated_fields.append("frequency_minutes")
    desired_status = map_status(job.status)
    if schedule.status != desired_status:
        schedule.status = desired_status
        updated_fields.append("status")
    if schedule.last_run_at != job.last_run_at:
        schedule.last_run_at = job.last_run_at
        updated_fields.append("last_run_at")
    if schedule.next_run_at != job.next_run_at:
        schedule.next_run_at = job.next_run_at
        updated_fields.append("next_run_at")
    if (schedule.metadata or {}) != (job.metadata or {}):
        schedule.metadata = dict(job.metadata or {})
        updated_fields.append("metadata")

    if updated_fields:
        updated_fields.append("updated_at")
        schedule.save(update_fields=updated_fields)

    return MappingResult(check=check, schedule=schedule)


@transaction.atomic
def ensure_check_for_probe_schedule(schedule: ProbeSchedule) -> AlertCheck:
    """Get or create an AlertCheck for the given ProbeSchedule."""

    defaults = {
        "name": schedule.name,
        "target": schedule.target,
        "protocol": schedule.protocol,
        "executor_type": AlertCheck.ExecutorType.PROBE,
    }
    check, _ = AlertCheck.objects.get_or_create(
        source_type=AlertCheck.SourceType.PROBE_SCHEDULE,
        source_id=schedule.id,
        defaults=defaults,
    )

    updated = False
    if check.name != schedule.name:
        check.name = schedule.name
        updated = True
    if check.target != schedule.target:
        check.target = schedule.target
        updated = True
    if check.protocol != schedule.protocol:
        check.protocol = schedule.protocol
        updated = True
    if updated:
        check.save(update_fields=["name", "target", "protocol", "updated_at"])
    return apply_resolution_snapshot(check)


@transaction.atomic
def ensure_schedule_for_probe_schedule(schedule: ProbeSchedule) -> MappingResult:
    """Get or create AlertCheck/AlertSchedule for a ProbeSchedule."""

    check = ensure_check_for_probe_schedule(schedule)

    defaults = {
        "cron_expression": "",
        "frequency_minutes": schedule.frequency_minutes,
        "status": map_status(schedule.status),
        "start_at": schedule.start_at,
        "end_at": schedule.end_at,
        "last_run_at": schedule.last_run_at,
        "next_run_at": schedule.next_run_at,
        "metadata": dict(schedule.metadata or {}),
    }
    alert_schedule, _ = AlertSchedule.objects.get_or_create(
        alert_check=check,
        defaults=defaults,
    )

    updated_fields = []
    if alert_schedule.frequency_minutes != schedule.frequency_minutes:
        alert_schedule.frequency_minutes = schedule.frequency_minutes
        updated_fields.append("frequency_minutes")
    desired_status = map_status(schedule.status)
    if alert_schedule.status != desired_status:
        alert_schedule.status = desired_status
        updated_fields.append("status")
    if alert_schedule.start_at != schedule.start_at:
        alert_schedule.start_at = schedule.start_at
        updated_fields.append("start_at")
    if alert_schedule.end_at != schedule.end_at:
        alert_schedule.end_at = schedule.end_at
        updated_fields.append("end_at")
    if alert_schedule.last_run_at != schedule.last_run_at:
        alert_schedule.last_run_at = schedule.last_run_at
        updated_fields.append("last_run_at")
    if alert_schedule.next_run_at != schedule.next_run_at:
        alert_schedule.next_run_at = schedule.next_run_at
        updated_fields.append("next_run_at")
    if (alert_schedule.metadata or {}) != (schedule.metadata or {}):
        alert_schedule.metadata = dict(schedule.metadata or {})
        updated_fields.append("metadata")

    if updated_fields:
        updated_fields.append("updated_at")
        alert_schedule.save(update_fields=updated_fields)

    return MappingResult(check=check, schedule=alert_schedule)


def map_status(source_status: str) -> str:
    """Map monitoring/probes status enums into AlertSchedule.Status values."""

    if source_status == MonitoringJob.Status.PAUSED or source_status == ProbeSchedule.Status.PAUSED:
        return AlertSchedule.Status.PAUSED
    if source_status == MonitoringJob.Status.ARCHIVED or source_status == ProbeSchedule.Status.ARCHIVED:
        return AlertSchedule.Status.ARCHIVED
    # Default everything else to ACTIVE
    return AlertSchedule.Status.ACTIVE
