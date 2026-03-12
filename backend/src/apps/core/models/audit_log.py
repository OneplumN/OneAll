from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """Immutable record describing user or system operations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=128)
    target_type = models.CharField(max_length=128, blank=True)
    target_id = models.CharField(max_length=128, blank=True)
    result = models.CharField(max_length=32, default="success")
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_audit_log"
        ordering = ("-occurred_at", "-created_at")
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["action", "occurred_at"], name="core_auditlog_act_occ_idx"),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.action} ({self.result})"
