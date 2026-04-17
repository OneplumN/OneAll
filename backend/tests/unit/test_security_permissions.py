from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import AuditLog
from apps.core.models.user import Role
from apps.tools.models import CodeDirectory, CodeRepository


def _make_user_with_permissions(username: str, *permissions: str):
    user_model = get_user_model()
    user = user_model.objects.create_user(username=username, password="pass1234")
    role = Role.objects.create(name=f"{username}-role", permissions=list(permissions))
    user.roles.set([role])
    return user


@pytest.mark.django_db
def test_role_list_requires_role_view_permission():
    client = APIClient()
    plain_user = _make_user_with_permissions("plain-user")
    client.force_authenticate(user=plain_user)
    response = client.get(reverse("role-list"))
    assert response.status_code == 403

    viewer = _make_user_with_permissions("role-viewer", "settings.roles.view")
    client.force_authenticate(user=viewer)
    response = client.get(reverse("role-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_role_update_blocks_non_superuser_from_modifying_superuser():
    manager = _make_user_with_permissions("manager-user", "settings.users.manage")
    superuser = get_user_model().objects.create_superuser(
        username="root-user",
        password="pass1234",
        email="root@example.com",
    )
    role = Role.objects.create(name="ops-role", permissions=["settings.users.view"])

    client = APIClient()
    client.force_authenticate(user=manager)
    response = client.put(
        reverse("user-role-update", kwargs={"user_id": superuser.id}),
        {"role_ids": [str(role.id)]},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_audit_log_requires_permission_and_masks_sensitive_fields():
    AuditLog.objects.create(
        action="security.test",
        target_type="SystemSettings",
        target_id=str(uuid.uuid4()),
        metadata={"token": "secret-token", "nested": {"password": "p@ss"}},
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0",
    )

    client = APIClient()
    plain_user = _make_user_with_permissions("plain-audit-user")
    client.force_authenticate(user=plain_user)
    response = client.get(reverse("audit-log-list"))
    assert response.status_code == 403

    viewer = _make_user_with_permissions("audit-viewer", "settings.audit_log.view")
    client.force_authenticate(user=viewer)
    response = client.get(reverse("audit-log-list"))
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["metadata"]["token"] == "***"
    assert result["metadata"]["nested"]["password"] == "***"
    assert result["ip_address"] is None
    assert result["user_agent"] == ""


@pytest.mark.django_db
def test_tool_definition_list_requires_library_view_permission():
    client = APIClient()
    plain_user = _make_user_with_permissions("plain-tool-user")
    client.force_authenticate(user=plain_user)
    response = client.get(reverse("tools-definitions"))
    assert response.status_code == 403

    viewer = _make_user_with_permissions("tool-viewer", "tools.library.view")
    client.force_authenticate(user=viewer)
    response = client.get(reverse("tools-definitions"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_asset_record_list_requires_records_view_permission():
    client = APIClient()
    plain_user = _make_user_with_permissions("plain-asset-user")
    client.force_authenticate(user=plain_user)
    response = client.get(reverse("assets-records"))
    assert response.status_code == 403

    viewer = _make_user_with_permissions("asset-viewer", "assets.records.view")
    client.force_authenticate(user=viewer)
    response = client.get(reverse("assets-records"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_code_repository_update_allows_owner_and_blocks_non_owner_without_manage():
    owner = _make_user_with_permissions("repo-owner", "tools.repository.create")
    other_user = _make_user_with_permissions("repo-other")
    directory = CodeDirectory.objects.create(key="ops", title="Ops", created_by=owner)
    repository = CodeRepository.objects.create(
        name="ops-script",
        language="python",
        tags=[],
        description="desc",
        directory=directory,
        content="print('hi')",
        created_by=owner,
        updated_by=owner,
    )

    client = APIClient()
    client.force_authenticate(user=other_user)
    response = client.put(
        reverse("code-repository-detail", kwargs={"repository_id": repository.id}),
        {"description": "updated-by-other"},
        format="json",
    )
    assert response.status_code == 403

    client.force_authenticate(user=owner)
    response = client.put(
        reverse("code-repository-detail", kwargs={"repository_id": repository.id}),
        {"description": "updated-by-owner"},
        format="json",
    )
    assert response.status_code == 200
