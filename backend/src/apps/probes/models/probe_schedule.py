from __future__ import annotations

from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.core.models.base import BaseModel
from apps.monitoring.models import DetectionTask, MonitoringJob, MonitoringRequest


class ProbeSchedule(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        MONITORING_REQUEST = "monitoring_request", "Monitoring Request"

    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    target = models.CharField(max_length=512)
    protocol = models.CharField(max_length=16, choices=DetectionTask.Protocol.choices)
    frequency_minutes = models.PositiveIntegerField(default=5)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    status_reason = models.CharField(max_length=255, blank=True)
    source_type = models.CharField(max_length=32, choices=Source.choices, default=Source.MANUAL)
    source_id = models.UUIDField(null=True, blank=True)
    monitoring_request = models.OneToOneField(
        MonitoringRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="probe_schedule",
    )
    monitoring_job = models.OneToOneField(
        MonitoringJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="probe_schedule",
    )
    metadata = models.JSONField(default=dict, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)

    probes = models.ManyToManyField(
        "probes.ProbeNode",
        related_name="schedules",
        blank=True,
    )

    class Meta:
        db_table = "probes_probe_schedule"
        ordering = ("name",)
        verbose_name = "Probe Schedule"
        verbose_name_plural = "Probe Schedules"

    def activate(self) -> None:
        now = timezone.now()
        interval_minutes = self.frequency_minutes or 1
        self.status = self.Status.ACTIVE
        self.status_reason = ""
        update_fields = ["status", "status_reason", "updated_at"]
        if not self.next_run_at or self.next_run_at <= now:
            interval = timedelta(minutes=interval_minutes)
            base_time = self.start_at if self.start_at and self.start_at > now else now
            self.next_run_at = base_time + interval
            update_fields.append("next_run_at")
        self.save(update_fields=update_fields)

    def pause(self, reason: str | None = None) -> None:
        self.status = self.Status.PAUSED
        self.status_reason = reason or ""
        self.save(update_fields=["status", "status_reason", "updated_at"])

    def archive(self, reason: str | None = None) -> None:
        self.status = self.Status.ARCHIVED
        self.status_reason = reason or ""
        self.save(update_fields=["status", "status_reason", "updated_at"])
