from __future__ import annotations

from dataclasses import dataclass

from apps.core.middleware import sanitize_metadata
from apps.core.models import AuditLog
from apps.tools.models import ScriptVersion, ToolExecution


@dataclass
class ToolAuditService:
    actor: object | None = None

    def log_execution(self, execution: ToolExecution) -> None:
        AuditLog.objects.create(
            actor=self.actor,
            action="tools.execution.enqueue",
            target_type="tools.ToolDefinition",
            target_id=str(execution.tool.id),
            metadata=sanitize_metadata({
                "run_id": str(execution.run_id),
                "parameters_keys": list((execution.parameters or {}).keys()),
            }),
        )

    def log_script_view(self, version: ScriptVersion) -> None:
        AuditLog.objects.create(
            actor=self.actor,
            action="tools.script.view",
            target_type="tools.ScriptVersion",
            target_id=str(version.id),
            metadata=sanitize_metadata({
                "tool": str(version.tool.id),
                "version": version.version,
            }),
        )
