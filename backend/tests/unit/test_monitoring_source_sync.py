from __future__ import annotations

import pytest

from apps.monitoring.tasks.monitoring_source_sync import sync_monitoring_sources


@pytest.mark.django_db
def test_sync_monitoring_sources_success(mocker):
    mock_prometheus = mocker.patch(
        "apps.monitoring.tasks.monitoring_source_sync.prometheus_adapter.fetch_metrics",
        return_value={"data": {"result": []}},
    )
    record_mock = mocker.patch("apps.monitoring.tasks.monitoring_source_sync.record_monitoring_source_snapshot")

    processed = sync_monitoring_sources()

    assert processed == 1
    mock_prometheus.assert_called_once_with("up")
    record_mock.assert_called_once()
    assert record_mock.call_args.kwargs["source_type"] == "prometheus"


@pytest.mark.django_db
def test_sync_monitoring_sources_handles_errors(mocker):
    mocker.patch(
        "apps.monitoring.tasks.monitoring_source_sync.prometheus_adapter.fetch_metrics",
        return_value={"data": {"result": []}},
    )
    record_mock = mocker.patch("apps.monitoring.tasks.monitoring_source_sync.record_monitoring_source_snapshot")

    processed = sync_monitoring_sources()

    assert processed == 1
    record_mock.assert_called_once()
