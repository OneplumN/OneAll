from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class KnowledgeArticle(BaseModel):
    """Knowledge base article with tagging and permissions."""

    class Visibility(models.TextChoices):
        INTERNAL = "internal", "内部可见"
        TEAM = "team", "团队内"
        PUBLIC = "public", "公开"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    content = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    visibility_scope = models.CharField(max_length=32, choices=Visibility.choices, default=Visibility.INTERNAL)
    last_editor = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="edited_articles",
    )
    last_edited_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "knowledge_article"
        ordering = ("-last_edited_at",)
        verbose_name = "Knowledge Article"
        verbose_name_plural = "Knowledge Articles"

    def __str__(self) -> str:  # pragma: no cover
        return self.title
