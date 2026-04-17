from __future__ import annotations

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
def test_download_current_script(tmp_path, monkeypatch):
    user = _make_user_with_perm("asset_model_admin6", "assets.records.manage")

    # Patch scripts root to temp dir
    scripts_root = tmp_path / "scripts"
    scripts_root.mkdir()
    monkeypatch.setattr(script_loader, "SCRIPTS_ROOT", scripts_root, raising=True)

    model = AssetModel.objects.create(
        key="download-model",
        label="下载测试模型",
        category="cmdb",
        fields=[{"key": "field1", "label": "字段1"}],
        unique_key=["field1"],
        script_id="download-model",
    )

    script_path = scripts_root / "download-model.py"
    script_content = "def run(context):\n    return []\n"
    script_path.write_text(script_content, encoding="utf-8")

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("assets-model-script-current", kwargs={"model_id": str(model.id)})
    resp = client.get(url)

    assert resp.status_code == 200
    assert resp["Content-Disposition"].startswith('attachment; filename="asset_sync_download-model.py"')
    assert script_content in resp.content.decode("utf-8")

