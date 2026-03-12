from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.tools.models import ToolExecution


@shared_task(name="apps.tools.tasks.tool_usage_metrics")
def tool_usage_metrics() -> dict[str, int]:
    since = timezone.now() - timedelta(days=30)
    executions = ToolExecution.objects.filter(created_at__gte=since)
    total = executions.count()
    tools = executions.values_list("tool__name", flat=True)
    usage: dict[str, int] = {}
    for name in tools:
        usage[name] = usage.get(name, 0) + 1
    return {"window_days": 30, "total": total, "by_tool": usage}
