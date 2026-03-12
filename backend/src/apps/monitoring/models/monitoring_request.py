from __future__ import annotations

import uuid

from django.db import models

from apps.core.models.base import BaseModel


class MonitoringRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    class Protocol(models.TextChoices):
        HTTP = "HTTP", "HTTP"
        HTTPS = "HTTPS", "HTTPS"
        TELNET = "Telnet", "Telnet"
        WSS = "WSS", "WebSocket Secure"
        CERTIFICATE = "CERTIFICATE", "Certificate"

    title = models.CharField(max_length=128)
    target = models.CharField(max_length=512)
    protocol = models.CharField(max_length=16, choices=Protocol.choices, default=Protocol.HTTPS)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    frequency_minutes = models.PositiveIntegerField(default=15)
    schedule_cron = models.CharField(max_length=64, blank=True)
    itsm_ticket_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "monitoring_request"
        ordering = ("-created_at",)
        verbose_name = "Monitoring Request"
        verbose_name_plural = "Monitoring Requests"

    def mark_approved(self, approver: str | None = None) -> None:
        self.status = self.Status.APPROVED
        if approver:
            meta = self.metadata or {}
            meta["approver"] = approver
            self.metadata = meta
        self.save(update_fields=["status", "metadata", "updated_at"])

    def mark_rejected(self, reason: str | None = None) -> None:
        self.status = self.Status.REJECTED
        if reason:
            meta = self.metadata or {}
            meta["reject_reason"] = reason
            self.metadata = meta
        self.save(update_fields=["status", "metadata", "updated_at"])
