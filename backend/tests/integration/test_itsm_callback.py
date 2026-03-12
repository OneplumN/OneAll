import uuid

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.monitoring.models import MonitoringRequest


@pytest.mark.django_db
def test_itsm_callback_updates_status(mocker):
    request = MonitoringRequest.objects.create(
        id=uuid.uuid4(),
        title='SSL 拨测',
        target='https://example.com',
        protocol='HTTPS',
        status=MonitoringRequest.Status.PENDING,
        itsm_ticket_id='ITSM-123',
        metadata={},
    )

    mocker.patch('apps.monitoring.services.monitoring_job_service.create_job_for_request')

    client = APIClient()
    client.force_authenticate(user=None)

    url = reverse('monitoring-request-status', kwargs={'pk': request.id})
    payload = {
        'status': 'approved',
        'itsm_ticket_id': 'ITSM-123',
        'approver': 'ops-admin',
    }

    response = client.patch(url, payload, format='json')
    assert response.status_code == 200

    request.refresh_from_db()
    assert request.status == 'approved'
