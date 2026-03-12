import pytest
import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

from apps.tools.models import CodeDirectory, CodeRepository, CodeRepositoryVersion, ToolExecution


@pytest.fixture()
def api_client():
    user_model = get_user_model()
    user = user_model.objects.create_user(username='repo-admin', password='password')
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_execute_code_repository_script(api_client):
    directory = CodeDirectory.objects.create(
        key=f'test-assets-{uuid.uuid4().hex[:6]}',
        title='资产脚本',
        keywords=['assets'],
    )
    repository = CodeRepository.objects.create(
        name='同步 Zabbix 主机',
        language='python',
        tags=['zabbix'],
        description='同步 Zabbix 资产',
        directory=directory,
        content='print("sync zabbix")',
    )
    version = CodeRepositoryVersion.objects.create(
        repository=repository,
        version='v1.0.0',
        summary='init',
        change_log='',
        content='print("sync zabbix")',
    )
    repository.latest_version = version
    repository.save(update_fields=['latest_version'])

    url = reverse('code-repository-execute', args=[repository.id])
    response = api_client.post(url, {'parameters': {'source': 'test'}}, format='json')

    assert response.status_code == 202
    data = response.json()
    assert 'run_id' in data

    assert ToolExecution.objects.filter(tool__metadata__repository_id=str(repository.id)).exists()
