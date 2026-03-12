from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction

from apps.tools.models import CodeRepository, CodeRepositoryVersion, ScriptVersion, ToolDefinition
from apps.tools.services.tool_runner import ToolRunnerService


class RepositoryExecutionError(RuntimeError):
    """Raised when a repository script cannot be executed."""


@dataclass
class RepositoryExecutionService:
    actor: object | None = None

    def execute(
        self,
        repository: CodeRepository,
        *,
        parameters: dict[str, Any] | None = None,
        repository_version: CodeRepositoryVersion | None = None,
    ):
        latest_version = repository_version or repository.latest_version
        if latest_version is None:
            raise RepositoryExecutionError("脚本仓库暂无版本，无法执行。")
        tool = self._ensure_tool(repository)
        script_version = self._ensure_script_version(tool, latest_version, repository)
        runner = ToolRunnerService(actor=self.actor)
        return runner.enqueue(tool, parameters=parameters or {}, script_version=script_version)

    def _ensure_tool(self, repository: CodeRepository) -> ToolDefinition:
        repo_id = str(repository.id)
        tool = ToolDefinition.objects.filter(metadata__repository_id=repo_id).first()
        if tool:
            return tool
        tool = ToolDefinition.objects.create(
            name=f"[脚本仓库] {repository.name}",
            category=repository.directory.title if repository.directory else "code-repo",
            tags=repository.tags,
            description=repository.description,
            metadata={"repository_id": repo_id},
            created_by=self.actor,
            updated_by=self.actor,
        )
        return tool

    @transaction.atomic
    def _ensure_script_version(
        self,
        tool: ToolDefinition,
        repo_version: CodeRepositoryVersion,
        repository: CodeRepository,
    ) -> ScriptVersion:
        repo_version_id = str(repo_version.id)
        existing = tool.versions.filter(metadata__repository_version_id=repo_version_id).first()
        if existing:
            if tool.latest_version_id != existing.id:
                tool.latest_version = existing
                tool.save(update_fields=["latest_version", "updated_at", "updated_by"])
            return existing

        script_version = ScriptVersion.objects.create(
            tool=tool,
            version=repo_version.version or f"repo-{repo_version_id}",
            language=self._map_language(repository.language),
            repository_path=repository.directory.title if repository.directory else "",
            content=repo_version.content,
            metadata={
                "repository_id": str(repository.id),
                "repository_version_id": repo_version_id,
            },
            created_by=self.actor,
            updated_by=self.actor,
        )
        tool.latest_version = script_version
        tool.save(update_fields=["latest_version", "updated_at", "updated_by"])
        return script_version

    def _map_language(self, language: str | None) -> str:
        if not language:
            return ScriptVersion.Language.PYTHON
        normalized = language.lower()
        if normalized in ("shell", "bash"):
            return ScriptVersion.Language.SHELL
        if normalized == "powershell":
            return ScriptVersion.Language.POWERSHELL
        if normalized == "python":
            return ScriptVersion.Language.PYTHON
        return ScriptVersion.Language.OTHER
