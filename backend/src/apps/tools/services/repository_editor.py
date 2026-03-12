from __future__ import annotations

import difflib
from dataclasses import dataclass

from django.db import transaction

from apps.tools.models import ScriptVersion, ToolDefinition
from apps.tools.services.script_repository import ScriptRepositoryService


@dataclass
class RepositoryEditorService:
    actor: object | None = None

    def diff(self, old: ScriptVersion, new_content: str) -> str:
        diff_lines = difflib.unified_diff(
            old.content.splitlines(),
            new_content.splitlines(),
            fromfile=f"{old.tool.name}@{old.version}",
            tofile="proposed",
            lineterm="",
        )
        return "\n".join(diff_lines)

    @transaction.atomic
    def update_content(
        self,
        tool: ToolDefinition,
        *,
        base_version: ScriptVersion,
        new_content: str,
        language: ScriptVersion.Language | None = None,
        repository_path: str | None = None,
    ) -> ScriptVersion:
        repo = ScriptRepositoryService(actor=self.actor)
        return repo.create_version(
            tool,
            content=new_content,
            language=language or base_version.language,
            repository_path=repository_path or base_version.repository_path,
            metadata={"source": "editor", "base_version": str(base_version.id)},
        )
