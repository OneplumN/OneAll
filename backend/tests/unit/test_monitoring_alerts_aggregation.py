import uuid

import pytest

from django.utils import timezone

from apps.alerts.models import AlertEvent
from apps.monitoring.models import DetectionTask, MonitoringJob, MonitoringRequest
from apps.monitoring.services import detection_service


@pytest.mark.django_db
def test_aggregated_alert_created_after_two_failures_for_same_job(mocker):
    request = MonitoringRequest.objects.create(
        title="Test job",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=1,
    )
    job = MonitoringJob.objects.create(request=request, frequency_minutes=1)

    # Avoid actually dispatching Celery task in unit test
    mocker.patch("apps.monitoring.services.detection_service.dispatch_alert_event.delay")

    detection1 = DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=DetectionTask.Status.RUNNING,
        metadata={"job_id": str(job.id)},
    )
    detection2 = DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=DetectionTask.Status.RUNNING,
        metadata={"job_id": str(job.id)},
    )

    # First failure should not trigger an aggregated alert yet
    detection_service.mark_detection_failed(detection1.id, "first failure")
    assert AlertEvent.objects.count() == 0

    # Second failure within the window should create one AlertEvent
    detection_service.mark_detection_failed(detection2.id, "second failure")

    assert AlertEvent.objects.count() == 1
    event = AlertEvent.objects.first()
    assert event is not None
    assert event.source == "monitoring"
    assert event.event_type == "monitoring_check_failed_aggregated"
    assert event.related_task_id == job.id
    assert event.context.get("failure_count") == 2
    assert event.context.get("job_id") == str(job.id)


@pytest.mark.django_db
def test_threshold_not_reached_does_not_create_alert(mocker):
    request = MonitoringRequest.objects.create(
        title="Test job",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=1,
    )
    job = MonitoringJob.objects.create(request=request, frequency_minutes=1)

    mocker.patch("apps.monitoring.services.detection_service.dispatch_alert_event.delay")

    detection = DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=DetectionTask.Status.RUNNING,
        metadata={"job_id": str(job.id)},
    )

    detection_service.mark_detection_failed(detection.id, "only failure")

    assert AlertEvent.objects.count() == 0


@pytest.mark.django_db
def test_window_deduplication_prevents_duplicate_alerts(mocker):
    request = MonitoringRequest.objects.create(
        title="Test job",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=1,
    )
    job = MonitoringJob.objects.create(request=request, frequency_minutes=1)

    mocker.patch("apps.monitoring.services.detection_service.dispatch_alert_event.delay")

    detection1 = DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=DetectionTask.Status.RUNNING,
        metadata={"job_id": str(job.id)},
    )
    detection2 = DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=DetectionTask.Status.RUNNING,
        metadata={"job_id": str(job.id)},
    )
    detection3 = DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=DetectionTask.Status.RUNNING,
        metadata={"job_id": str(job.id)},
    )

    detection_service.mark_detection_failed(detection1.id, "first failure")
    detection_service.mark_detection_failed(detection2.id, "second failure")
    assert AlertEvent.objects.count() == 1

    # Third failure within the same window should not create a second alert
    detection_service.mark_detection_failed(detection3.id, "third failure")
    assert AlertEvent.objects.count() == 1


@pytest.mark.django_db
def test_aggregated_alert_dispatch_failure_does_not_break_state_update(mocker):
    request = MonitoringRequest.objects.create(
        title="Test job",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=1,
    )
    job = MonitoringJob.objects.create(request=request, frequency_minutes=1)

    mock_logger = mocker.patch("apps.monitoring.services.detection_service.logger")
    mocker.patch(
        "apps.monitoring.services.detection_service.dispatch_alert_event.delay",
        side_effect=RuntimeError("redis down"),
    )

    detection1 = DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=DetectionTask.Status.RUNNING,
        metadata={"job_id": str(job.id)},
    )
    detection2 = DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=DetectionTask.Status.RUNNING,
        metadata={"job_id": str(job.id)},
    )

    detection_service.mark_detection_failed(detection1.id, "first failure")
    detection_service.mark_detection_failed(detection2.id, "second failure")

    detection2.refresh_from_db()
    assert detection2.status == DetectionTask.Status.FAILED
    assert AlertEvent.objects.count() == 1
    mock_logger.exception.assert_called()
