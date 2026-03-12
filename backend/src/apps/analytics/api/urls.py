from django.urls import path

from .report_view import DetectionReportView
from .asset_governance_view import AssetGovernanceOverviewView, AssetProxyHostsView

urlpatterns = [
    path('analytics/reports/detection', DetectionReportView.as_view(), name='analytics-detection-report'),
    path('analytics/assets/overview', AssetGovernanceOverviewView.as_view(), name='analytics-asset-governance-overview'),
    path('analytics/assets/proxy-hosts', AssetProxyHostsView.as_view(), name='analytics-asset-proxy-hosts'),
]
