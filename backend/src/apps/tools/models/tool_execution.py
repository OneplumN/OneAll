from __future__ import annotations

import uuid

from django.db import models

from apps.core.models.base import BaseModel


class ToolExecution(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    run_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    tool = models.ForeignKey("tools.ToolDefinition", on_delete=models.CASCADE, related_name="executions")
    script_version = models.ForeignKey(
        "tools.ScriptVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executions",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    parameters = models.JSONField(default=dict, blank=True)
    output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "tools_tool_execution"
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.tool.name}@{self.run_id}"
