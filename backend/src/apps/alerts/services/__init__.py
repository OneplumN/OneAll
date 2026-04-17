from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.utils import timezone

from apps.alerts.models import AlertEvent

from .check_mapping_service import (
    MappingResult,
    ensure_check_for_monitoring_request,
    ensure_check_for_probe_schedule,
    ensure_schedule_for_monitoring_job,
    ensure_schedule_for_probe_schedule,
    map_status,
)
from .check_target_resolution_service import (
    ResolutionResult,
    apply_resolution_snapshot,
    normalize_target_to_domain,
    resolve_check_target,
)
from .system_overview_service import build_system_overview


@dataclass
class CheckResult:
    """Lightweight representation of a monitoring/probe check outcome."""

    source: str
    event_type: str
    severity: str
    title: str
    message: str | None
    status: str
    task_id: Optional[str] = None
    asset_id: Optional[str] = None
    probe_id: Optional[str] = None
    context: Dict[str, Any] | None = None


def evaluate_and_raise(result: CheckResult) -> AlertEvent:
    """Create a minimal AlertEvent based on a completed check result."""

    return AlertEvent.objects.create(
        source=result.source,
        event_type=result.event_type,
        severity=result.severity,
        title=result.title,
        message=result.message or "",
        status=AlertEvent.Status.PENDING,
        related_task_id=result.task_id,
        related_asset_id=result.asset_id,
        related_probe_id=result.probe_id,
        context=result.context or {},
        channels=[],
    )


def mark_event_sent(event: AlertEvent, *, channels: list[str]) -> AlertEvent:
    """Helper to mark an event as successfully delivered."""

    event.status = AlertEvent.Status.SENT
    event.channels = channels
    event.sent_at = timezone.now()
    event.last_error = ""
    event.save(update_fields=["status", "channels", "sent_at", "last_error", "updated_at"])
    return event


def mark_event_failed(event: AlertEvent, *, error_message: str) -> AlertEvent:
    """Helper to mark an event as failed to deliver."""

    event.status = AlertEvent.Status.FAILED
    event.last_error = error_message
    event.save(update_fields=["status", "last_error", "updated_at"])
    return event


__all__ = [
    "CheckResult",
    "MappingResult",
    "ResolutionResult",
    "apply_resolution_snapshot",
    "build_system_overview",
    "ensure_check_for_monitoring_request",
    "ensure_check_for_probe_schedule",
    "ensure_schedule_for_monitoring_job",
    "ensure_schedule_for_probe_schedule",
    "evaluate_and_raise",
    "map_status",
    "mark_event_failed",
    "mark_event_sent",
    "normalize_target_to_domain",
    "resolve_check_target",
]
