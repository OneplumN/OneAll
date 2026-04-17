from __future__ import annotations

import json

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.assets.api.asset_view import AssetRecordImportView, AssetRecordListView
from apps.assets.models import AssetRecord
from apps.core.models.user import User


@pytest.mark.django_db
def test_create_asset_without_existing_conflict_succeeds() -> None:
    factory = APIRequestFactory()
    payload = {
        "source": "CMDB",
        "name": "https://account.aliyun.com/",
        "system_name": "ALIYUN-ACCOUNT",
        "owners": [],
        "contacts": [],
        "metadata": {
            "asset_type": "cmdb-domain",
            "domain": "https://account.aliyun.com/",
            "system_name": "ALIYUN-ACCOUNT",
        },
    }
    request = factory.post("/api/assets/records", data=json.dumps(payload), content_type="application/json")
    user = User.objects.create(username="tester")
    force_authenticate(request, user=user)

    view = AssetRecordListView.as_view()
    response = view(request)

    assert response.status_code == 201
    assert AssetRecord.objects.filter(
        source="CMDB",
        asset_type="cmdb-domain",
        canonical_key="https://account.aliyun.com/",
        is_removed=False,
    ).count() == 1


@pytest.mark.django_db
def test_import_conflicting_asset_rejected() -> None:
    # 先放一条已有资产
    AssetRecord.objects.create(
        source=AssetRecord.Source.CMDB,
        asset_type="cmdb-domain",
        canonical_key="example.com",
        external_id="domain:example.com",
        name="example.com",
        metadata={"asset_type": "cmdb-domain", "domain": "example.com"},
        sync_status="synced",
    )

    factory = APIRequestFactory()
    payload = {
        "records": [
            {
                "source": "CMDB",
                "name": "example.com",
                "metadata": {
                    "asset_type": "cmdb-domain",
                    "domain": "example.com",
                },
            }
        ]
    }
    request = factory.post("/api/assets/import", data=json.dumps(payload), content_type="application/json")
    user = User.objects.create(username="tester")
    force_authenticate(request, user=user)
    view = AssetRecordImportView.as_view()
    response = view(request)

    assert response.status_code == 200
    body = response.data
    assert body["created"] == 0
    assert body["failed"] == 1
    assert body["errors"]
    err = body["errors"][0]
    assert "canonical_key" in err["errors"]
