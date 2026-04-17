from __future__ import annotations

from unittest import mock

import pytest

from apps.alerts.models import AlertEvent
from apps.alerts.tasks import dispatch_alert_event
from apps.settings.models import AlertChannel, AlertTemplate
from apps.tools.models import CodeDirectory, CodeRepository, CodeRepositoryVersion


@pytest.mark.django_db
@mock.patch("apps.alerts.services.delivery_service.requests.request")
def test_dispatch_alert_event_delivers_via_http_channel(mock_request):
    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_request.return_value = mock_response

    AlertChannel.objects.create(
        channel_type="http",
        name="callback",
        enabled=True,
        config={"url": "https://example.com/alerts", "method": "POST"},
    )
    AlertTemplate.objects.create(
        channel_type="http",
        name="默认 HTTP 模板",
        body='{"title": "${title}", "status": "${status}"}',
        is_default=True,
    )
    event = AlertEvent.objects.create(
        source="monitoring",
        event_type="monitoring_check_failed_aggregated",
        severity="critical",
        title="监控任务连续失败告警",
        message="任务失败",
        context={
            "status": "failed",
            "task_name": "example.com",
            "timestamp": "2026-04-09T10:00:00+08:00",
            "alert_channels": ["http"],
        },
    )

    dispatch_alert_event(str(event.id))

    event.refresh_from_db()
    assert event.status == AlertEvent.Status.SENT
    assert event.channels == ["http"]
    mock_request.assert_called_once()


@pytest.mark.django_db
def test_dispatch_alert_event_marks_failed_when_no_enabled_channel():
    event = AlertEvent.objects.create(
        source="monitoring",
        event_type="monitoring_check_failed_aggregated",
        severity="critical",
        title="监控任务连续失败告警",
        message="任务失败",
        context={"status": "failed", "task_name": "example.com"},
    )

    dispatch_alert_event(str(event.id))

    event.refresh_from_db()
    assert event.status == AlertEvent.Status.FAILED
    assert "没有可用的告警通道" in event.last_error


@pytest.mark.django_db
def test_dispatch_alert_event_delivers_via_script_channel():
    directory = CodeDirectory.objects.create(
        key="alert-scripts",
        title="告警脚本",
        keywords=["alerts"],
    )
    repository = CodeRepository.objects.create(
        name="通知脚本",
        language="python",
        tags=["alerts"],
        description="用于告警通知",
        directory=directory,
        content="",
    )
    version = CodeRepositoryVersion.objects.create(
        repository=repository,
        version="v1.0.0",
        summary="init",
        change_log="",
        content=(
            "def main(context):\n"
            "    assert context['subject'] == '监控任务连续失败告警'\n"
            "    assert context['alert']['status'] == 'failed'\n"
            "    assert context['contacts'] == ['ops@example.com']\n"
            "    return {'success': True}\n"
        ),
    )
    repository.latest_version = version
    repository.save(update_fields=["latest_version"])

    AlertChannel.objects.create(
        channel_type="script",
        name="script",
        enabled=True,
        config={"repository_id": str(repository.id), "version_id": str(version.id)},
    )
    event = AlertEvent.objects.create(
        source="monitoring",
        event_type="monitoring_check_failed_aggregated",
        severity="critical",
        title="监控任务连续失败告警",
        message="任务失败",
        context={
            "status": "failed",
            "task_name": "example.com",
            "timestamp": "2026-04-09T10:00:00+08:00",
            "alert_channels": ["script"],
            "alert_contacts": ["ops@example.com"],
        },
    )

    dispatch_alert_event(str(event.id))

    event.refresh_from_db()
    assert event.status == AlertEvent.Status.SENT
    assert event.channels == ["script"]


@pytest.mark.django_db
def test_dispatch_alert_event_marks_failed_when_script_channel_returns_failure():
    directory = CodeDirectory.objects.create(
        key="alert-scripts-failure",
        title="告警脚本失败",
        keywords=["alerts"],
    )
    repository = CodeRepository.objects.create(
        name="失败通知脚本",
        language="python",
        tags=["alerts"],
        description="用于告警通知失败测试",
        directory=directory,
        content="",
    )
    version = CodeRepositoryVersion.objects.create(
        repository=repository,
        version="v1.0.0",
        summary="init",
        change_log="",
        content=(
            "def main(context):\n"
            "    return {'success': False, 'message': 'script failed'}\n"
        ),
    )
    repository.latest_version = version
    repository.save(update_fields=["latest_version"])

    AlertChannel.objects.create(
        channel_type="script",
        name="script",
        enabled=True,
        config={"repository_id": str(repository.id), "version_id": str(version.id)},
    )
    event = AlertEvent.objects.create(
        source="monitoring",
        event_type="monitoring_check_failed_aggregated",
        severity="critical",
        title="监控任务连续失败告警",
        message="任务失败",
        context={
            "status": "failed",
            "task_name": "example.com",
            "timestamp": "2026-04-09T10:00:00+08:00",
            "alert_channels": ["script"],
        },
    )

    dispatch_alert_event(str(event.id))

    event.refresh_from_db()
    assert event.status == AlertEvent.Status.FAILED
    assert "script failed" in event.last_error


@pytest.mark.django_db
def test_dispatch_alert_event_marks_failed_when_script_channel_times_out():
    directory = CodeDirectory.objects.create(
        key="alert-scripts-timeout",
        title="告警脚本超时",
        keywords=["alerts"],
    )
    repository = CodeRepository.objects.create(
        name="超时通知脚本",
        language="python",
        tags=["alerts"],
        description="用于告警通知超时测试",
        directory=directory,
        content="",
    )
    version = CodeRepositoryVersion.objects.create(
        repository=repository,
        version="v1.0.0",
        summary="init",
        change_log="",
        content=(
            "import time\n"
            "def main(context):\n"
            "    time.sleep(2)\n"
            "    return {'success': True}\n"
        ),
    )
    repository.latest_version = version
    repository.save(update_fields=["latest_version"])

    AlertChannel.objects.create(
        channel_type="script",
        name="script",
        enabled=True,
        config={
            "repository_id": str(repository.id),
            "version_id": str(version.id),
            "timeout_seconds": 1,
        },
    )
    event = AlertEvent.objects.create(
        source="monitoring",
        event_type="monitoring_check_failed_aggregated",
        severity="critical",
        title="监控任务连续失败告警",
        message="任务失败",
        context={
            "status": "failed",
            "task_name": "example.com",
            "timestamp": "2026-04-09T10:00:00+08:00",
            "alert_channels": ["script"],
        },
    )

    dispatch_alert_event(str(event.id))

    event.refresh_from_db()
    assert event.status == AlertEvent.Status.FAILED
    assert "脚本执行超时" in event.last_error
