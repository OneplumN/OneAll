from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.tools.models import ScriptVersion, ToolDefinition


@dataclass
class ScriptRepositoryService:
    actor: object | None = None

    def _next_version(self, tool: ToolDefinition) -> str:
        latest = tool.versions.order_by("-created_at").first()
        if latest is None:
            return "v1"
        prefix = latest.version.rstrip("0123456789") or "v"
        suffix = latest.version[len(prefix) :]
        try:
            number = int(suffix)
        except ValueError:
            number = tool.versions.count() + 1
        else:
            number += 1
        return f"{prefix}{number}"

    @transaction.atomic
    def create_version(
        self,
        tool: ToolDefinition,
        *,
        content: str,
        language: ScriptVersion.Language = ScriptVersion.Language.PYTHON,
        repository_path: str = "",
        metadata: dict | None = None,
        version: str | None = None,
    ) -> ScriptVersion:
        version_label = version or self._next_version(tool)
        script_version = ScriptVersion.objects.create(
            tool=tool,
            version=version_label,
            language=language,
            repository_path=repository_path,
            content=content,
            metadata=metadata or {},
            created_by=self.actor,
            updated_by=self.actor,
        )
        tool.latest_version = script_version
        tool.updated_by = self.actor
        tool.save(update_fields=["latest_version", "updated_at", "updated_by"])
        return script_version

    @transaction.atomic
    def create_tool(
        self,
        *,
        name: str,
        category: str,
        tags: list[str] | None = None,
        description: str = "",
        entry_point: str = "",
        default_parameters: dict | None = None,
        initial_script: str,
        language: ScriptVersion.Language = ScriptVersion.Language.PYTHON,
    ) -> ToolDefinition:
        tool = ToolDefinition.objects.create(
            name=name,
            category=category,
            tags=tags or [],
            description=description,
            entry_point=entry_point,
            default_parameters=default_parameters or {},
            created_by=self.actor,
            updated_by=self.actor,
        )
        self.create_version(
            tool,
            content=initial_script,
            language=language,
        )
        return tool
