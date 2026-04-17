from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from apps.core.models.base import BaseModel


class DetectionTask(BaseModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        TIMEOUT = "timeout", "Timeout"

    class Protocol(models.TextChoices):
        HTTP = "HTTP", "HTTP"
        HTTPS = "HTTPS", "HTTPS"
        TELNET = "Telnet", "Telnet"
        WSS = "WSS", "WebSocket Secure"
        TCP = "TCP", "TCP"
        CERTIFICATE = "CERTIFICATE", "Certificate"

    target = models.CharField(max_length=512)
    protocol = models.CharField(max_length=16, choices=Protocol.choices)
    probe = models.ForeignKey(
        "probes.ProbeNode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detection_tasks",
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.SCHEDULED)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    status_code = models.CharField(max_length=32, blank=True)
    error_message = models.TextField(blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    requested_by = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "monitoring_detection_task"
        ordering = ("-created_at",)
        verbose_name = "Detection Task"
        verbose_name_plural = "Detection Tasks"

    def mark_running(self, *, published_at=None, claimed_at=None) -> None:
        self.status = self.Status.RUNNING
        if self.published_at is None:
            self.published_at = published_at or timezone.now()
        if self.claimed_at is None:
            self.claimed_at = claimed_at or timezone.now()
        self.save(update_fields=["status", "published_at", "claimed_at", "updated_at"])

    def mark_failed(
        self,
        message: str,
        *,
        response_time_ms: int | None = None,
        status_code: str | int | None = None,
        result_payload: dict | None = None,
        executed_at=None,
    ) -> None:
        self.status = self.Status.FAILED
        self.error_message = message
        self.response_time_ms = response_time_ms
        self.status_code = "" if status_code is None else str(status_code)
        if result_payload is not None:
            self.result_payload = result_payload
        self.executed_at = executed_at or timezone.now()
        self.save(
            update_fields=[
                "status",
                "error_message",
                "response_time_ms",
                "status_code",
                "result_payload",
                "executed_at",
                "updated_at",
            ]
        )

    def mark_timeout(
        self,
        *,
        message: str = "",
        response_time_ms: int | None = None,
        status_code: str | int | None = None,
        result_payload: dict | None = None,
        executed_at=None,
    ) -> None:
        self.status = self.Status.TIMEOUT
        self.error_message = message
        self.response_time_ms = response_time_ms
        self.status_code = "" if status_code is None else str(status_code)
        if result_payload is not None:
            self.result_payload = result_payload
        self.executed_at = executed_at or timezone.now()
        self.save(
            update_fields=[
                "status",
                "error_message",
                "response_time_ms",
                "status_code",
                "result_payload",
                "executed_at",
                "updated_at",
            ]
        )

    def mark_succeeded(
        self,
        response_time_ms: int | None,
        result_payload: dict | None = None,
        *,
        status_code: str | int | None = None,
        message: str = "",
        executed_at=None,
    ) -> None:
        self.status = self.Status.SUCCEEDED
        self.error_message = message
        self.response_time_ms = response_time_ms
        self.status_code = "" if status_code is None else str(status_code)
        if result_payload is not None:
            self.result_payload = result_payload
        self.executed_at = executed_at or timezone.now()
        self.save(
            update_fields=[
                "status",
                "error_message",
                "response_time_ms",
                "status_code",
                "result_payload",
                "executed_at",
                "updated_at",
            ]
        )
