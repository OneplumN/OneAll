from django.urls import path

from .asset_model_view import (
    AssetModelDetailView,
    AssetModelListCreateView,
    AssetModelScriptUploadView,
    AssetModelScriptDownloadView,
    AssetModelScriptTemplateView,
)
from .asset_model_sync_view import AssetModelSyncView
from .asset_view import AssetRecordDetailView, AssetRecordListView, AssetRecordImportView, AssetRecordQueryView
from .asset_sync_view import AssetSyncTriggerView
from .asset_sync_run_view import AssetSyncRunDetailView, AssetSyncRunListView
from .asset_type_view import AssetTypeDetailView, AssetTypeListView
from .proxy_mapping_view import ProxyMappingView

urlpatterns = [
    path("assets/records", AssetRecordListView.as_view(), name="assets-records"),
    path("assets/records/query", AssetRecordQueryView.as_view(), name="assets-records-query"),
    path("assets/records/<uuid:record_id>", AssetRecordDetailView.as_view(), name="assets-record-detail"),
    path("assets/import", AssetRecordImportView.as_view(), name="assets-import"),
    path("assets/sync", AssetSyncTriggerView.as_view(), name="assets-sync"),
    path("assets/sync/runs", AssetSyncRunListView.as_view(), name="assets-sync-runs"),
    path("assets/sync/runs/<uuid:run_id>", AssetSyncRunDetailView.as_view(), name="assets-sync-run-detail"),
    path("assets/proxy-mappings", ProxyMappingView.as_view(), name="assets-proxy-mappings"),
    path("assets/types", AssetTypeListView.as_view(), name="assets-types"),
    path("assets/types/<str:type_key>", AssetTypeDetailView.as_view(), name="assets-type-detail"),
    path("assets/models", AssetModelListCreateView.as_view(), name="assets-models"),
    path("assets/models/<uuid:model_id>", AssetModelDetailView.as_view(), name="assets-model-detail"),
    path(
        "assets/models/<uuid:model_id>/script",
        AssetModelScriptUploadView.as_view(),
        name="assets-model-script",
    ),
    path(
        "assets/models/<uuid:model_id>/script/current",
        AssetModelScriptDownloadView.as_view(),
        name="assets-model-script-current",
    ),
    path(
        "assets/models/<uuid:model_id>/script/template",
        AssetModelScriptTemplateView.as_view(),
        name="assets-model-script-template",
    ),
    path(
        "assets/models/<uuid:model_id>/sync",
        AssetModelSyncView.as_view(),
        name="assets-model-sync",
    ),
]
