from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models.user import Role
from apps.monitoring.models import DetectionTask, MonitoringJob, MonitoringRequest
from apps.alerts.services import ensure_schedule_for_monitoring_job


def _make_user_with_perms(username: str, *permissions: str):
    user_model = get_user_model()
    user = user_model.objects.create_user(username=username, password="pass1234")
    role = Role.objects.create(name=f"{username}-role", permissions=list(permissions))
    user.roles.set([role])
    return user


def _seed_overview_data():
    request = MonitoringRequest.objects.create(
        title="Payment homepage",
        target="https://pay.demo.oneall.com/health",
        protocol=MonitoringRequest.Protocol.HTTPS,
        frequency_minutes=5,
    )
    job = MonitoringJob.objects.create(
        request=request,
        frequency_minutes=5,
        schedule_cron="*/5 * * * *",
        status=MonitoringJob.Status.ACTIVE,
    )
    check = ensure_schedule_for_monitoring_job(job).check
    check.resolved_domain = "pay.demo.oneall.com"
    check.resolved_system_name = "支付平台"
    check.asset_match_status = "matched"
    check.save(
        update_fields=[
            "resolved_domain",
            "resolved_system_name",
            "asset_match_status",
            "updated_at",
        ]
    )
    DetectionTask.objects.create(
        target=request.target,
        protocol=request.protocol,
        status=DetectionTask.Status.SUCCEEDED,
        response_time_ms=90,
        status_code="200",
        executed_at=request.created_at,
        metadata={"request_id": str(request.id)},
    )


@pytest.mark.django_db
def test_alerts_system_overview_api_returns_systems_and_items():
    user = _make_user_with_perms("alerts_overview_tester", "alerts.module.access")
    _seed_overview_data()

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("alerts-checks-system-overview"))

    assert response.status_code == 200
    data = response.json()
    assert "systems" in data
    assert "items" in data
    assert data["systems"][0]["system_name"] == "支付平台"
    assert data["items"][0]["check_name"] == "Payment homepage"


@pytest.mark.django_db
def test_alerts_system_overview_api_allows_monitoring_overview_permission():
    user = _make_user_with_perms("monitoring_overview_tester", "monitoring.overview.view")
    _seed_overview_data()

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("alerts-checks-system-overview"))

    assert response.status_code == 200
    data = response.json()
    assert data["systems"][0]["system_name"] == "支付平台"
