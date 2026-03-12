from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from django.utils import timezone

from apps.tools.models import ScriptVersion, ToolDefinition, ToolExecution
from apps.tools.services.tool_audit import ToolAuditService

logger = logging.getLogger(__name__)


@dataclass
class ToolRunnerService:
    actor: object | None = None

    def enqueue(
        self,
        tool: ToolDefinition,
        *,
        parameters: dict[str, Any] | None = None,
        script_version: ScriptVersion | None = None,
    ) -> ToolExecution:
        script = script_version or tool.latest_version
        execution = ToolExecution.objects.create(
            tool=tool,
            script_version=script,
            parameters=parameters or {},
            status=ToolExecution.Status.PENDING,
            created_by=self.actor,
            updated_by=self.actor,
        )
        ToolAuditService(actor=self.actor).log_execution(execution)
        from apps.tools.tasks.run_tool_task import run_tool_task  # local import to avoid circular

        try:
            run_tool_task.delay(str(execution.run_id))
        except Exception as exc:  # pragma: no cover - network/config errors
            logger.warning("Failed to enqueue tool execution; Celery unavailable, waiting for manual trigger.", exc_info=exc)
        return execution

    def mark_running(self, execution: ToolExecution) -> None:
        execution.status = ToolExecution.Status.RUNNING
        execution.started_at = timezone.now()
        execution.save(update_fields=["status", "started_at", "updated_at"])

    def mark_finished(self, execution: ToolExecution, *, output: str, success: bool, error: str | None = None) -> None:
        execution.status = ToolExecution.Status.SUCCEEDED if success else ToolExecution.Status.FAILED
        execution.output = output
        execution.error_message = error or ""
        execution.finished_at = timezone.now()
        execution.save(update_fields=["status", "output", "error_message", "finished_at", "updated_at"])
