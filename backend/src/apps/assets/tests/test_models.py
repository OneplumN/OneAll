from __future__ import annotations

import pytest

from apps.assets.models import AssetModel


@pytest.mark.django_db
def test_create_asset_model():
    model = AssetModel.objects.create(
        key="aliyun-account",
        label="阿里云账号",
        category="cmdb",
        fields=[{"key": "account_id", "label": "账号ID", "type": "string"}],
        unique_key=["account_id"],
    )

    fetched = AssetModel.objects.get(pk=model.pk)
    assert fetched.key == "aliyun-account"
    assert fetched.label == "阿里云账号"
    assert fetched.category == "cmdb"
    assert fetched.fields and fetched.fields[0]["key"] == "account_id"
    assert fetched.unique_key == ["account_id"]

