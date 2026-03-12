from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class KnowledgeCategory(BaseModel):
  """Directory for knowledge base articles."""

  key = models.SlugField(max_length=80, unique=True)
  title = models.CharField(max_length=120)
  description = models.CharField(max_length=255, blank=True)
  builtin = models.BooleanField(default=False)
  display_order = models.PositiveIntegerField(default=0)

  class Meta:
    db_table = "knowledge_category"
    ordering = ("display_order", "title")
    verbose_name = "Knowledge Category"
    verbose_name_plural = "Knowledge Categories"

  def __str__(self) -> str:  # pragma: no cover
    return self.title
