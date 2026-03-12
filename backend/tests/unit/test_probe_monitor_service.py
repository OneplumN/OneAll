from __future__ import annotations

import pytest

from apps.probes.models import ProbeNode
from apps.probes.services import probe_monitor_service


@pytest.mark.django_db
def test_handle_heartbeat_normalizes_runtime_metrics():
    probe = ProbeNode.objects.create(
        name='probe-metrics',
        location='hangzhou',
        network_type='internal',
        supported_protocols=['HTTP']
    )

    payload = {
        'status': 'online',
        'metrics': {
            'cpu_usage': 150,
            'memory_usage_mb': -10,
            'load_avg': 2.5,
            'task_queue_depth': -1,
            'active_tasks': 4,
            'queue_latency_ms': 30
        }
    }

    probe_monitor_service.handle_heartbeat(probe=probe, payload=payload)

    probe.refresh_from_db()
    metrics = probe.runtime_metrics
    assert metrics['cpu_usage'] == 100
    assert metrics['memory_usage_mb'] == 0
    assert metrics['load_avg'] == 2.5
    assert metrics['task_queue_depth'] == 0
    assert metrics['active_tasks'] == 4
    assert metrics['queue_latency_ms'] == 30
    assert 'reported_at' in metrics
