from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.alerts.models import AlertCheck
from apps.core.models.user import Role
from apps.monitoring.models import MonitoringJob, MonitoringRequest
from apps.probes.models import ProbeNode, ProbeSchedule
from apps.probes.services.probe_schedule_service import sync_schedule_from_job
from apps.alerts.services import ensure_schedule_for_monitoring_job


def _make_user_with_perms(username: str, *permissions: str):
    user_model = get_user_model()
    user = user_model.objects.create_user(username=username, password="pass1234")
    role = Role.objects.create(name=f"{username}-role", permissions=list(permissions))
    user.roles.set([role])
    return user


@pytest.mark.django_db
def test_alert_checks_api_can_create_manual_strategy():
    user = _make_user_with_perms("alert_check_creator", "alerts.module.access")
    probe = ProbeNode.objects.create(
        name="node-a",
        location="Shanghai",
        network_type="internal",
        supported_protocols=["HTTP", "HTTPS"],
        status="online",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "name": "Homepage strategy",
        "target": "https://example.com/health",
        "protocol": "HTTPS",
        "frequency_minutes": 5,
        "probe_ids": [str(probe.id)],
        "timeout_seconds": 10,
        "expected_status_codes": [200],
        "alert_threshold": 2,
        "alert_contacts": ["ops@example.com"],
        "alert_channels": ["email"],
    }

    response = client.post(reverse("alerts-checks"), payload, format="json")

    assert response.status_code == 201, response.json()
    data = response.json()
    assert data["name"] == "Homepage strategy"
    assert data["source_type"] == "probe_schedule"
    assert data["metadata"]["alert_channels"] == ["email"]

    schedule = ProbeSchedule.objects.get(name="Homepage strategy")
    assert list(schedule.probes.values_list("id", flat=True)) == [probe.id]
    assert schedule.metadata["alert_contacts"] == ["ops@example.com"]


@pytest.mark.django_db
def test_alert_check_detail_api_can_update_manual_strategy():
    user = _make_user_with_perms("alert_check_editor", "alerts.module.access")
    probe_a = ProbeNode.objects.create(
        name="node-a",
        location="Shanghai",
        network_type="internal",
        supported_protocols=["HTTPS"],
        status="online",
    )
    probe_b = ProbeNode.objects.create(
        name="node-b",
        location="Beijing",
        network_type="internal",
        supported_protocols=["HTTPS"],
        status="online",
    )
    schedule = ProbeSchedule.objects.create(
        name="Editable strategy",
        target="https://example.com/health",
        protocol="HTTPS",
        frequency_minutes=5,
        source_type=ProbeSchedule.Source.MANUAL,
        metadata={"alert_contacts": ["old@example.com"]},
    )
    schedule.probes.add(probe_a)
    check = AlertCheck.objects.create(
        name=schedule.name,
        target=schedule.target,
        protocol=schedule.protocol,
        source_type=AlertCheck.SourceType.PROBE_SCHEDULE,
        source_id=schedule.id,
        executor_type=AlertCheck.ExecutorType.PROBE,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "name": "Editable strategy v2",
        "frequency_minutes": 10,
        "probe_ids": [str(probe_b.id)],
        "alert_contacts": ["new@example.com"],
        "alert_channels": ["email", "http"],
    }
    response = client.patch(
        reverse("alerts-check-detail", kwargs={"check_id": check.id}),
        payload,
        format="json",
    )

    assert response.status_code == 200, response.json()
    schedule.refresh_from_db()
    check.refresh_from_db()

    assert schedule.name == "Editable strategy v2"
    assert schedule.frequency_minutes == 10
    assert list(schedule.probes.values_list("id", flat=True)) == [probe_b.id]
    assert schedule.metadata["alert_contacts"] == ["new@example.com"]
    assert schedule.metadata["alert_channels"] == ["email", "http"]
    assert check.name == "Editable strategy v2"


@pytest.mark.django_db
def test_alert_check_detail_api_delete_removes_manual_strategy():
    user = _make_user_with_perms("alert_check_delete", "alerts.module.access")
    schedule = ProbeSchedule.objects.create(
        name="Delete me",
        target="https://example.com/health",
        protocol="HTTPS",
        frequency_minutes=5,
        source_type=ProbeSchedule.Source.MANUAL,
    )
    check = AlertCheck.objects.create(
        name=schedule.name,
        target=schedule.target,
        protocol=schedule.protocol,
        source_type=AlertCheck.SourceType.PROBE_SCHEDULE,
        source_id=schedule.id,
        executor_type=AlertCheck.ExecutorType.PROBE,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.delete(reverse("alerts-check-detail", kwargs={"check_id": check.id}))

    assert response.status_code == 204
    assert not ProbeSchedule.objects.filter(id=schedule.id).exists()
    assert not AlertCheck.objects.filter(id=check.id).exists()


@pytest.mark.django_db
def test_alert_checks_api_hides_monitoring_derived_probe_schedule_duplicates():
    user = _make_user_with_perms("alert_check_viewer", "alerts.module.access")
    request = MonitoringRequest.objects.create(
        title="Payment homepage",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
        metadata={"alert_contacts": ["ops@example.com"]},
    )
    job = MonitoringJob.objects.create(
        request=request,
        frequency_minutes=5,
        schedule_cron="*/5 * * * *",
        status=MonitoringJob.Status.ACTIVE,
        metadata=dict(request.metadata or {}),
    )
    ensure_schedule_for_monitoring_job(job)
    sync_schedule_from_job(job)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("alerts-checks"))

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source_type"] == "monitoring_request"
    assert data[0]["metadata"]["alert_contacts"] == ["ops@example.com"]
