from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel
from apps.tools.models.code_directory import CodeDirectory


class CodeRepository(BaseModel):
    """Source-managed script used by the code management module."""

    class Language(models.TextChoices):
        PYTHON = "python", "Python"
        SHELL = "shell", "Shell"
        POWERSHELL = "powershell", "PowerShell"
        BASH = "bash", "Bash"
        GO = "go", "Go"
        JAVASCRIPT = "javascript", "JavaScript"
        TYPESCRIPT = "typescript", "TypeScript"
        JAVA = "java", "Java"
        XML = "xml", "XML"
        YAML = "yaml", "YAML"
        JSON = "json", "JSON"
        SQL = "sql", "SQL"
        OTHER = "other", "Other"

    name = models.CharField(max_length=150, unique=True)
    language = models.CharField(max_length=40, choices=Language.choices, default=Language.PYTHON)
    tags = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    directory = models.ForeignKey(CodeDirectory, on_delete=models.PROTECT, related_name="repositories")
    latest_version = models.ForeignKey(
        "tools.CodeRepositoryVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    content = models.TextField(blank=True)

    class Meta:
        db_table = "tools_code_repository"
        ordering = ("name",)
        verbose_name = "Code Repository"
        verbose_name_plural = "Code Repositories"

    def __str__(self) -> str:  # pragma: no cover
        return self.name
