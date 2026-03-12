from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class MonitoringJob(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    request = models.ForeignKey(
        "monitoring.MonitoringRequest",
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    schedule_cron = models.CharField(max_length=64, blank=True)
    frequency_minutes = models.PositiveIntegerField(default=15)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "monitoring_job"
        ordering = ("-created_at",)
        verbose_name = "Monitoring Job"
        verbose_name_plural = "Monitoring Jobs"
