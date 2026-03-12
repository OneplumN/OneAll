from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.db import transaction

from apps.knowledge.models import KnowledgeArticle
from apps.tools.models import ToolExecution


@dataclass
class ToolResultSyncService:
    actor: object | None = None

    @transaction.atomic
    def sync_execution_result(
        self,
        execution: ToolExecution,
        *,
        article_slug: str,
        summary: str | None = None,
    ) -> KnowledgeArticle:
        article, _ = KnowledgeArticle.objects.get_or_create(
            slug=article_slug,
            defaults={
                "title": summary or execution.tool.name,
                "content": execution.output or execution.error_message or "",
                "tags": ["tool", execution.tool.name],
                "created_by": self.actor,
                "last_editor": self.actor,
            },
        )
        if summary:
            article.title = summary
        article.content = execution.output or execution.error_message or article.content
        article.last_editor = self.actor
        article.save(update_fields=["title", "content", "last_editor", "updated_at"])
        return article
