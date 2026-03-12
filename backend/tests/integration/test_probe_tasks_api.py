import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.monitoring.models import DetectionTask
from apps.probes.models import ProbeNode


@pytest.fixture()
def api_client():
    user_model = get_user_model()
    user = user_model.objects.create_user(username='probe-tester', password='password')
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_fetch_tasks_and_submit_result(api_client):
    probe = ProbeNode.objects.create(
        name='probe-alpha',
        location='Shanghai',
        network_type='external',
        supported_protocols=['HTTP', 'HTTPS'],
    )
    token = 'probe-token'
    probe.set_api_token(token)
    task = DetectionTask.objects.create(
        target='https://example.com',
        protocol=DetectionTask.Protocol.HTTPS,
        probe=probe,
        status=DetectionTask.Status.SCHEDULED,
        metadata={'timeout_seconds': 45, 'expect_status': 200},
    )

    response = api_client.get(
        f'/api/probes/nodes/{probe.id}/tasks/',
        HTTP_AUTHORIZATION=f'ProbeToken {token}',
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]['timeout_seconds'] == 45
    assert payload[0]['expect_status'] == 200

    task.refresh_from_db()
    assert task.status == DetectionTask.Status.RUNNING

    result_payload = {
        'status': 'success',
        'latency_ms': 150,
        'status_code': 200,
        'metadata': {'detail': 'ok'},
    }
    result_resp = api_client.post(
        f'/api/probes/nodes/{probe.id}/tasks/{task.id}/result/',
        result_payload,
        format='json',
        HTTP_AUTHORIZATION=f'ProbeToken {token}',
    )
    assert result_resp.status_code == 202

    task.refresh_from_db()
    assert task.status == DetectionTask.Status.SUCCEEDED
    assert task.response_time_ms == 150
    assert task.status_code == '200'
    assert task.result_payload == {'detail': 'ok'}
