from __future__ import annotations

import logging

import contextlib
import io
import time
import traceback

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.tools.models import ToolExecution
from apps.tools.services.tool_runner import ToolRunnerService

logger = logging.getLogger(__name__)

MAX_OUTPUT_CHARS = 500_000


class ExecutionOutputStream(io.TextIOBase):
    def __init__(
        self,
        execution: ToolExecution,
        *,
        flush_interval_s: float = 0.6,
        flush_chunk_chars: int = 2048,
        max_chars: int = MAX_OUTPUT_CHARS,
    ) -> None:
        super().__init__()
        self._execution_id = execution.id
        self._buffer: list[str] = []
        self._buffer_size = 0
        self._last_flush = time.monotonic()
        self._flush_interval_s = flush_interval_s
        self._flush_chunk_chars = flush_chunk_chars
        self._max_chars = max_chars
        self._output = ""

    def writable(self) -> bool:  # pragma: no cover
        return True

    def write(self, s: str) -> int:  # type: ignore[override]
        if not s:
            return 0
        text = str(s)
        self._buffer.append(text)
        self._buffer_size += len(text)
        # 以“行”为粒度尽快落库，避免脚本长时间无输出时页面看不到增量。
        # print(...) 通常会分两次 write：内容 + "\n"；这里遇到换行就立即 flush。
        if "\n" in text or self._should_flush():
            self.flush()
        return len(text)

    def _should_flush(self) -> bool:
        if self._buffer_size >= self._flush_chunk_chars:
            return True
        return (time.monotonic() - self._last_flush) >= self._flush_interval_s

    def flush(self) -> None:  # type: ignore[override]
        if not self._buffer:
            return
        chunk = "".join(self._buffer)
        self._buffer.clear()
        self._buffer_size = 0
        self._last_flush = time.monotonic()
        self._append_and_persist(chunk)

    def _append_and_persist(self, chunk: str) -> None:
        self._output += chunk
        if len(self._output) > self._max_chars:
            self._output = self._output[-self._max_chars :]
        ToolExecution.objects.filter(id=self._execution_id).update(output=self._output, updated_at=timezone.now())

    @property
    def value(self) -> str:
        if self._buffer:
            self.flush()
        return self._output


@shared_task(name="apps.tools.tasks.run_tool")
def run_tool_task(run_id: str) -> dict[str, str]:
    try:
        execution = ToolExecution.objects.select_related("tool", "script_version").get(run_id=run_id)
    except ToolExecution.DoesNotExist:  # pragma: no cover - defensive
        logger.warning("ToolExecution with run_id=%s not found", run_id)
        return {"status": "missing"}

    runner = ToolRunnerService()
    runner.mark_running(execution)

    script_content = execution.script_version.content if execution.script_version else ""
    parameters = execution.parameters or {}

    stdout = ExecutionOutputStream(execution)
    success = False
    error_message = ""
    script_result: object | None = None

    if not script_content.strip():
        error_message = "脚本内容为空，无法执行。"
    else:
        try:
            namespace = {"__name__": "__main__", "CONFIG": parameters}
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
                exec(script_content, namespace)
                main_func = namespace.get("main")
                if callable(main_func):
                    script_result = main_func(parameters)
                else:
                    script_result = namespace.get("RESULT")
            success = True
        except Exception as exc:  # pragma: no cover - runtime errors
            error_message = f"{exc}\n{traceback.format_exc()}"
            logger.error("Tool execution failed: %s", error_message)

    # 资产类脚本：支持脚本直接返回 records（list[dict]）后自动入库，不再依赖 JSON 临时文件。
    asset_ingest: dict | None = None
    if success:
        plugin = str((parameters or {}).get("plugin") or "").strip()

        def _extract_records(value: object | None) -> list[dict] | None:
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value
            if isinstance(value, dict):
                candidate = value.get("records") or value.get("items")
                if isinstance(candidate, list) and all(isinstance(item, dict) for item in candidate):
                    return candidate
            return None

        records = _extract_records(script_result)
        if plugin.startswith("asset_") and records is not None:
            try:
                from apps.assets.services.sync_service import ASSET_PLUGIN_SCOPES, ingest_asset_snapshot

                full_snapshot = bool((parameters or {}).get("full_snapshot", False))
                if plugin in ASSET_PLUGIN_SCOPES:
                    full_snapshot = True

                with transaction.atomic():
                    stats = ingest_asset_snapshot(records, plugin=plugin, full_snapshot=full_snapshot)
                asset_ingest = {"plugin": plugin, **stats}
                ToolExecution.objects.filter(id=execution.id).update(
                    metadata={
                        **(execution.metadata or {}),
                        "asset_ingest": asset_ingest,
                    },
                    updated_at=timezone.now(),
                )
            except Exception as exc:  # pragma: no cover - ingestion errors
                success = False
                error_message = f"[资产入库失败] {exc}\n{traceback.format_exc()}"
                logger.error("Asset ingest failed for plugin=%s: %s", plugin, error_message)

    output_text = stdout.value
    if success and asset_ingest:
        output_text = (
            f"{output_text}\n[资产入库] plugin={asset_ingest.get('plugin')} "
            f"fetched={asset_ingest.get('fetched')} created={asset_ingest.get('created')} "
            f"updated={asset_ingest.get('updated')} removed={asset_ingest.get('removed')}"
        ).strip()
    if success and script_result is not None:
        rendered_result = script_result if isinstance(script_result, str) else str(script_result)
        if rendered_result.strip():
            output_text = f"{output_text}\n{rendered_result}".strip() if output_text else rendered_result
    if not output_text and success:
        output_text = f"[{timezone.now().isoformat()}] {execution.tool.name} executed."

    runner.mark_finished(execution, output=output_text, success=success, error=error_message or None)
    logger.info("Tool %s executed status=%s (run_id=%s)", execution.tool.name, execution.status, run_id)
    return {"status": execution.status}
