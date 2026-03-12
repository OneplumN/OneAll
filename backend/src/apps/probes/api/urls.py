from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .probe_views import (
    ProbeNodeViewSet,
    ProbeScheduleViewSet,
    ProbeScheduleExecutionViewSet,
    RecentProbeAlertView,
)

router = DefaultRouter()
router.register(r'probes/nodes', ProbeNodeViewSet, basename='probe-node')
router.register(r'probes/schedules', ProbeScheduleViewSet, basename='probe-schedule')
router.register(r'probes/schedule-executions', ProbeScheduleExecutionViewSet, basename='probe-schedule-execution')

urlpatterns = [
  path('probes/alerts/recent/', RecentProbeAlertView.as_view(), name='probe-alerts-recent'),
  path('', include(router.urls)),
]
