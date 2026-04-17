from __future__ import annotations

from datetime import timedelta
from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.alerts.models import AlertSchedule
from apps.alerts.services import (
    ensure_schedule_for_monitoring_job,
    ensure_schedule_for_probe_schedule,
)
from apps.alerts.tasks import run_alert_check, run_due_alert_schedules
from apps.monitoring.models import DetectionTask, MonitoringJob, MonitoringRequest
from apps.probes.models import ProbeNode, ProbeSchedule


@pytest.mark.django_db
@override_settings(ALERTS_CENTRAL_SCHEDULER_ENABLED=False)
@mock.patch("apps.alerts.tasks.run_alert_check.delay")
def test_run_due_alert_schedules_disabled_noop(mock_delay) -> None:
    """在中央调度关闭时，alerts 侧调度不应该下发任何任务。"""

    now = timezone.now()
    # 创建一个简单的监控任务 + 调度，用于验证调度器确实会忽略它
    request = MonitoringRequest.objects.create(
        title="ping-home",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
    )
    job = MonitoringJob.objects.create(
        request=request,
        frequency_minutes=5,
        status=MonitoringJob.Status.ACTIVE,
        next_run_at=now - timedelta(minutes=1),
    )
    mapping = ensure_schedule_for_monitoring_job(job)
    schedule = mapping.schedule
    assert isinstance(schedule, AlertSchedule)

    # 即使有 due 的 AlertSchedule，flag 关闭时也不应该调用 run_alert_check
    run_due_alert_schedules()

    mock_delay.assert_not_called()


@pytest.mark.django_db
@override_settings(ALERTS_CENTRAL_SCHEDULER_ENABLED=True)
@mock.patch("apps.alerts.tasks.run_alert_check.delay")
def test_run_due_alert_schedules_enqueues_due_schedules(mock_delay) -> None:
    """在中央调度开启时，应为 due 的 AlertSchedule 下发执行任务。"""

    now = timezone.now()
    request = MonitoringRequest.objects.create(
        title="ping-home",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
    )
    job = MonitoringJob.objects.create(
        request=request,
        frequency_minutes=5,
        status=MonitoringJob.Status.ACTIVE,
        next_run_at=now - timedelta(minutes=1),
    )
    mapping = ensure_schedule_for_monitoring_job(job)
    schedule = mapping.schedule
    assert isinstance(schedule, AlertSchedule)

    # 标记为 due
    schedule.next_run_at = now - timedelta(minutes=1)
    schedule.status = AlertSchedule.Status.ACTIVE
    schedule.save(update_fields=["next_run_at", "status", "updated_at"])

    run_due_alert_schedules()

    mock_delay.assert_called_once_with(str(schedule.id))


@pytest.mark.django_db
@override_settings(ALERTS_CENTRAL_SCHEDULER_ENABLED=True)
def test_run_alert_check_enqueues_monitoring_detection_tasks() -> None:
    """run_alert_check 对监控任务应复用旧逻辑创建 DetectionTask。"""

    now = timezone.now()
    probe = ProbeNode.objects.create(
        name="probe-auto",
        location="hz-idc",
        network_type="external",
        status="online",
        supported_protocols=["HTTPS"],
    )
    request = MonitoringRequest.objects.create(
        title="API 可用性",
        target="https://status.example.com",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
        metadata={
            "probe_ids": [str(probe.id)],
            "expected_status_codes": [200],
            "timeout_seconds": 20,
        },
    )
    job = MonitoringJob.objects.create(
        request=request,
        frequency_minutes=5,
        status=MonitoringJob.Status.ACTIVE,
        next_run_at=now - timedelta(minutes=1),
    )

    mapping = ensure_schedule_for_monitoring_job(job)
    schedule = mapping.schedule
    assert isinstance(schedule, AlertSchedule)

    # 赋值一个合理的 next_run_at，作为“理论执行时间”
    schedule.next_run_at = now
    schedule.save(update_fields=["next_run_at", "updated_at"])

    assert DetectionTask.objects.count() == 0

    run_alert_check(str(schedule.id))

    # 应创建一条 DetectionTask，并更新 Job 的运行时间
    assert DetectionTask.objects.count() == 1
    detection = DetectionTask.objects.get()
    assert detection.metadata.get("job_id") == str(job.id)
    job.refresh_from_db()
    assert job.last_run_at is not None
    assert job.next_run_at is not None
    assert job.next_run_at > now


@pytest.mark.django_db
@override_settings(ALERTS_CENTRAL_SCHEDULER_ENABLED=True)
def test_run_alert_check_enqueues_manual_probe_schedule() -> None:
    """run_alert_check 对手工 ProbeSchedule 应复用旧逻辑创建 DetectionTask。"""

    now = timezone.now()
    probe = ProbeNode.objects.create(
        name="manual-probe",
        location="gz-idc",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    schedule = ProbeSchedule.objects.create(
        name="站点拨测",
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        frequency_minutes=5,
        status=ProbeSchedule.Status.ACTIVE,
        source_type=ProbeSchedule.Source.MANUAL,
        next_run_at=now - timedelta(minutes=1),
        metadata={
            "expected_status_codes": [200],
            "timeout_seconds": 20,
        },
    )
    schedule.probes.add(probe)

    mapping = ensure_schedule_for_probe_schedule(schedule)
    alert_schedule = mapping.schedule
    assert isinstance(alert_schedule, AlertSchedule)

    alert_schedule.next_run_at = now
    alert_schedule.save(update_fields=["next_run_at", "updated_at"])

    assert DetectionTask.objects.count() == 0

    run_alert_check(str(alert_schedule.id))

    # 应创建一条 DetectionTask，并推进 ProbeSchedule.next_run_at
    assert DetectionTask.objects.count() == 1
    detection = DetectionTask.objects.get()
    assert detection.metadata.get("schedule_id") == str(schedule.id)

    schedule.refresh_from_db()
    assert schedule.next_run_at is not None
    assert schedule.next_run_at > now

