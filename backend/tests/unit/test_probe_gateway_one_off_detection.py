from __future__ import annotations

from google.protobuf import json_format, struct_pb2

import pytest
from django.utils import timezone

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode
from apps.probes.streaming.service import ProbeGatewayService
from probes.v1 import gateway_pb2


@pytest.mark.django_db
def test_claim_pending_detection_tasks_defers_running_until_message_is_sent(mocker):
    probe = ProbeNode.objects.create(
        name="probe-a",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS", "Telnet", "WSS", "CERTIFICATE"],
    )
    detection = DetectionTask.objects.create(
        target="service.internal",
        protocol=DetectionTask.Protocol.TELNET,
        probe=probe,
        status=DetectionTask.Status.SCHEDULED,
        metadata={
            "execution_source": "one_off",
            "selected_node": str(probe.id),
            "config": {
                "timeout_seconds": 12,
                "port": 2323,
            },
        },
    )
    apply_async = mocker.patch(
        "apps.probes.streaming.service.expire_detection_task.apply_async"
    )

    service = ProbeGatewayService()

    messages = service._claim_pending_detection_tasks(probe)

    detection.refresh_from_db()
    assert len(messages) == 1
    assert detection.status == DetectionTask.Status.SCHEDULED
    assert detection.published_at is None
    apply_async.assert_not_called()

    outbound = messages[0]
    dispatch = outbound.payload.task
    payload = json_format.MessageToDict(dispatch.metadata, preserving_proto_field_name=True)
    assert dispatch.task_id == str(detection.id)
    assert dispatch.protocol == DetectionTask.Protocol.TELNET
    assert dispatch.timeout_seconds == 12
    assert payload["port"] == 2323
    assert payload["config"]["port"] == 2323

    outbound.on_sent()
    detection.refresh_from_db()
    assert detection.status == DetectionTask.Status.SCHEDULED
    assert detection.published_at is not None
    apply_async.assert_called_once_with(args=[str(detection.id)], countdown=12)


@pytest.mark.django_db
def test_claim_pending_detection_tasks_continues_when_timeout_enqueue_fails(mocker):
    probe = ProbeNode.objects.create(
        name="probe-a",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    detection = DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        probe=probe,
        status=DetectionTask.Status.SCHEDULED,
        metadata={
            "execution_source": "one_off",
            "config": {
                "timeout_seconds": 10,
                "follow_redirects": True,
            },
        },
    )
    mocker.patch(
        "apps.probes.streaming.service.expire_detection_task.apply_async",
        side_effect=RuntimeError("redis down"),
    )
    mock_logger = mocker.patch("apps.probes.streaming.service.logger")

    service = ProbeGatewayService()

    messages = service._claim_pending_detection_tasks(probe)

    detection.refresh_from_db()
    assert len(messages) == 1
    assert detection.status == DetectionTask.Status.SCHEDULED
    assert detection.published_at is None

    messages[0].on_sent()
    detection.refresh_from_db()
    assert detection.status == DetectionTask.Status.SCHEDULED
    assert detection.published_at is not None
    mock_logger.exception.assert_called()


@pytest.mark.django_db
def test_handle_task_ack_marks_published_detection_running():
    probe = ProbeNode.objects.create(
        name="probe-a",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["HTTPS"],
    )
    detection = DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        probe=probe,
        status=DetectionTask.Status.SCHEDULED,
        published_at=timezone.now(),
        metadata={"execution_source": "one_off"},
    )
    ack = gateway_pb2.TaskAck(task_id=str(detection.id))

    service = ProbeGatewayService()
    service._handle_task_ack(probe, ack)

    detection.refresh_from_db()
    assert detection.status == DetectionTask.Status.RUNNING


@pytest.mark.django_db
def test_handle_schedule_result_updates_detection_task_for_direct_one_off_result():
    probe = ProbeNode.objects.create(
        name="probe-a",
        location="cn",
        network_type="internal",
        status="online",
        supported_protocols=["CERTIFICATE"],
    )
    detection = DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.CERTIFICATE,
        probe=probe,
        status=DetectionTask.Status.RUNNING,
        metadata={"execution_source": "one_off"},
    )
    metadata = struct_pb2.Struct()
    metadata.update(
        {
            "certificate": {
                "status": "valid",
                "days_until_expiry": 30,
            }
        }
    )
    result = gateway_pb2.TaskResult(
        task_id=str(detection.id),
        protocol="CERTIFICATE",
        status="success",
        response_time_ms=123,
        metadata=metadata,
    )

    service = ProbeGatewayService()
    service._handle_schedule_result(probe, result)

    detection.refresh_from_db()
    assert detection.status == DetectionTask.Status.SUCCEEDED
    assert detection.response_time_ms == 123
    assert detection.executed_at is not None
    assert detection.result_payload["certificate"]["status"] == "valid"
