import pytest

from apps.monitoring.integrations import zabbix_adapter


def test_zabbix_adapter_parses_items(monkeypatch):
    mock_client = type('Client', (), {'query': lambda self: [{'host': 'app-1', 'status': '0'}]})()
    monkeypatch.setattr(zabbix_adapter, 'get_client', lambda: mock_client)

    result = zabbix_adapter.fetch_status()
    assert result == [{'host': 'app-1', 'status': '0'}]
