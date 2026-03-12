from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class ToolDefinition(BaseModel):
    """Declarative description of a reusable automation tool/script."""

    name = models.CharField(max_length=150, unique=True)
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    entry_point = models.CharField(max_length=255, blank=True)
    default_parameters = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    latest_version = models.ForeignKey(
        "tools.ScriptVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="latest_for_tools",
    )

    class Meta:
        db_table = "tools_tool_definition"
        ordering = ("name",)
        verbose_name = "Tool Definition"
        verbose_name_plural = "Tool Definitions"

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return self.name
