import pytest

from apps.monitoring.integrations import prometheus_adapter


def test_prometheus_adapter_fetches_metrics(monkeypatch):
    monkeypatch.setattr(prometheus_adapter, 'query_prometheus', lambda query: {'data': {'result': []}})

    response = prometheus_adapter.fetch_metrics('up')
    assert response == {'data': {'result': []}}
