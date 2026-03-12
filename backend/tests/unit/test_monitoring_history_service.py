import pytest
from django.utils import timezone

from apps.monitoring.models import DetectionTask
from apps.monitoring.repositories.monitoring_history_repository import MonitoringHistoryFilters
from apps.monitoring.services import monitoring_history_service
from apps.probes.models import ProbeNode


@pytest.mark.django_db
def test_query_history_returns_items_and_aggregates():
    probe = ProbeNode.objects.create(
        name="probe-a",
        location="Shanghai",
        network_type="external",
        supported_protocols=["HTTP", "HTTPS"],
        status="online",
    )

    DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.SUCCEEDED,
        response_time_ms=120,
        executed_at=timezone.now(),
        probe=probe,
    )
    DetectionTask.objects.create(
        target="https://example.com",
        protocol=DetectionTask.Protocol.HTTPS,
        status=DetectionTask.Status.FAILED,
        response_time_ms=350,
        executed_at=timezone.now(),
    )

    result = monitoring_history_service.query_history(MonitoringHistoryFilters())

    assert result.pagination.total_items == 2
    assert result.pagination.total_pages == 1
    assert len(result.items) == 2
    assert result.aggregates.total_count == 2
    assert result.aggregates.status_counts[DetectionTask.Status.SUCCEEDED] == 1
    assert result.aggregates.status_counts[DetectionTask.Status.FAILED] == 1
    assert result.aggregates.success_rate == pytest.approx(50.0)
    assert result.aggregates.average_response_time_ms == pytest.approx(235.0)


@pytest.mark.django_db
def test_query_history_filters_by_status():
    DetectionTask.objects.create(
        target="https://filter.example",
        protocol=DetectionTask.Protocol.HTTP,
        status=DetectionTask.Status.SUCCEEDED,
        executed_at=timezone.now(),
    )
    DetectionTask.objects.create(
        target="https://filter.example",
        protocol=DetectionTask.Protocol.HTTP,
        status=DetectionTask.Status.FAILED,
        executed_at=timezone.now(),
    )

    result = monitoring_history_service.query_history(
        MonitoringHistoryFilters(status=DetectionTask.Status.SUCCEEDED)
    )

    assert len(result.items) == 1
    assert result.items[0].status == DetectionTask.Status.SUCCEEDED
    assert result.aggregates.total_count == 1
    assert result.aggregates.status_counts[DetectionTask.Status.SUCCEEDED] == 1
    assert result.aggregates.status_counts[DetectionTask.Status.FAILED] == 0
    assert result.aggregates.success_rate == pytest.approx(100.0)
