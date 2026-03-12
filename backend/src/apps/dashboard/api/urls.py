from django.urls import path

from .alerts_summary_view import DashboardAlertsSummaryView
from .certificate_alerts_view import DashboardCertificateAlertsView
from .detection_grid_view import DashboardDetectionGridView
from .overview_view import DashboardOverviewView
from .todo_view import DashboardTodoView

urlpatterns = [
    path('dashboard/overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('dashboard/alerts-summary/', DashboardAlertsSummaryView.as_view(), name='dashboard-alerts-summary'),
    path('dashboard/todos/', DashboardTodoView.as_view(), name='dashboard-todos'),
    path('dashboard/detection-grid/', DashboardDetectionGridView.as_view(), name='dashboard-detection-grid'),
    path('dashboard/certificate-alerts/', DashboardCertificateAlertsView.as_view(), name='dashboard-certificate-alerts'),
]
