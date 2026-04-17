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
def test_download_script_template_basic():
    user = _make_user_with_perm("asset_model_admin5", "assets.records.manage")

    model = AssetModel.objects.create(
        key="sample-model",
        label="示例模型",
        category="cmdb",
        fields=[
            {"key": "field1", "label": "字段1"},
            {"key": "field2", "label": "字段2"},
        ],
        unique_key=["field1"],
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("assets-model-script-template", kwargs={"model_id": str(model.id)})
    resp = client.get(url)

    assert resp.status_code == 200
    text = resp.content.decode("utf-8")
    assert "资产同步脚本模板（自动生成）" in text
    assert "sample-model" in text
    assert "field1" in text
    assert "field2" in text
    assert "API_URL = \"\"" in text
    assert "fetch_source_rows" in text
    assert "demo-1" not in text
