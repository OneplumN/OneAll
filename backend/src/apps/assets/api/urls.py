from django.urls import path

from .asset_view import AssetRecordDetailView, AssetRecordListView, AssetRecordImportView, AssetRecordQueryView
from .asset_sync_view import AssetSyncTriggerView
from .asset_sync_run_view import AssetSyncRunDetailView, AssetSyncRunListView
from .proxy_mapping_view import ProxyMappingView

urlpatterns = [
    path('assets/records', AssetRecordListView.as_view(), name='assets-records'),
    path('assets/records/query', AssetRecordQueryView.as_view(), name='assets-records-query'),
    path('assets/records/<uuid:record_id>', AssetRecordDetailView.as_view(), name='assets-record-detail'),
    path('assets/import', AssetRecordImportView.as_view(), name='assets-import'),
    path('assets/sync', AssetSyncTriggerView.as_view(), name='assets-sync'),
    path('assets/sync/runs', AssetSyncRunListView.as_view(), name='assets-sync-runs'),
    path('assets/sync/runs/<uuid:run_id>', AssetSyncRunDetailView.as_view(), name='assets-sync-run-detail'),
    path('assets/proxy-mappings', ProxyMappingView.as_view(), name='assets-proxy-mappings'),
]
