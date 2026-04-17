from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.assets.models import AssetSyncRun
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
def test_list_asset_sync_runs_basic():
    user = _make_user_with_perm("sync_tester", "assets.records.view")

    # 创建几条同步记录
    AssetSyncRun.objects.create(mode=AssetSyncRun.Mode.ASYNC, status=AssetSyncRun.Status.QUEUED)
    AssetSyncRun.objects.create(
        mode=AssetSyncRun.Mode.SYNC,
        status=AssetSyncRun.Status.SUCCEEDED,
        summary={"totals": {"created": 1}},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("assets-sync-runs")
    response = client.get(url, {"limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert "total" in data and data["total"] >= 2
    assert "items" in data
    assert isinstance(data["items"], list)
    assert any(item["status"] == "succeeded" for item in data["items"])


@pytest.mark.django_db
def test_get_asset_sync_run_detail_without_changes():
    user = _make_user_with_perm("sync_tester2", "assets.records.view")

    run = AssetSyncRun.objects.create(
        mode=AssetSyncRun.Mode.SYNC,
        status=AssetSyncRun.Status.SUCCEEDED,
        summary={"totals": {"created": 2, "updated": 3}},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("assets-sync-run-detail", kwargs={"run_id": str(run.id)})
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == str(run.id)
    assert data["status"] == "succeeded"
    assert data.get("summary", {}).get("totals", {}).get("created") == 2
    assert "changes" not in data
