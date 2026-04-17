from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class AlertEvent(BaseModel):
    """Represents a single alert instance raised by the monitoring/probes pipeline."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        SUPPRESSED = "suppressed", "Suppressed"

    source = models.CharField(max_length=64, help_text="Origin of the alert, e.g. monitoring, probes")
    event_type = models.CharField(max_length=64, help_text="Logical alert type, e.g. detection_failure")
    severity = models.CharField(max_length=32, default="warning")
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    # loosely reference related objects to avoid hard coupling
    related_task_id = models.UUIDField(null=True, blank=True)
    related_asset_id = models.UUIDField(null=True, blank=True)
    related_probe_id = models.UUIDField(null=True, blank=True)
    # snapshot of context at the time of alert
    context = models.JSONField(default=dict, blank=True)
    # delivery metadata
    channels = models.JSONField(default=list, blank=True, help_text="List of channel identifiers used")
    last_error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "alerts_event"
        verbose_name = "Alert Event"
        verbose_name_plural = "Alert Events"

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"[{self.severity}] {self.title}"


class AlertRule(BaseModel):
    """Simple alert rule bound to monitoring tasks/assets/probes."""

    class Scope(models.TextChoices):
        GLOBAL = "global", "Global"
        MONITORING_TASK = "monitoring_task", "Monitoring Task"
        ASSET = "asset", "Asset"
        PROBE = "probe", "Probe"

    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    scope = models.CharField(max_length=32, choices=Scope.choices, default=Scope.GLOBAL)
    # store identifiers as plain UUIDs/strings to decouple from concrete models
    target_id = models.CharField(max_length=64, blank=True)
    enabled = models.BooleanField(default=True)
    severity = models.CharField(max_length=32, default="warning")
    # simple threshold-like configuration, to be interpreted by alerts.services
    conditions = models.JSONField(default=dict, blank=True)
    channels = models.JSONField(default=list, blank=True, help_text="Preferred channels for this rule")

    class Meta:
        db_table = "alerts_rule"
        verbose_name = "Alert Rule"
        verbose_name_plural = "Alert Rules"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class AlertCheck(BaseModel):
    """Logical definition of what to check and how to execute it.

    This model is intentionally decoupled from concrete monitoring/probes models.
    `source_type`/`source_id` point back to the originating object
    (e.g. MonitoringRequest, ProbeSchedule).
    """

    class SourceType(models.TextChoices):
        MONITORING_REQUEST = "monitoring_request", "Monitoring Request"
        PROBE_SCHEDULE = "probe_schedule", "Probe Schedule"
        AD_HOC = "ad_hoc", "Ad-hoc"

    class ExecutorType(models.TextChoices):
        PROBE = "probe", "Probe"
        DIRECT = "direct", "Direct"

    name = models.CharField(max_length=128)
    target = models.CharField(max_length=512, help_text="Target to check, e.g. URL, host, or asset identifier")
    protocol = models.CharField(max_length=32, help_text="Protocol such as HTTP/HTTPS/TCP")
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    source_id = models.UUIDField(null=True, blank=True, help_text="UUID of originating object")
    executor_type = models.CharField(max_length=32, choices=ExecutorType.choices, default=ExecutorType.DIRECT)
    executor_config = models.JSONField(default=dict, blank=True, help_text="Backend-specific execution configuration")
    asset_id = models.UUIDField(null=True, blank=True, help_text="Optional related asset identifier")
    resolved_domain = models.CharField(max_length=255, blank=True)
    resolved_system_name = models.CharField(max_length=128, blank=True)
    asset_record_id = models.UUIDField(null=True, blank=True)
    asset_match_status = models.CharField(max_length=32, blank=True)

    class Meta:
        db_table = "alerts_check"
        verbose_name = "Alert Check"
        verbose_name_plural = "Alert Checks"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class AlertSchedule(BaseModel):
    """Schedule describing when an AlertCheck should be executed."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    alert_check = models.ForeignKey(
        AlertCheck,
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    cron_expression = models.CharField(max_length=64, blank=True)
    frequency_minutes = models.PositiveIntegerField(default=5)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "alerts_check_schedule"
        verbose_name = "Alert Check Schedule"
        verbose_name_plural = "Alert Check Schedules"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.alert_check.name} ({self.frequency_minutes}m)"


class AlertCheckExecution(BaseModel):
    """Represents a single execution of an AlertSchedule."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        TIMEOUT = "timeout", "Timeout"
        MISSED = "missed", "Missed"

    schedule = models.ForeignKey(
        AlertSchedule,
        on_delete=models.CASCADE,
        related_name="executions",
    )
    executor_type = models.CharField(
        max_length=32,
        choices=AlertCheck.ExecutorType.choices,
        default=AlertCheck.ExecutorType.DIRECT,
    )
    executor_ref = models.CharField(
        max_length=128,
        blank=True,
        help_text="Opaque identifier of the concrete executor (e.g. ProbeNode id)",
    )
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.SCHEDULED)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    status_code = models.CharField(max_length=32, blank=True)
    error_message = models.TextField(blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    # Back-reference to original execution record if needed
    source_type = models.CharField(max_length=32, blank=True)
    source_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "alerts_check_execution"
        verbose_name = "Alert Check Execution"
        verbose_name_plural = "Alert Check Executions"
        indexes = [
            models.Index(fields=["schedule", "scheduled_at"]),
            models.Index(fields=["executor_type", "executor_ref", "scheduled_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.schedule_id} @ {self.scheduled_at.isoformat()}"
