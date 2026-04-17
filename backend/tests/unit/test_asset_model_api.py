from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.assets.models import AssetModel
from apps.core.models.user import Role


def _make_user_with_perm(username: str, permission: str):
    user_model = get_user_model()
    user = user_model.objects.create_user(username=username, password="pass1234")
    role = Role.objects.create(name=f"{username}-role")
    role.permissions = [permission]
    role.save()
    user.roles.set([role])
    return user


@pytest.mark.django_db
def test_create_and_list_asset_models():
    user = _make_user_with_perm("asset_model_admin", "assets.records.manage")

    client = APIClient()
    client.force_authenticate(user=user)

    create_url = reverse("assets-models")
    payload = {
        "key": "aliyun-account",
        "label": "阿里云账号",
        "category": "cmdb",
        "fields": [
            {"key": "account_id", "label": "账号ID", "type": "string"},
            {"key": "owner", "label": "负责人", "type": "string"},
        ],
        "unique_key": ["account_id"],
    }

    resp = client.post(create_url, payload, format="json")
    assert resp.status_code == 201
    data = resp.json()
    assert data["key"] == "aliyun-account"
    assert data["label"] == "阿里云账号"
    assert data["unique_key"] == ["account_id"]

    # list
    list_resp = client.get(create_url)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(item["key"] == "aliyun-account" for item in items)


@pytest.mark.django_db
def test_update_asset_model_unique_key_validation():
    user = _make_user_with_perm("asset_model_admin2", "assets.records.manage")

    model = AssetModel.objects.create(
        key="test-model",
        label="测试模型",
        category="cmdb",
        fields=[{"key": "field1", "label": "字段1", "type": "string"}],
        unique_key=["field1"],
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("assets-model-detail", kwargs={"model_id": str(model.id)})

    # unique_key references undefined field -> should fail
    resp = client.put(
        url,
        {
            "key": "test-model",
            "label": "测试模型",
            "category": "cmdb",
            "fields": model.fields,
            "unique_key": ["not_exists"],
            "is_active": True,
        },
        format="json",
    )
    assert resp.status_code == 400
    body = resp.json()
    assert "unique_key" in body

