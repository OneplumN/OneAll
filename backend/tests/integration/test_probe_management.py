import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.core.models.user import Role
from apps.probes.models import ProbeNode


@pytest.fixture()
def api_client():
    user_model = get_user_model()
    user = user_model.objects.create_user(username='tester', password='password')
    role = Role.objects.create(name='probe-node-admin-role', permissions=['probes.nodes.manage'])
    user.roles.set([role])
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_create_probe_and_process_heartbeat(api_client):
    probe_payload = {
        'name': 'probe-shanghai',
        'location': '上海-张江',
        'network_type': 'internal',
        'supported_protocols': ['HTTP', 'HTTPS']
    }
    probe_response = api_client.post('/api/probes/nodes/', probe_payload, format='json')
    assert probe_response.status_code == 201
    probe_id = probe_response.data['id']

    heartbeat_payload = {
        'status': 'online',
        'supported_protocols': ['HTTP', 'HTTPS', 'WSS'],
        'metrics': {
            'cpu_usage': 55.5,
            'memory_usage_mb': 2048,
            'task_queue_depth': 4,
            'active_tasks': 2,
            'queue_latency_ms': 120
        }
    }
    token = 'probe-secret'
    probe = ProbeNode.objects.get(id=probe_id)
    probe.set_api_token(token)
    heartbeat_response = api_client.post(
        f'/api/probes/nodes/{probe_id}/heartbeat/',
        heartbeat_payload,
        format='json',
        HTTP_AUTHORIZATION=f'ProbeToken {token}',
    )
    assert heartbeat_response.status_code == 202

    probe.refresh_from_db()
    assert probe.status == 'online'
    assert set(probe.supported_protocols) == {'HTTP', 'HTTPS', 'WSS'}
    assert probe.last_heartbeat_at is not None
    assert probe.runtime_metrics['cpu_usage'] == 55.5
    assert probe.runtime_metrics['task_queue_depth'] == 4


@pytest.mark.django_db
def test_heartbeat_unknown_probe_is_rejected():
    client = APIClient()
    probe_id = uuid.uuid4()
    heartbeat_payload = {
        'status': 'online',
        'supported_protocols': ['HTTP'],
        'metrics': {'cpu_usage': 12.5}
    }
    token = 'bootstrap-secret'
    response = client.post(
        f'/api/probes/nodes/{probe_id}/heartbeat/',
        heartbeat_payload,
        format='json',
        HTTP_AUTHORIZATION=f'ProbeToken {token}',
    )
    assert response.status_code == 404
    assert not ProbeNode.objects.filter(id=probe_id).exists()


@pytest.mark.django_db
def test_rotate_token(api_client):
    probe = ProbeNode.objects.create(
        name='probe-rotate',
        location='深圳',
        network_type='external',
        supported_protocols=['HTTP']
    )
    payload = {'token': 'new-strong-token-123456'}
    response = api_client.post(f'/api/probes/nodes/{probe.id}/token/', payload, format='json')
    assert response.status_code == 200
    data = response.json()
    assert data['token'] == payload['token']
    probe.refresh_from_db()
    assert probe.api_token_hint == payload['token'][-4:]
    assert probe.check_api_token(payload['token'])


@pytest.mark.django_db
def test_runtime_endpoint_returns_metrics(api_client):
    probe = ProbeNode.objects.create(
        name='probe-runtime',
        location='广州',
        network_type='external',
        supported_protocols=['HTTPS']
    )
    token = 'runtime-secret-token'
    probe.set_api_token(token)
    client = APIClient()
    heartbeat_payload = {
        'status': 'online',
        'supported_protocols': ['HTTPS'],
        'metrics': {
            'cpu_usage': 80,
            'memory_usage_mb': 1024,
            'load_avg': 1.25,
            'task_queue_depth': 6,
            'active_tasks': 3,
            'queue_latency_ms': 450
        }
    }
    response = client.post(
        f'/api/probes/nodes/{probe.id}/heartbeat/',
        heartbeat_payload,
        format='json',
        HTTP_AUTHORIZATION=f'ProbeToken {token}',
    )
    assert response.status_code == 202

    runtime_response = api_client.get(f'/api/probes/nodes/{probe.id}/runtime/')
    assert runtime_response.status_code == 200
    data = runtime_response.json()
    metrics = data['resource_metrics']
    assert metrics['cpu_usage'] == 80
    assert metrics['memory_usage_mb'] == 1024
    assert metrics['task_queue_depth'] == 6
    assert data['tasks']['scheduled'] == 0
