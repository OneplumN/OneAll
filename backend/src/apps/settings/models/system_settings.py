from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel

ZABBIX_REFRESH_INTERVALS = [30, 60, 300, 900, 1800, 3600]


class SystemSettings(BaseModel):
    platform_name = models.CharField(max_length=128, default="OneAll 智能运维平台")
    platform_logo = models.TextField(blank=True, default="")
    default_timezone = models.CharField(max_length=64, default="Asia/Shanghai")
    alert_escalation_threshold = models.PositiveIntegerField(default=60)
    zabbix_dashboard_refresh_seconds = models.PositiveIntegerField(default=60, choices=[(value, value) for value in ZABBIX_REFRESH_INTERVALS])
    certificate_expiry_threshold_critical_days = models.PositiveIntegerField(default=15)
    certificate_expiry_threshold_warning_days = models.PositiveIntegerField(default=30)
    certificate_expiry_threshold_notice_days = models.PositiveIntegerField(default=45)
    theme = models.CharField(max_length=32, default="light")
    notification_channels = models.JSONField(default=dict, blank=True)
    integrations = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "settings_system_settings"
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.platform_name
