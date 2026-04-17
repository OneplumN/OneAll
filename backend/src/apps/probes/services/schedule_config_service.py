from __future__ import annotations

from datetime import datetime, timedelta

from django.utils import timezone
from google.protobuf import struct_pb2, timestamp_pb2

from apps.probes.models import ProbeNode, ProbeSchedule, ProbeConfigRefreshRequest
from probes.v1 import gateway_pb2


def build_config_update_for_probe(probe: ProbeNode) -> gateway_pb2.ConfigUpdate:
    """Build a ConfigUpdate message for all schedules assigned to a probe."""

    schedules = (
        ProbeSchedule.objects.filter(probes=probe)
        .exclude(status=ProbeSchedule.Status.ARCHIVED)
        .select_related("monitoring_job", "monitoring_request")
    )

    schedule_msgs: list[gateway_pb2.ScheduleConfig] = []
    schedule_ids: list[str] = []

    for schedule in schedules:
        _ensure_future_next_run(schedule)
        schedule_ids.append(str(schedule.id))
        cfg = gateway_pb2.ScheduleConfig(
            schedule_id=str(schedule.id),
            target=schedule.target,
            protocol=schedule.protocol,
            interval_seconds=_interval_seconds(schedule),
            timeout_seconds=_timeout_seconds(schedule),
            version=int(schedule.updated_at.timestamp() if schedule.updated_at else timezone.now().timestamp()),
            paused=schedule.status != ProbeSchedule.Status.ACTIVE,
        )
        if schedule.start_at:
            cfg.start_at.CopyFrom(_to_timestamp(schedule.start_at))
        if schedule.end_at:
            cfg.end_at.CopyFrom(_to_timestamp(schedule.end_at))

        metadata_struct = struct_pb2.Struct()
        metadata = schedule.metadata or {}
        metadata_struct.update(metadata)
        cfg.metadata.CopyFrom(metadata_struct)
        schedule_msgs.append(cfg)

    update = gateway_pb2.ConfigUpdate(
        version=int(timezone.now().timestamp()),
        schedules=schedule_msgs,
        removed_schedule_ids=[],
        full_resync=True,
    )
    return update


def request_probe_refresh(probe_ids: list[str] | set[str]) -> None:
    if not probe_ids:
        return
    existing = set(
        ProbeConfigRefreshRequest.objects.filter(
            probe_id__in=probe_ids,
            processed_at__isnull=True,
        ).values_list("probe_id", flat=True)
    )
    pending = [
        ProbeConfigRefreshRequest(probe_id=probe_id)
        for probe_id in probe_ids
        if probe_id not in existing
    ]
    if pending:
        ProbeConfigRefreshRequest.objects.bulk_create(pending, ignore_conflicts=True)


def pop_pending_refresh_requests(probe: ProbeNode) -> bool:
    pending = list(
        ProbeConfigRefreshRequest.objects.filter(
            probe=probe,
            processed_at__isnull=True,
        )
    )
    if not pending:
        return False
    ProbeConfigRefreshRequest.objects.filter(
        id__in=[entry.id for entry in pending]
    ).update(processed_at=timezone.now(), updated_at=timezone.now())
    return True


def _interval_seconds(schedule: ProbeSchedule) -> int:
    minutes = schedule.frequency_minutes or 1
    if minutes < 1:
        minutes = 1
    return minutes * 60


def _timeout_seconds(schedule: ProbeSchedule) -> int:
    metadata = schedule.metadata or {}
    timeout = metadata.get("timeout_seconds")
    if isinstance(timeout, (int, float)) and timeout > 0:
        return int(timeout)
    return 30


def _to_timestamp(value: datetime) -> timestamp_pb2.Timestamp:
    ts = timestamp_pb2.Timestamp()
    ts.FromDatetime(value)
    return ts


def _ensure_future_next_run(schedule: ProbeSchedule) -> None:
    """Ensure next_run_at is rolled forward even if probe停机导致长期未执行."""

    interval_minutes = max(schedule.frequency_minutes or 1, 1)
    interval = timedelta(minutes=interval_minutes)
    now = timezone.now()
    next_run = schedule.next_run_at

    if next_run is None:
        next_run = schedule.start_at or now

    if next_run < now:
        delta = now - next_run
        steps = int(delta / interval) + 1
        next_run = next_run + steps * interval

    if schedule.next_run_at != next_run:
        schedule.next_run_at = next_run
        schedule.save(update_fields=["next_run_at", "updated_at"])
        if schedule.source_type == ProbeSchedule.Source.MANUAL:
            from apps.alerts.services import ensure_schedule_for_probe_schedule

            ensure_schedule_for_probe_schedule(schedule)
