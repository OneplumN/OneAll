from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.alerts.models import AlertCheck, AlertCheckExecution, AlertEvent, AlertSchedule
from apps.alerts.services import mark_event_failed, mark_event_sent
from apps.alerts.services.delivery_service import deliver_alert_event
from apps.monitoring.models import MonitoringJob
from apps.probes.models import ProbeSchedule


@shared_task(name="apps.alerts.tasks.dispatch_alert_event")
def dispatch_alert_event(event_id: str) -> None:
    try:
        event = AlertEvent.objects.get(id=event_id)
    except AlertEvent.DoesNotExist:
        return

    try:
        channels = deliver_alert_event(event)
        mark_event_sent(event, channels=channels)
    except Exception as exc:  # pragma: no cover - defensive logging
        mark_event_failed(event, error_message=str(exc))


def _central_scheduler_enabled() -> bool:
    return bool(getattr(settings, "ALERTS_CENTRAL_SCHEDULER_ENABLED", False))


@shared_task(name="apps.alerts.tasks.run_due_alert_schedules")
def run_due_alert_schedules() -> None:
    """Central scheduler entrypoint that enqueues executions for due AlertSchedules.

    This is guarded by ALERTS_CENTRAL_SCHEDULER_ENABLED to avoid changing
    behavior until explicitly enabled.
    """

    if not _central_scheduler_enabled():
        return

    now = timezone.now()
    due_schedules = AlertSchedule.objects.filter(
        status=AlertSchedule.Status.ACTIVE,
        next_run_at__lte=now,
    ).select_related("alert_check")

    for schedule in due_schedules:
        run_alert_check.delay(str(schedule.id))


@shared_task(name="apps.alerts.tasks.run_alert_check")
def run_alert_check(schedule_id: str) -> None:
    """执行一个 AlertSchedule，真正创建 DetectionTask / 探针拨测任务。

    在 ALERTS_CENTRAL_SCHEDULER_ENABLED 打开时，这里会：
    - 对 MonitoringRequest 映射的检查：复用原有 MonitoringJob 的 enqueue 逻辑；
    - 对手工 ProbeSchedule 映射的检查：复用原有手工调度 enqueue 逻辑；
    然后通过 check_mapping 服务把 Job / ProbeSchedule 的运行时信息同步回 AlertSchedule。
    """

    if not _central_scheduler_enabled():
        return

    try:
        schedule = AlertSchedule.objects.select_related("alert_check").get(id=schedule_id)
    except AlertSchedule.DoesNotExist:
        return

    check = schedule.alert_check
    # 调度“理论执行时间”优先使用 AlertSchedule.next_run_at，缺失时退回当前时间
    now = schedule.next_run_at or timezone.now()

    if check.source_type == AlertCheck.SourceType.MONITORING_REQUEST:
        # 通过 MonitoringRequest 反查所有关联的 MonitoringJob（通常只有一条）
        jobs = MonitoringJob.objects.filter(request_id=check.source_id, status=MonitoringJob.Status.ACTIVE)
        if not jobs.exists():
            return

        from apps.monitoring.services.job_runner_service import _enqueue_single_job  # lazy import 避免循环依赖
        from apps.alerts.services import ensure_schedule_for_monitoring_job  # lazy import 避免循环依赖

        for job in jobs:
            # 复用原有单 Job enqueue 逻辑创建 DetectionTask，并推进 Job.next_run_at
            _enqueue_single_job(job=job, now=now)
            # 将 Job 的 last_run_at / next_run_at 映射回 AlertSchedule，作为下一次调度依据
            ensure_schedule_for_monitoring_job(job)

    elif check.source_type == AlertCheck.SourceType.PROBE_SCHEDULE:
        try:
            probe_schedule = ProbeSchedule.objects.get(id=check.source_id)
        except ProbeSchedule.DoesNotExist:
            return

        # 只接管真正的“手工调度”探针；由 MonitoringRequest 派生的 ProbeSchedule
        # 继续通过 MonitoringJob 分支调度，避免重复创建任务。
        if probe_schedule.source_type != ProbeSchedule.Source.MANUAL:
            return

        from apps.probes.services.manual_schedule_runner import _enqueue_schedule  # lazy import 避免循环依赖
        from apps.alerts.services import ensure_schedule_for_probe_schedule  # lazy import 避免循环依赖

        # 复用原有手工调度 enqueue 逻辑创建 DetectionTask，并推进 ProbeSchedule.next_run_at
        _enqueue_schedule(schedule=probe_schedule, now=now)
        # 将 ProbeSchedule 的 next_run_at 同步回 AlertSchedule
        ensure_schedule_for_probe_schedule(probe_schedule)
