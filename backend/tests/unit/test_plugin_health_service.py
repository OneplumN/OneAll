import pytest

from apps.settings.services import plugin_health_service


@pytest.mark.django_db
def test_health_check_marks_plugin_status(monkeypatch, django_db_reset_sequences):
    plugin = plugin_health_service.PluginConfig.objects.create(
        name='Zabbix',
        type='zabbix',
        config={'url': 'https://zabbix.example.com'},
        status='unknown',
    )

    monkeypatch.setattr(
        plugin_health_service,
        'run_health_check_for_plugin',
        lambda plugin: {'status': 'healthy', 'message': 'ok'},
    )

    plugin_health_service.evaluate_plugin_health()

    plugin.refresh_from_db()
    assert plugin.status == 'healthy'
    assert plugin.last_message == 'ok'
