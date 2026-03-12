from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class CodeDirectory(BaseModel):
    """Grouping metadata for script repositories."""

    key = models.SlugField(max_length=60, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    keywords = models.JSONField(default=list, blank=True)
    builtin = models.BooleanField(default=False)

    class Meta:
        db_table = "tools_code_directory"
        ordering = ("title",)
        verbose_name = "Code Directory"
        verbose_name_plural = "Code Directories"

    def __str__(self) -> str:
        return self.title
