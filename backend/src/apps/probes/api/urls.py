from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .probe_task_views import (
    ProbeNodeTaskListCompatView,
    ProbeNodeTaskResultCompatView,
    ProbeScheduleResultView,
    ProbeTaskClaimView,
    ProbeTaskResultView,
)
from .probe_views import (
    ProbeHeartbeatCompatView,
    ProbeRegistrationView,
    ProbeNodeViewSet,
    ProbeRecentAlertListView,
    ProbeScheduleViewSet,
    ProbeScheduleExecutionViewSet,
)

router = DefaultRouter()
router.register(r'probes/nodes', ProbeNodeViewSet, basename='probe-node')
router.register(r'probes/schedules', ProbeScheduleViewSet, basename='probe-schedule')
router.register(r'probes/schedule-executions', ProbeScheduleExecutionViewSet, basename='probe-schedule-execution')

urlpatterns = [
  path("probes/register/", ProbeRegistrationView.as_view(), name="probe-register"),
  path("probes/alerts/recent", ProbeRecentAlertListView.as_view(), name="probe-alerts-recent"),
  path("probes/nodes/<uuid:pk>/heartbeat/", ProbeHeartbeatCompatView.as_view(), name="probe-node-heartbeat"),
  path("probes/nodes/<uuid:pk>/tasks/", ProbeNodeTaskListCompatView.as_view(), name="probe-node-tasks"),
  path(
      "probes/nodes/<uuid:pk>/tasks/<uuid:task_id>/result/",
      ProbeNodeTaskResultCompatView.as_view(),
      name="probe-node-task-result",
  ),
  path("probes/tasks/claim", ProbeTaskClaimView.as_view(), name="probe-task-claim"),
  path("probes/tasks/<uuid:task_id>/result", ProbeTaskResultView.as_view(), name="probe-task-result"),
  path("probes/schedules/<uuid:schedule_id>/result", ProbeScheduleResultView.as_view(), name="probe-schedule-result"),
  path("", include(router.urls)),
]
