from __future__ import annotations

import io

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.assets.models import AssetModel
from apps.assets.services import script_loader
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
def test_upload_valid_script(tmp_path, monkeypatch):
    user = _make_user_with_perm("asset_model_admin3", "assets.records.manage")

    # Patch scripts root to temp dir to avoid touching real filesystem
    scripts_root = tmp_path / "scripts"
    monkeypatch.setattr(script_loader, "SCRIPTS_ROOT", scripts_root, raising=True)

    model = AssetModel.objects.create(
        key="test-model",
        label="测试模型",
        category="cmdb",
        fields=[{"key": "field1", "label": "字段1", "type": "string"}],
        unique_key=["field1"],
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("assets-model-script", kwargs={"model_id": str(model.id)})
    content = b"def run(context):\n    return []\n"
    file_obj = io.BytesIO(content)
    file_obj.name = "script.py"

    resp = client.post(url, {"file": file_obj}, format="multipart")
    assert resp.status_code == 200
    data = resp.json()
    assert data["script_id"] == model.key

    refreshed = AssetModel.objects.get(pk=model.pk)
    assert refreshed.script_id == model.key


@pytest.mark.django_db
def test_upload_invalid_script_rejected(tmp_path, monkeypatch):
    user = _make_user_with_perm("asset_model_admin4", "assets.records.manage")

    scripts_root = tmp_path / "scripts"
    monkeypatch.setattr(script_loader, "SCRIPTS_ROOT", scripts_root, raising=True)

    model = AssetModel.objects.create(
        key="bad-model",
        label="坏脚本模型",
        category="cmdb",
        fields=[{"key": "field1", "label": "字段1", "type": "string"}],
        unique_key=["field1"],
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("assets-model-script", kwargs={"model_id": str(model.id)})
    # Missing run(context)
    content = b"def foo():\n    return []\n"
    file_obj = io.BytesIO(content)
    file_obj.name = "script.py"

    resp = client.post(url, {"file": file_obj}, format="multipart")
    assert resp.status_code == 400
    body = resp.json()
    assert "脚本校验失败" in body.get("detail", "")

    refreshed = AssetModel.objects.get(pk=model.pk)
    assert not refreshed.script_id

