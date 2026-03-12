from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class ScriptPlugin(BaseModel):
    """Represents a script-based plugin backed by the code repository module."""

    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    repository = models.ForeignKey(
        "tools.CodeRepository",
        on_delete=models.PROTECT,
        related_name="plugins",
    )
    repository_version = models.ForeignKey(
        "tools.CodeRepositoryVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plugin_bindings",
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_enabled = models.BooleanField(default=True)
    builtin = models.BooleanField(default=False)
    group = models.CharField(max_length=60, default="tools")
    route = models.CharField(max_length=255, blank=True)
    component = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)

    class Meta:
        db_table = "tools_script_plugin"
        verbose_name = "Script Plugin"
        verbose_name_plural = "Script Plugins"
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.slug})"
