import pytest

from apps.monitoring.services import detection_service
from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode


@pytest.mark.django_db
def test_schedule_detection_success():
    request = detection_service.DetectionRequest(
        target="https://example.com",
        protocol="HTTPS",
        probe_id=None,
        timeout_seconds=10,
        metadata={"initiated_by": "d2f6bb5a-5f91-4e3f-8e2d-6c7b9fcbe2c4"},
    )

    detection = detection_service.schedule_one_off_detection(request)

    assert detection.target == "https://example.com"
    assert detection.protocol == "HTTPS"
    assert detection.status == detection_service.DetectionStatus.SCHEDULED


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
    assert task.executed_at is not None
    assert task.error_message == "探针未在超时时间内回传结果"


@pytest.mark.django_db
def test_mark_detection_running_sets_claimed_at():
    task = DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.SCHEDULED,
    )

    task.mark_running()

    task.refresh_from_db()
    assert task.status == DetectionTask.Status.RUNNING
    assert task.published_at is not None
    assert task.claimed_at is not None


@pytest.mark.django_db
def test_schedule_detection_with_missing_probe():
    request = detection_service.DetectionRequest(
        target="https://example.com",
        protocol="HTTPS",
        probe_id="d2f6bb5a-5f91-4e3f-8e2d-6c7b9fcbe2c4",
        timeout_seconds=10,
        metadata={},
    )

    with pytest.raises(ValueError, match="指定的探针不存在"):
        detection_service.schedule_one_off_detection(request)


@pytest.mark.django_db
def test_schedule_detection_rejects_unsupported_probe_protocol():
    probe = ProbeNode.objects.create(
        name="probe-a",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    request = detection_service.DetectionRequest(
        target="wss://example.com/socket",
        protocol="WSS",
        probe_id=str(probe.id),
        timeout_seconds=10,
        metadata={},
    )

    with pytest.raises(detection_service.ProbeUnavailableError, match="不支持协议"):
        detection_service.schedule_one_off_detection(request)
