from __future__ import annotations

from django.urls import path

from apps.alerts.api.views import (
    AlertCheckDetailView,
    AlertCheckListView,
    AlertCheckScheduleListView,
    AlertEventListView,
    AlertSystemOverviewView,
)

urlpatterns = [
    path("alerts/events", AlertEventListView.as_view(), name="alerts-events"),
    path("alerts/checks", AlertCheckListView.as_view(), name="alerts-checks"),
    path(
        "alerts/checks/system-overview",
        AlertSystemOverviewView.as_view(),
        name="alerts-checks-system-overview",
    ),
    path(
        "alerts/checks/<uuid:check_id>",
        AlertCheckDetailView.as_view(),
        name="alerts-check-detail",
    ),
    path(
        "alerts/checks/<uuid:check_id>/schedules",
        AlertCheckScheduleListView.as_view(),
        name="alerts-check-schedules",
    ),
]
