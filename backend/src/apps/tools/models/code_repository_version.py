from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class CodeRepositoryVersion(BaseModel):
    """Historical snapshot of a repository script."""

    repository = models.ForeignKey(
        "tools.CodeRepository",
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version = models.CharField(max_length=40)
    summary = models.CharField(max_length=255, blank=True)
    change_log = models.TextField(blank=True)
    content = models.TextField()

    class Meta:
        db_table = "tools_code_repository_version"
        ordering = ("repository", "-created_at")
        unique_together = ("repository", "version")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.repository.name}#{self.version}"
