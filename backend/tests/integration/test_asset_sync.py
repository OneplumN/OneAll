import pytest

from apps.assets.services.sync_service import sync_assets


@pytest.mark.django_db
def test_asset_sync_runs_collectors(mocker):
    mocked_collector = mocker.patch('apps.assets.services.sync_service.collect_sources', return_value=[{'name': 'app-1'}])
    mocked_store = mocker.patch('apps.assets.services.sync_service.store_assets')

    result = sync_assets()

    mocked_collector.assert_called_once()
    mocked_store.assert_called_once_with([{'name': 'app-1'}])
    assert result == {'synced': 1}
