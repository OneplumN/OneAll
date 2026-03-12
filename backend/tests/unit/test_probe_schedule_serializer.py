from __future__ import annotations

import pytest

from apps.probes.api.serializers import ProbeScheduleSerializer
from apps.probes.models import ProbeNode, ProbeSchedule


@pytest.mark.django_db
def test_serializer_exposes_metadata_fields_for_read():
    probe = ProbeNode.objects.create(
        name="node-a",
        location="Shanghai",
        network_type="external",
        supported_protocols=["HTTPS"],
    )
    schedule = ProbeSchedule.objects.create(
        name="meta-schedule",
        target="https://example.com",
        protocol="HTTPS",
        frequency_minutes=5,
        source_type=ProbeSchedule.Source.MANUAL,
        status=ProbeSchedule.Status.ACTIVE,
        metadata={
            "timeout_seconds": 45,
            "expected_status_codes": [200, 204],
            "alert_threshold": 3,
            "alert_contacts": ["oncall@example.com", "sre@example.com"],
        },
    )
    schedule.probes.add(probe)

    serializer = ProbeScheduleSerializer(instance=schedule)
    data = serializer.data

    assert data["timeout_seconds"] == 45
    assert data["expected_status_codes"] == [200, 204]
    assert data["alert_threshold"] == 3
    assert data["alert_contacts"] == ["oncall@example.com", "sre@example.com"]


@pytest.mark.django_db
def test_update_schedule_persists_metadata_fields():
    probe = ProbeNode.objects.create(
        name="node-b",
        location="Beijing",
        network_type="external",
        supported_protocols=["HTTPS"],
    )
    schedule = ProbeSchedule.objects.create(
        name="editable",
        target="https://example.com",
        protocol="HTTPS",
        frequency_minutes=5,
        source_type=ProbeSchedule.Source.MANUAL,
        status=ProbeSchedule.Status.ACTIVE,
        metadata={
            "timeout_seconds": 30,
            "expected_status_codes": [200],
            "alert_threshold": 1,
            "alert_contacts": [],
        },
    )
    schedule.probes.add(probe)

    payload = {
        "name": "editable",
        "target": "https://example.com",
        "protocol": "HTTPS",
        "frequency_minutes": 5,
        "probe_ids": [str(probe.id)],
        "timeout_seconds": 60,
        "expected_status_codes": [300],
        "alert_threshold": 2,
        "alert_contacts": ["foo@example.com"],
    }
    serializer = ProbeScheduleSerializer(instance=schedule, data=payload, partial=True)
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    schedule.refresh_from_db()

    assert schedule.metadata["timeout_seconds"] == 60
    assert schedule.metadata["expected_status_codes"] == [300]
    assert schedule.metadata["alert_threshold"] == 2
    assert schedule.metadata["alert_contacts"] == ["foo@example.com"]
