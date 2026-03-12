import pytest

from apps.monitoring.services import detection_service
from apps.monitoring.models import DetectionTask


@pytest.mark.django_db
def test_schedule_detection_success(mocker):
    request = detection_service.DetectionRequest(
        target="https://example.com",
        protocol="HTTPS",
        probe_id=None,
        timeout_seconds=10,
        metadata={"initiated_by": "d2f6bb5a-5f91-4e3f-8e2d-6c7b9fcbe2c4"},
    )

    celery_delay = mocker.patch("apps.monitoring.services.detection_service.execute_detection_task.delay")

    detection = detection_service.schedule_one_off_detection(request)

    assert detection.target == "https://example.com"
    assert detection.protocol == "HTTPS"
    assert detection.status == detection_service.DetectionStatus.SCHEDULED
    celery_delay.assert_called_once_with(str(detection.id))


@pytest.mark.django_db
def test_schedule_detection_with_invalid_protocol():
    request = detection_service.DetectionRequest(
        target="https://example.com",
        protocol="FTP",
        probe_id=None,
        timeout_seconds=10,
        metadata={},
    )

    with pytest.raises(ValueError):
        detection_service.schedule_one_off_detection(request)


@pytest.mark.django_db
def test_mark_detection_timeout():
    task = DetectionTask.objects.create(
        target="https://slow.example",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.RUNNING,
    )

    detection_service.mark_detection_timeout(task.id)

    task.refresh_from_db()
    assert task.status == detection_service.DetectionStatus.TIMEOUT

