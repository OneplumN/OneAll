from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class KnowledgeArticleVersion(BaseModel):
    """Snapshot of a knowledge article for history tracking."""

    article = models.ForeignKey(
        "knowledge.KnowledgeArticle",
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    visibility_scope = models.CharField(max_length=32)
    content = models.TextField()
    summary = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "knowledge_article_version"
        ordering = ("-created_at",)
        unique_together = ("article", "version")
        verbose_name = "Knowledge Article Version"
        verbose_name_plural = "Knowledge Article Versions"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.article_id} v{self.version}"
