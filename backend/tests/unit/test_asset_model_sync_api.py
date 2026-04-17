from __future__ import annotations

import io

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.assets.models import AssetModel, AssetRecord, AssetSyncChange, AssetSyncRun
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
def test_sync_asset_model_creates_records(tmp_path, monkeypatch):
    user = _make_user_with_perm("asset_model_admin7", "assets.records.manage")

    # Patch scripts root to temp dir
    scripts_root = tmp_path / "scripts"
    scripts_root.mkdir()
    monkeypatch.setattr(script_loader, "SCRIPTS_ROOT", scripts_root, raising=True)

    # Create model
    model = AssetModel.objects.create(
        key="sync-model",
        label="同步测试模型",
        category="cmdb",
        fields=[{"key": "field1", "label": "字段1"}],
        unique_key=["field1"],
        script_id="sync-model",
    )

    # Write a simple script that returns two records
    script_content = (
        "def run(context):\n"
        "    asset_type = context.get('asset_type', 'sync-model')\n"
        "    return [\n"
        "        {\n"
        "            'asset_type': asset_type,\n"
        "            'source': 'Manual',\n"
        "            'external_id': 'id-1',\n"
        "            'metadata': {'field1': 'v1'},\n"
        "        },\n"
        "        {\n"
        "            'asset_type': asset_type,\n"
        "            'source': 'Manual',\n"
        "            'external_id': 'id-2',\n"
        "            'metadata': {'field1': 'v2'},\n"
        "        },\n"
        "    ]\n"
    )
    script_path = scripts_root / "sync-model.py"
    script_path.write_text(script_content, encoding="utf-8")

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("assets-model-sync", kwargs={"model_id": str(model.id)})
    resp = client.post(url, {}, format="json")

    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"]
    assert data["model_key"] == "sync-model"
    summary = data["summary"]
    assert summary["trigger_type"] == "asset_model"
    assert summary["model_key"] == "sync-model"
    assert summary["script_id"] == "sync-model"
    assert summary["totals"]["created"] == 2

    # Ensure AssetRecord rows were created
    records = AssetRecord.objects.filter(asset_type="sync-model").order_by("external_id")
    assert records.count() == 2
    assert records[0].external_id == "id-1"
    assert records[0].metadata.get("field1") == "v1"
    assert records[1].external_id == "id-2"
    assert records[1].metadata.get("field1") == "v2"

    run = AssetSyncRun.objects.get(id=data["run_id"])
    assert run.status == AssetSyncRun.Status.SUCCEEDED
    assert run.source_filters == ["sync-model"]
    assert run.summary["trigger_type"] == "asset_model"
    assert run.summary["totals"]["created"] == 2
    assert AssetSyncChange.objects.filter(run=run, action=AssetSyncChange.Action.CREATE).count() == 2


@pytest.mark.django_db
def test_sync_asset_model_rejects_template_rows(tmp_path, monkeypatch):
    user = _make_user_with_perm("asset_model_admin8", "assets.records.manage")

    scripts_root = tmp_path / "scripts"
    scripts_root.mkdir()
    monkeypatch.setattr(script_loader, "SCRIPTS_ROOT", scripts_root, raising=True)

    model = AssetModel.objects.create(
        key="template-model",
        label="模板模型",
        category="cmdb",
        fields=[{"key": "field1", "label": "字段1"}],
        unique_key=["field1"],
        script_id="template-model",
    )

    script_content = (
        "def run(context):\n"
        "    return [\n"
        "        {\n"
        "            'asset_type': context.get('asset_type', 'template-model'),\n"
        "            'source': 'Manual',\n"
        "            'external_id': 'demo-1',\n"
        "            'metadata': {'field1': ''},\n"
        "        },\n"
        "    ]\n"
    )
    (scripts_root / "template-model.py").write_text(script_content, encoding="utf-8")

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("assets-model-sync", kwargs={"model_id": str(model.id)})
    resp = client.post(url, {}, format="json")

    assert resp.status_code == 400
    assert "模板示例" in resp.json()["detail"]
    assert AssetRecord.objects.filter(asset_type="template-model").count() == 0

    run = AssetSyncRun.objects.latest("created_at")
    assert run.status == AssetSyncRun.Status.FAILED
    assert "模板示例" in run.error_message
