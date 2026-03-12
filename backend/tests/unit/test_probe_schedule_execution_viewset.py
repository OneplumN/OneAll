from apps.probes.api.probe_views import ProbeScheduleExecutionViewSet
from apps.probes.models import ProbeScheduleExecution


def test_aggregate_status_counts_merges_aliases():
    viewset = ProbeScheduleExecutionViewSet()
    queryset_counts = [
        {"status": "succeeded", "total": 4},
        {"status": "SUCCEEDED", "total": 3},
        {"status": "success", "total": 2},
        {"status": "failed", "total": 5},
        {"status": "failure", "total": 1},
        {"status": "error", "total": 1},
        {"status": "missed", "total": 2},
        {"status": "timeout", "total": 4},
    ]

    normalized_counts = viewset._aggregate_status_counts(queryset_counts)

    assert normalized_counts[ProbeScheduleExecution.Status.SUCCEEDED] == 9
    assert normalized_counts[ProbeScheduleExecution.Status.FAILED] == 7
    assert normalized_counts[ProbeScheduleExecution.Status.MISSED] == 6
