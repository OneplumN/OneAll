import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.assets.models import AssetRecord
from apps.core.models.user import Role


def _make_user_with_permissions(username: str, *permissions: str):
    user_model = get_user_model()
    user = user_model.objects.create_user(username=username, password="pass1234")
    role = Role.objects.create(name=f"{username}-role", permissions=list(permissions))
    user.roles.set([role])
    return user


@pytest.mark.django_db
def test_create_asset_record_via_api():
    user = _make_user_with_permissions("tester", "assets.records.manage")

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "source": "CMDB",
        "external_id": "domain:example.com",
        "name": "example.com",
        "system_name": "OneAll",
        "metadata": {
            "asset_type": "cmdb-domain",
            "domain": "example.com",
            "network_type": "internet",
            "owner": "张三",
        },
        "contacts": ["000123", "000456"],
    }

    url = reverse("assets-records")
    response = client.post(url, payload, format="json")

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "example.com"
    assert data["source"] == "CMDB"

    record = AssetRecord.objects.get(id=data["id"])
    assert record.metadata["domain"] == "example.com"
    assert record.metadata["asset_type"] == "cmdb-domain"
    assert record.contacts == ["000123", "000456"]


@pytest.mark.django_db
def test_import_assets_partial_success():
    user = _make_user_with_permissions("tester-import", "assets.records.manage")

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "records": [
            {
                "source": "CMDB",
                "name": "demo-domain",
                "metadata": {"asset_type": "cmdb-domain", "domain": "demo-domain"},
            },
            {
                "source": "CMDB",
                # missing name/external id
            },
        ]
    }

    url = reverse("assets-import")
    response = client.post(url, payload, format="json")

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 1
    assert data["failed"] == 1
    assert AssetRecord.objects.count() == 1


@pytest.mark.django_db
def test_import_assets_all_failed():
    user = _make_user_with_permissions("tester2", "assets.records.manage")

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {"records": [{"source": "CMDB"}]}

    url = reverse("assets-import")
    response = client.post(url, payload, format="json")

    assert response.status_code == 400
    assert "errors" in response.json()
    assert AssetRecord.objects.count() == 0
