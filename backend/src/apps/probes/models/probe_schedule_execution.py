from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from apps.core.models.base import BaseModel
from apps.probes.models import ProbeNode, ProbeSchedule


class ProbeScheduleExecution(BaseModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        MISSED = "missed", "Missed"

    STATUS_ALIASES = {
        Status.SUCCEEDED: {"success", "successes", "succeed"},
        Status.FAILED: {"failure", "error"},
        Status.MISSED: {"timeout"},
    }
    STATUS_VALUE_SET = {choice.value for choice in Status}
    STATUS_ALIAS_LOOKUP = {
        alias: canonical
        for canonical, aliases in STATUS_ALIASES.items()
        for alias in aliases
    }

    @classmethod
    def normalize_status(cls, value: str | None) -> str:
        if not value:
            return cls.Status.FAILED
        normalized = value.lower()
        if normalized in cls.STATUS_VALUE_SET:
            return normalized
        return cls.STATUS_ALIAS_LOOKUP.get(normalized, normalized)

    @classmethod
    def status_aliases(cls, canonical: str) -> list[str]:
        return list(cls.STATUS_ALIASES.get(canonical, []))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(
        ProbeSchedule,
        on_delete=models.CASCADE,
        related_name="executions",
    )
    probe = models.ForeignKey(
        ProbeNode,
        on_delete=models.CASCADE,
        related_name="schedule_executions",
    )
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.SCHEDULED)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    status_code = models.CharField(max_length=16, blank=True)
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "probes_schedule_execution"
        verbose_name = "Probe Schedule Execution"
        verbose_name_plural = "Probe Schedule Executions"
        indexes = [
            models.Index(fields=["schedule", "scheduled_at"]),
            models.Index(fields=["probe", "scheduled_at"]),
        ]

    @classmethod
    def record_result(
        cls,
        *,
        schedule: ProbeSchedule,
        probe: ProbeNode,
        scheduled_at,
        status: str,
        response_time_ms: int | None = None,
        status_code: str | None = None,
        message: str | None = None,
        metadata: dict | None = None,
    ) -> ProbeScheduleExecution:
        execution, _ = cls.objects.get_or_create(
            schedule=schedule,
            probe=probe,
            scheduled_at=scheduled_at,
            defaults={
                "status": cls.Status.RUNNING,
                "started_at": timezone.now(),
            },
        )
        update_fields = ["status", "response_time_ms", "status_code", "message", "metadata", "finished_at", "updated_at"]
        execution.status = status
        execution.response_time_ms = response_time_ms
        execution.status_code = status_code or ""
        execution.message = message or ""
        execution.metadata = metadata or {}
        execution.finished_at = timezone.now()
        execution.save(update_fields=update_fields)
        return execution
