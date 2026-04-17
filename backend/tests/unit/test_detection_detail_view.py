from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.monitoring.models import DetectionTask


@pytest.mark.django_db
def test_detection_detail_marks_overdue_task_timeout():
    user = get_user_model().objects.create_user(username="detection-viewer", password="pass1234")
    task = DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.SCHEDULED,
        published_at=timezone.now() - timedelta(seconds=20),
        metadata={"timeout_seconds": 5},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("detection-detail", kwargs={"detection_id": task.id})
    response = client.get(url)

    assert response.status_code == 200
    assert response.json()["status"] == DetectionTask.Status.TIMEOUT

    task.refresh_from_db()
    assert task.status == DetectionTask.Status.TIMEOUT
    assert task.error_message == "探针未在超时时间内回传结果"


@pytest.mark.django_db
def test_detection_detail_keeps_fresh_task_scheduled():
    user = get_user_model().objects.create_user(username="detection-viewer-fresh", password="pass1234")
    task = DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.SCHEDULED,
        published_at=timezone.now() - timedelta(seconds=2),
        metadata={"timeout_seconds": 10},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("detection-detail", kwargs={"detection_id": task.id})
    response = client.get(url)

    assert response.status_code == 200
    assert response.json()["status"] == DetectionTask.Status.SCHEDULED

    task.refresh_from_db()
    assert task.status == DetectionTask.Status.SCHEDULED


@pytest.mark.django_db
def test_detection_detail_marks_overdue_running_task_timeout_from_claimed_at():
    user = get_user_model().objects.create_user(username="detection-viewer-running", password="pass1234")
    task = DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.RUNNING,
        claimed_at=timezone.now() - timedelta(seconds=20),
        metadata={"timeout_seconds": 5},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("detection-detail", kwargs={"detection_id": task.id})
    response = client.get(url)

    assert response.status_code == 200
    assert response.json()["status"] == DetectionTask.Status.TIMEOUT
