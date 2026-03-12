import uuid

import pytest

from apps.monitoring.models import MonitoringRequest
from apps.monitoring.serializers.monitoring_request_serializer import (
    MonitoringRequestCreateSerializer,
)


@pytest.mark.django_db
def test_create_serializer_persists_expected_status_codes():
    payload = {
        "title": "证书拨测",
        "target": "https://example.com",
        "protocol": "HTTPS",
        "frequency_minutes": 5,
        "system_name": "OneAll",
        "network_type": "internet",
        "owner_name": "张三",
        "alert_contacts": ["000123"],
        "probe_ids": [uuid.uuid4()],
        "alert_threshold": 3,
        "expected_status_codes": [202, 200, 202],
    }

    serializer = MonitoringRequestCreateSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert isinstance(instance, MonitoringRequest)
    assert instance.metadata["system_name"] == "OneAll"
    assert instance.metadata["expected_status_codes"] == [200, 202]
    assert instance.metadata["probe_ids"]
    assert isinstance(instance.metadata["probe_ids"][0], str)


@pytest.mark.django_db
def test_create_serializer_defaults_expected_status_codes():
    payload = {
        "title": "HTTP 拨测",
        "target": "https://status.example.com",
        "protocol": "HTTPS",
        "frequency_minutes": 1,
    }

    serializer = MonitoringRequestCreateSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.metadata["expected_status_codes"] == [200]
