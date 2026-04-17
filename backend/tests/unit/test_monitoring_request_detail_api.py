from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.alerts.models import AlertSchedule
from apps.core.models.user import Role
from apps.monitoring.models import MonitoringJob, MonitoringRequest
from apps.monitoring.services.monitoring_job_service import create_job_for_request
from apps.probes.models import ProbeNode


@pytest.mark.django_db
def test_monitoring_request_patch_syncs_approved_request_to_job_and_alert_schedule():
    user_model = get_user_model()
    user = user_model.objects.create_user(username="monitor-editor", password="pass1234")
    role = Role.objects.create(name="monitor-editor-role", permissions=["detection.schedules.create", "detection.schedules.view"])
    user.roles.set([role])
    old_probe = ProbeNode.objects.create(
        name="old-probe",
        location="Shanghai",
        network_type="internal",
        supported_protocols=["HTTPS"],
        status="online",
    )
    new_probe = ProbeNode.objects.create(
        name="new-probe",
        location="Beijing",
        network_type="internet",
        supported_protocols=["HTTPS"],
        status="online",
    )
    request = MonitoringRequest.objects.create(
        title="Payment homepage",
        target="https://example.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        description="old",
        status=MonitoringRequest.Status.APPROVED,
        frequency_minutes=5,
        schedule_cron="*/5 * * * *",
        metadata={
            "probe_ids": [str(old_probe.id)],
            "alert_threshold": 2,
            "alert_contacts": ["old@example.com"],
            "expected_status_codes": [200],
        },
        created_by=user,
        updated_by=user,
    )
    job = create_job_for_request(request)

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "frequency_minutes": 10,
        "schedule_cron": "*/10 * * * *",
        "probe_ids": [str(new_probe.id)],
        "alert_threshold": 4,
        "alert_contacts": ["new@example.com"],
        "expected_status_codes": [200, 302],
    }
    response = client.patch(
        reverse("monitoring-request-detail", kwargs={"pk": request.id}),
        payload,
        format="json",
    )

    assert response.status_code == 200, response.json()

    request.refresh_from_db()
    job.refresh_from_db()
    probe_schedule = job.probe_schedule
    monitoring_alert_schedule = AlertSchedule.objects.get(
        alert_check__source_type="monitoring_request",
        alert_check__source_id=request.id,
    )

    assert request.frequency_minutes == 10
    assert request.schedule_cron == "*/10 * * * *"
    assert request.metadata["probe_ids"] == [str(new_probe.id)]
    assert request.metadata["alert_threshold"] == 4
    assert request.metadata["alert_contacts"] == ["new@example.com"]
    assert request.metadata["expected_status_codes"] == [200, 302]

    assert job.frequency_minutes == 10
    assert job.schedule_cron == "*/10 * * * *"
    assert job.metadata["probe_ids"] == [str(new_probe.id)]
    assert job.metadata["alert_threshold"] == 4
    assert job.metadata["alert_contacts"] == ["new@example.com"]
    assert job.metadata["expected_status_codes"] == [200, 302]

    assert probe_schedule.frequency_minutes == 10
    assert list(probe_schedule.probes.values_list("id", flat=True)) == [new_probe.id]
    assert probe_schedule.metadata["probe_ids"] == [str(new_probe.id)]
    assert probe_schedule.metadata["alert_threshold"] == 4
    assert probe_schedule.metadata["alert_contacts"] == ["new@example.com"]

    assert monitoring_alert_schedule.frequency_minutes == 10
    assert monitoring_alert_schedule.cron_expression == "*/10 * * * *"
    assert monitoring_alert_schedule.metadata["probe_ids"] == [str(new_probe.id)]
    assert monitoring_alert_schedule.metadata["alert_threshold"] == 4
    assert monitoring_alert_schedule.metadata["alert_contacts"] == ["new@example.com"]
