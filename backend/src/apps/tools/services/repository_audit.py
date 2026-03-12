from __future__ import annotations

from dataclasses import dataclass

from apps.core.models import AuditLog
from apps.core.middleware import sanitize_metadata
from apps.tools.models import ScriptVersion, ToolDefinition


@dataclass
class RepositoryAuditService:
    actor: object | None = None

    def log_upload(self, tool: ToolDefinition, version: ScriptVersion) -> None:
        AuditLog.objects.create(
            actor=self.actor,
            action="tools.repository.upload",
            target_type="tools.ToolDefinition",
            target_id=str(tool.id),
            metadata=sanitize_metadata({
                "version": version.version,
                "checksum": version.checksum,
            }),
        )

    def log_rollback(self, tool: ToolDefinition, version: ScriptVersion) -> None:
        AuditLog.objects.create(
            actor=self.actor,
            action="tools.repository.rollback",
            target_type="tools.ToolDefinition",
            target_id=str(tool.id),
            metadata=sanitize_metadata({
                "version": version.version,
            }),
        )
