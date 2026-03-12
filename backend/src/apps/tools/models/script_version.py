from __future__ import annotations

import hashlib

from django.db import models

from apps.core.models.base import BaseModel


class ScriptVersion(BaseModel):
    """Versioned script content tracked for tool execution."""

    class Language(models.TextChoices):
        PYTHON = "python", "Python"
        SHELL = "shell", "Shell"
        POWERSHELL = "powershell", "PowerShell"
        OTHER = "other", "Other"

    tool = models.ForeignKey(
        "tools.ToolDefinition",
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version = models.CharField(max_length=40)
    language = models.CharField(max_length=20, choices=Language.choices, default=Language.PYTHON)
    repository_path = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    checksum = models.CharField(max_length=64, editable=False)

    class Meta:
        db_table = "tools_script_version"
        unique_together = ("tool", "version")
        ordering = ("tool", "-created_at")

    def save(self, *args, **kwargs):
        self.checksum = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.tool.name}#{self.version}"
