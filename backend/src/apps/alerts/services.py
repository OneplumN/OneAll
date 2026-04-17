from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from apps.alerts.models import AlertCheck, AlertCheckExecution, AlertEvent, AlertSchedule
from apps.monitoring.models import MonitoringJob, MonitoringRequest
from apps.probes.models import ProbeSchedule


@dataclass
class CheckResult:
    """Lightweight representation of a monitoring/probe check outcome.

    This is intentionally decoupled from concrete models so monitoring/probes
    can pass in just the data alerts needs.
    """

    source: str
    event_type: str
    severity: str
    title: str
    message: str | None
    status: str
    task_id: Optional[str] = None
    asset_id: Optional[str] = None
    probe_id: Optional[str] = None
    context: Dict[str, Any] | None = None


def evaluate_and_raise(result: CheckResult) -> AlertEvent:
    """Create a minimal AlertEvent based on a completed check result.

    This is a first version that simply stores the event; rule evaluation and
    channel routing will be expanded later.
    """

    event = AlertEvent.objects.create(
        source=result.source,
        event_type=result.event_type,
        severity=result.severity,
        title=result.title,
        message=result.message or "",
        status=AlertEvent.Status.PENDING,
        related_task_id=result.task_id,
        related_asset_id=result.asset_id,
        related_probe_id=result.probe_id,
        context=result.context or {},
        channels=[],
    )
    return event


def mark_event_sent(event: AlertEvent, *, channels: list[str]) -> AlertEvent:
    """Helper to mark an event as successfully delivered."""

    event.status = AlertEvent.Status.SENT
    event.channels = channels
    event.sent_at = timezone.now()
    event.last_error = ""
    event.save(update_fields=["status", "channels", "sent_at", "last_error", "updated_at"])
    return event


def mark_event_failed(event: AlertEvent, *, error_message: str) -> AlertEvent:
    """Helper to mark an event as failed to deliver."""

    event.status = AlertEvent.Status.FAILED
    event.last_error = error_message
    event.save(update_fields=["status", "last_error", "updated_at"])
    return event


@dataclass
class MappingResult:
    check: AlertCheck
    schedule: Optional[AlertSchedule] = None


@transaction.atomic
def ensure_check_for_monitoring_request(request: MonitoringRequest) -> AlertCheck:
    """Get or create an AlertCheck for the given MonitoringRequest."""

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
    return check


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
        defaults=defaults,
    )

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
    return check


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
    return AlertSchedule.Status.ACTIVE
