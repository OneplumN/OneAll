from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils import timezone

from apps.alerts.models import AlertCheck
from apps.alerts.services.check_target_resolution_service import (
    INVALID_TARGET,
    MATCHED,
    MISSING_SYSTEM,
    UNMANAGED,
)
from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeSchedule, ProbeScheduleExecution

MISSING_SYSTEM_BUCKET = "未配置系统"
UNMANAGED_BUCKET = "未纳管域名"


def build_system_overview() -> dict[str, Any]:
    checks = _listable_checks(
        AlertCheck.objects.filter(
        source_type__in=[
            AlertCheck.SourceType.MONITORING_REQUEST,
            AlertCheck.SourceType.PROBE_SCHEDULE,
        ]
        ).order_by("created_at", "id")
    )
    latest_detections = _latest_detection_by_request_id(checks)
    latest_probe_executions = _latest_probe_execution_by_schedule_id(checks)
    systems: dict[str, dict[str, Any]] = {}
    items: list[dict[str, Any]] = []
    latest_data_at: datetime | None = None

    for check in checks:
        system_name = _resolve_system_bucket(check)
        latest_record = _latest_record_for_check(
            check,
            latest_detections=latest_detections,
            latest_probe_executions=latest_probe_executions,
        )
        latest_status = _normalize_execution_status(latest_record)
        last_checked_at = _execution_timestamp(latest_record)

        if last_checked_at and (latest_data_at is None or last_checked_at > latest_data_at):
            latest_data_at = last_checked_at

        items.append(
            {
                "system_name": system_name,
                "resolved_domain": check.resolved_domain or check.target,
                "target": check.target,
                "check_id": str(check.id),
                "check_name": check.name,
                "protocol": check.protocol,
                "latest_status": latest_status,
                "status_code": _execution_status_code(latest_record),
                "response_time_ms": _execution_response_time(latest_record),
                "last_checked_at": _format_datetime(last_checked_at),
                "latest_error": _execution_error(latest_record),
                "asset_match_status": check.asset_match_status,
            }
        )

        system = systems.setdefault(
            system_name,
            {
                "system_name": system_name,
                "status": "idle",
                "domain_count": 0,
                "abnormal_count": 0,
                "last_checked_at": None,
                "matched_strategy_count": 0,
                "_domains": set(),
                "_valid_result_count": 0,
            },
        )
        system["matched_strategy_count"] += 1
        system["_domains"].add(check.resolved_domain or check.target)

        if latest_status == "danger":
            system["abnormal_count"] += 1
            system["_valid_result_count"] += 1
            system["status"] = "danger"
        elif latest_status == "success":
            system["_valid_result_count"] += 1
            if system["status"] != "danger":
                system["status"] = "success"

        if last_checked_at and (
            system["last_checked_at"] is None or last_checked_at > system["last_checked_at"]
        ):
            system["last_checked_at"] = last_checked_at

    summaries = []
    for system_name in sorted(systems):
        system = systems[system_name]
        if system["status"] != "danger" and system["_valid_result_count"] == 0:
            system["status"] = "idle"
        system["domain_count"] = len(system["_domains"])
        system["last_checked_at"] = _format_datetime(system["last_checked_at"])
        del system["_domains"]
        del system["_valid_result_count"]
        summaries.append(system)

    items.sort(key=lambda item: (item["system_name"], item["resolved_domain"], item["check_name"]))

    return {
        "generated_at": timezone.now().isoformat(),
        "data_updated_at": _format_datetime(latest_data_at),
        "systems": summaries,
        "items": items,
    }


def _resolve_system_bucket(check: AlertCheck) -> str:
    if check.asset_match_status == MATCHED and check.resolved_system_name:
        return check.resolved_system_name
    if check.asset_match_status == MISSING_SYSTEM:
        return MISSING_SYSTEM_BUCKET
    if check.asset_match_status in {UNMANAGED, INVALID_TARGET}:
        return UNMANAGED_BUCKET
    if check.resolved_system_name:
        return check.resolved_system_name
    return UNMANAGED_BUCKET


def _latest_detection_by_request_id(checks) -> dict[str, DetectionTask]:
    request_ids = {
        str(check.source_id)
        for check in checks
        if check.source_type == AlertCheck.SourceType.MONITORING_REQUEST and check.source_id
    }
    if not request_ids:
        return {}

    latest: dict[str, DetectionTask] = {}
    queryset = DetectionTask.objects.filter(
        metadata__request_id__in=list(request_ids)
    ).order_by("-executed_at", "-created_at", "-id")
    for detection in queryset:
        request_id = str((detection.metadata or {}).get("request_id") or "")
        if request_id and request_id not in latest:
            latest[request_id] = detection
    return latest


def _latest_probe_execution_by_schedule_id(checks) -> dict[str, ProbeScheduleExecution]:
    schedule_ids = {
        str(check.source_id)
        for check in checks
        if check.source_type == AlertCheck.SourceType.PROBE_SCHEDULE and check.source_id
    }
    if not schedule_ids:
        return {}

    latest: dict[str, ProbeScheduleExecution] = {}
    queryset = ProbeScheduleExecution.objects.filter(
        schedule_id__in=list(schedule_ids)
    ).order_by("-scheduled_at", "-id")
    for execution in queryset:
        schedule_id = str(execution.schedule_id)
        if schedule_id not in latest:
            latest[schedule_id] = execution
    return latest


def _latest_record_for_check(
    check: AlertCheck,
    *,
    latest_detections: dict[str, DetectionTask],
    latest_probe_executions: dict[str, ProbeScheduleExecution],
) -> DetectionTask | ProbeScheduleExecution | None:
    if not check.source_id:
        return None
    source_id = str(check.source_id)
    if check.source_type == AlertCheck.SourceType.MONITORING_REQUEST:
        return latest_detections.get(source_id)
    if check.source_type == AlertCheck.SourceType.PROBE_SCHEDULE:
        return latest_probe_executions.get(source_id)
    return None


def _normalize_execution_status(execution: DetectionTask | ProbeScheduleExecution | None) -> str:
    if execution is None:
        return "idle"

    if isinstance(execution, DetectionTask):
        if execution.status == DetectionTask.Status.SUCCEEDED:
            return "success"
        if execution.status in {
            DetectionTask.Status.FAILED,
            DetectionTask.Status.TIMEOUT,
        }:
            return "danger"
        return "idle"

    if execution.status == ProbeScheduleExecution.Status.SUCCEEDED:
        return "success"
    if execution.status in {
        ProbeScheduleExecution.Status.FAILED,
        ProbeScheduleExecution.Status.MISSED,
    }:
        return "danger"
    return "idle"


def _execution_timestamp(execution: DetectionTask | ProbeScheduleExecution | None):
    if execution is None:
        return None
    if isinstance(execution, DetectionTask):
        return execution.executed_at or execution.created_at or execution.updated_at
    return execution.finished_at or execution.scheduled_at


def _execution_status_code(execution: DetectionTask | ProbeScheduleExecution | None) -> str:
    if execution is None:
        return ""
    status_code = execution.status_code
    return str(status_code) if status_code is not None else ""


def _execution_response_time(execution: DetectionTask | ProbeScheduleExecution | None) -> int | None:
    if execution is None:
        return None
    return execution.response_time_ms


def _execution_error(execution: DetectionTask | ProbeScheduleExecution | None) -> str:
    if execution is None:
        return ""
    if isinstance(execution, DetectionTask):
        return execution.error_message or ""
    return execution.message or ""


def _format_datetime(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _listable_checks(checks):
    items = list(checks)
    probe_schedule_ids = [
        check.source_id
        for check in items
        if check.source_type == AlertCheck.SourceType.PROBE_SCHEDULE and check.source_id
    ]
    if not probe_schedule_ids:
        return items

    manual_schedule_ids = set(
        ProbeSchedule.objects.filter(
            id__in=probe_schedule_ids,
            source_type=ProbeSchedule.Source.MANUAL,
        ).values_list("id", flat=True)
    )
    return [
        check
        for check in items
        if check.source_type != AlertCheck.SourceType.PROBE_SCHEDULE or check.source_id in manual_schedule_ids
    ]
