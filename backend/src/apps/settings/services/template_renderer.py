from __future__ import annotations

from string import Template
from typing import Any, Mapping

ALERT_VARIABLES = {
    "title": "告警标题",
    "severity": "严重级别，例如 critical、warning",
    "status": "状态，如 triggered、resolved",
    "timestamp": "触发时间（ISO 字符串）",
    "task_name": "任务名称",
    "probe_name": "探针名称",
    "message": "告警描述或错误信息",
    "result_url": "控制台查看详情的链接",
}


class AlertTemplateError(ValueError):
    pass


def validate_alert_template(body: str) -> None:
    try:
        Template(body)
    except ValueError as exc:  # pragma: no cover - validation branch
        raise AlertTemplateError(str(exc)) from exc


def render_alert_template(body: str, context: Mapping[str, Any]) -> str:
    try:
        return Template(body).safe_substitute({k: context.get(k, "") for k in ALERT_VARIABLES})
    except Exception as exc:  # pragma: no cover - rendering safety
        raise AlertTemplateError(f"模板渲染失败: {exc}") from exc
