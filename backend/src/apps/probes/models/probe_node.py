from __future__ import annotations

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

from apps.core.models.base import BaseModel


class ProbeNode(BaseModel):
    NETWORK_TYPES = (
        ("internal", "内网"),
        ("external", "外网"),
    )
    STATUS_CHOICES = (
        ("online", "在线"),
        ("offline", "离线"),
        ("maintenance", "维护"),
    )

    name = models.CharField(max_length=128, unique=True)
    location = models.CharField(max_length=128)
    network_type = models.CharField(max_length=32, choices=NETWORK_TYPES)
    supported_protocols = models.JSONField(default=list)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="offline")
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    last_authenticated_at = models.DateTimeField(null=True, blank=True)
    runtime_metrics = models.JSONField(default=dict, blank=True)
    api_token_hash = models.CharField(max_length=128, blank=True, default="")
    api_token_hint = models.CharField(max_length=8, blank=True, default="")
    agent_config = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "probes_probe_node"
        verbose_name = "Probe Node"
        verbose_name_plural = "Probe Nodes"

    def __str__(self) -> str:  # pragma: no cover - repr utility
        return f"{self.name} [{self.get_status_display()}]"

    # Token helpers
    def set_api_token(self, token: str) -> None:
        if not token:
            raise ValueError("Token cannot be empty")
        self.api_token_hash = make_password(token)
        self.api_token_hint = token[-4:]
        self.save(update_fields=["api_token_hash", "api_token_hint", "updated_at"])

    def check_api_token(self, token: str) -> bool:
        if not self.api_token_hash or not token:
            return False
        return check_password(token, self.api_token_hash)

    def touch_authenticated(self) -> None:
        now = timezone.now()
        self.last_authenticated_at = now
        ProbeNode.objects.filter(id=self.id).update(last_authenticated_at=now, updated_at=now)
