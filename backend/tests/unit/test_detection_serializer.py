from __future__ import annotations

import uuid

from apps.monitoring.serializers.detection_serializer import DetectionRequestSerializer


def test_detection_request_serializer_accepts_wss_target():
    serializer = DetectionRequestSerializer(
        data={
            "target": "wss://example.com/socket",
            "protocol": "WSS",
            "probe_id": str(uuid.uuid4()),
            "timeout_seconds": 10,
        }
    )

    assert serializer.is_valid(), serializer.errors


def test_detection_request_serializer_accepts_telnet_host_target():
    serializer = DetectionRequestSerializer(
        data={
            "target": "app.internal.example.com",
            "protocol": "Telnet",
            "probe_id": str(uuid.uuid4()),
            "timeout_seconds": 10,
        }
    )

    assert serializer.is_valid(), serializer.errors


def test_detection_request_serializer_rejects_missing_probe():
    serializer = DetectionRequestSerializer(
        data={
            "target": "https://example.com",
            "protocol": "HTTPS",
            "timeout_seconds": 10,
        }
    )

    assert not serializer.is_valid()
    assert "probe_id" in serializer.errors
