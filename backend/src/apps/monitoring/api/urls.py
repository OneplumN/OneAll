from django.urls import path

from .cmdb_validation_view import DomainValidationView
from .detection_detail_view import DetectionDetailView
from .one_off_detection_view import OneOffDetectionView
from .monitoring_approval_view import (
    MonitoringRequestApproveView,
    MonitoringRequestRejectView,
    MonitoringRequestResubmitView,
    MonitoringRequestStatusCallbackView,
)
from .monitoring_history_view import MonitoringHistoryView
from .monitoring_request_detail_view import MonitoringRequestDetailView
from .monitoring_request_view import MonitoringRequestView

urlpatterns = [
    path('detection/one-off', OneOffDetectionView.as_view(), name='detection-one-off'),
    path('detection/tasks/<uuid:detection_id>', DetectionDetailView.as_view(), name='detection-detail'),
    path('detection/cmdb/validate', DomainValidationView.as_view(), name='detection-cmdb-validate'),
    path('monitoring/requests', MonitoringRequestView.as_view(), name='monitoring-request'),
    path('monitoring/requests/<uuid:pk>', MonitoringRequestDetailView.as_view(), name='monitoring-request-detail'),
    path('monitoring/requests/<uuid:pk>/status', MonitoringRequestStatusCallbackView.as_view(), name='monitoring-request-status'),
    path('monitoring/requests/<uuid:pk>/approve', MonitoringRequestApproveView.as_view(), name='monitoring-request-approve'),
    path('monitoring/requests/<uuid:pk>/reject', MonitoringRequestRejectView.as_view(), name='monitoring-request-reject'),
    path('monitoring/requests/<uuid:pk>/resubmit', MonitoringRequestResubmitView.as_view(), name='monitoring-request-resubmit'),
    path('monitoring/tasks/history', MonitoringHistoryView.as_view(), name='monitoring-history'),
]
