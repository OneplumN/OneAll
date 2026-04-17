from __future__ import annotations

import logging
from typing import Iterable, Sequence

from django.conf import settings
from django.utils import timezone

from apps.alerts.services import CheckResult, evaluate_and_raise
from apps.alerts.tasks import dispatch_alert_event
from apps.core.models import AuditLog
from apps.probes.models import ProbeScheduleExecution
from apps.settings.services.system_settings_service import get_system_settings

logger = logging.getLogger(__name__)

FAILURE_STATUSES = {
    ProbeScheduleExecution.Status.FAILED,
    ProbeScheduleExecution.Status.MISSED,
}
ALERT_LOG_ACTION = "probes.alert"


def evaluate_probe_alert(execution: ProbeScheduleExecution) -> None:
    """Evaluate whether the given execution should trigger an alert."""

    if execution.status not in FAILURE_STATUSES:
        return

    threshold = _resolve_threshold(execution)
    if threshold <= 0:
        return

    failures = _collect_failure_window(execution, threshold)
    if len(failures) < threshold:
        return

    if failures[0].id != execution.id:
        # Only the most recent execution should fan out the alert.
        return

    if any(item.status not in FAILURE_STATUSES for item in failures):
        return

    if _alert_already_recorded(execution):
        return

    contacts = _resolve_contacts(execution)
    context = _build_context(execution, contacts, threshold)

    _record_alert(execution, failures, threshold, contacts, context)


def _resolve_threshold(execution: ProbeScheduleExecution) -> int:
    metadata = execution.schedule.metadata or {}
    value = metadata.get("alert_threshold")
    try:
        threshold = int(value)
    except (TypeError, ValueError):
        threshold = 1
    return max(threshold, 1)


def _collect_failure_window(execution: ProbeScheduleExecution, threshold: int) -> list[ProbeScheduleExecution]:
    return list(
        ProbeScheduleExecution.objects.filter(
            schedule=execution.schedule,
            probe=execution.probe,
            scheduled_at__lte=execution.scheduled_at,
        )
        .order_by("-scheduled_at")[:threshold]
    )


def _alert_already_recorded(execution: ProbeScheduleExecution) -> bool:
    return AuditLog.objects.filter(
        action=ALERT_LOG_ACTION,
        metadata__execution_id=str(execution.id),
    ).exists()


def _resolve_contacts(execution: ProbeScheduleExecution) -> list[str]:
    metadata = execution.schedule.metadata or {}
    contacts = metadata.get("alert_contacts") or []
    if isinstance(contacts, str):
        contacts = [contacts]
    cleaned = [str(contact).strip() for contact in contacts if str(contact).strip()]
    if cleaned:
        return cleaned
    system_settings = get_system_settings()
    defaults = system_settings.notification_channels or {}
    default_email = defaults.get("email")
    if default_email:
        return [str(default_email)]
    return []


def _build_context(execution: ProbeScheduleExecution, contacts: Sequence[str], threshold: int) -> dict[str, str]:
    schedule = execution.schedule
    probe = execution.probe
    metadata = schedule.metadata or {}
    finished_at = execution.finished_at or timezone.now()
    severity = _detect_severity(execution.status)
    system_settings = get_system_settings()
    platform_name = system_settings.platform_name
    title = f"{platform_name} | {schedule.name} 探针告警"
    detail_lines = []
    if execution.message:
        detail_lines.append(execution.message.strip())
    detail_lines.append(f"目标：{schedule.target}")
    if execution.status_code:
        detail_lines.append(f"状态码：{execution.status_code}")
    if execution.response_time_ms:
        detail_lines.append(f"响应耗时：{execution.response_time_ms} ms")
    detail_lines.append(f"连续失败次数：{threshold}")
    detail_lines.append(f"调度时间：{execution.scheduled_at.isoformat()}")
    if contacts:
        detail_lines.append(f"通知联系人：{', '.join(contacts)}")
    message = "\n".join(detail_lines)
    return {
        "title": title,
        "severity": severity,
        "status": execution.status,
        "timestamp": finished_at.isoformat(),
        "task_name": schedule.name,
        "probe_name": probe.name if probe else "",
        "message": message,
        "result_url": _build_result_url(execution),
        "alert_channels": metadata.get("alert_channels") or [],
    }


def _build_result_url(execution: ProbeScheduleExecution) -> str:
    base = getattr(settings, "CONSOLE_BASE_URL", "") or ""
    path = "/#/alerts/checks"
    try:
        from apps.alerts.models import AlertCheck

        check = AlertCheck.objects.filter(
            source_type=AlertCheck.SourceType.PROBE_SCHEDULE,
            source_id=execution.schedule_id,
        ).only("id").first()
        if check:
            path = f"/#/alerts/checks/{check.id}?executionId={execution.id}"
    except Exception:  # pragma: no cover - alert link fallback should not break alert creation
        logger.exception("Failed to resolve alert check result url for probe execution %s", execution.id)
    return f"{base.rstrip('/')}{path}" if base else path


def _detect_severity(status: str) -> str:
    normalized = status.lower()
    if normalized == ProbeScheduleExecution.Status.FAILED:
        return "critical"
    if normalized == ProbeScheduleExecution.Status.MISSED:
        return "warning"
    return "info"


def _record_alert(
    execution: ProbeScheduleExecution,
    failures: Sequence[ProbeScheduleExecution],
    threshold: int,
    contacts: Sequence[str],
    context: dict[str, str],
) -> None:
    # Persist legacy audit log record for backward compatibility / auditing
    AuditLog.objects.create(
        action=ALERT_LOG_ACTION,
        target_type="ProbeSchedule",
        target_id=str(execution.schedule_id),
        result="failed",
        metadata={
            "execution_id": str(execution.id),
            "execution_ids": [str(item.id) for item in failures],
            "schedule_id": str(execution.schedule_id),
            "probe_id": str(execution.probe_id),
            "status": execution.status,
            "threshold": threshold,
            "alert_contacts": list(contacts),
            "message": context.get("message", ""),
        },
    )

    # Also emit a unified AlertEvent into the alerts domain
    schedule = execution.schedule
    probe = execution.probe
    check_context: dict[str, object] = {
        "execution_id": str(execution.id),
        "execution_ids": [str(item.id) for item in failures],
        "schedule_id": str(execution.schedule_id),
        "schedule_name": schedule.name,
        "probe_id": str(execution.probe_id) if execution.probe_id else None,
        "probe_name": probe.name if probe else "",
        "status": execution.status,
        "threshold": threshold,
        "alert_contacts": list(contacts),
        "message": context.get("message", ""),
        "target": schedule.target,
        "status_code": execution.status_code,
        "response_time_ms": execution.response_time_ms,
        "scheduled_at": execution.scheduled_at.isoformat(),
        "finished_at": (execution.finished_at or timezone.now()).isoformat(),
        "result_url": context.get("result_url"),
        "severity": context.get("severity"),
    }

    result = CheckResult(
        source="probes",
        event_type="probe_schedule_alert",
        severity=context.get("severity") or _detect_severity(execution.status),
        title=context.get("title") or f"{schedule.name} 探针告警",
        message=context.get("message", ""),
        status=execution.status,
        task_id=str(execution.schedule_id),
        probe_id=str(execution.probe_id) if execution.probe_id else None,
        context=check_context,
    )
    event = evaluate_and_raise(result)
    # Fan out to the unified alerts pipeline asynchronously.
    _enqueue_alert_dispatch(str(event.id))


def _enqueue_alert_dispatch(event_id: str) -> None:
    try:
        dispatch_alert_event.delay(event_id)
    except Exception:  # pragma: no cover - broker degradation should not break result ingestion
        logger.exception("Failed to enqueue probe alert event %s", event_id)


def _dispatch_to_channel(*args, **kwargs) -> None:
    """Legacy test shim.

    历史测试会 patch 这个符号，但当前统一告警链路已经不再直接从 probe_alert_service 发送通知。
    保留一个空实现，避免兼容测试在 import 阶段失败。
    """

    return None
