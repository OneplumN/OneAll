from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.settings.models import SystemSettings
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
def test_list_asset_types_returns_override_values():
    SystemSettings.objects.create(
        integrations={
            "assets": {
                "types": {
                    "cmdb-domain": {
                        "unique_fields": ["system_name", "domain"],
                        "extra_fields": [
                            {
                                "key": "env",
                                "label": "环境",
                                "type": "string",
                                "options": [],
                                "required": False,
                                "list_visible": True,
                            }
                        ],
                    }
                }
            }
        }
    )
    user = _make_user_with_perm("asset_type_reader", "assets.records.view")

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("assets-types"))

    assert response.status_code == 200
    payload = response.json()
    cmdb_domain = next(item for item in payload if item["key"] == "cmdb-domain")
    assert cmdb_domain["unique_fields"] == ["system_name", "domain"]
    assert cmdb_domain["default_unique_fields"] == ["domain"]
    assert cmdb_domain["extra_fields"][0]["key"] == "env"


@pytest.mark.django_db
def test_patch_asset_type_updates_asset_settings():
    user = _make_user_with_perm("asset_type_admin", "assets.records.manage")

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        reverse("assets-type-detail", kwargs={"type_key": "cmdb-domain"}),
        data={
            "unique_fields": ["system_name", "domain"],
            "extra_fields": [
                {
                    "key": "env",
                    "label": "环境",
                    "type": "enum",
                    "options": ["prod", "test"],
                    "required": True,
                    "list_visible": True,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["unique_fields"] == ["system_name", "domain"]
    assert payload["default_unique_fields"] == ["domain"]
    assert payload["extra_fields"][0]["key"] == "env"
    assert payload["extra_fields"][0]["options"] == ["prod", "test"]

    settings = SystemSettings.objects.first()
    overrides = settings.integrations["assets"]["types"]["cmdb-domain"]
    assert overrides["unique_fields"] == ["system_name", "domain"]
    assert overrides["extra_fields"][0]["label"] == "环境"


@pytest.mark.django_db
def test_patch_asset_type_rejects_unknown_unique_field():
    user = _make_user_with_perm("asset_type_admin2", "assets.records.manage")

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        reverse("assets-type-detail", kwargs={"type_key": "cmdb-domain"}),
        data={"unique_fields": ["not_exists"]},
        format="json",
    )

    assert response.status_code == 400
    assert "unique_fields" in response.json()
