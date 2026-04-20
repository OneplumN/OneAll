from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import AuditLog
from apps.core.models.user import Role
from apps.settings.models import AlertChannel, PluginConfig
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


@pytest.mark.django_db
def test_code_repository_execute_requires_explicit_execute_permission():
    owner = _make_user_with_permissions("repo-exec-owner", "tools.repository.create")
    executor = _make_user_with_permissions("repo-executor", "tools.repository.execute")
    directory = CodeDirectory.objects.create(key="ops-exec", title="Ops Execute", created_by=owner)
    repository = CodeRepository.objects.create(
        name="ops-exec-script",
        language="python",
        tags=[],
        description="desc",
        directory=directory,
        content="print('hi')",
        created_by=owner,
        updated_by=owner,
    )
    repository.versions.create(version="v1.0.0", summary="init", change_log="", content="print('hi')", created_by=owner)
    repository.latest_version = repository.versions.first()
    repository.save(update_fields=["latest_version"])

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.post(
        reverse("code-repository-execute", kwargs={"repository_id": repository.id}),
        {"parameters": {}},
        format="json",
    )
    assert response.status_code == 403

    client.force_authenticate(user=executor)
    response = client.post(
        reverse("code-repository-execute", kwargs={"repository_id": repository.id}),
        {"parameters": {}},
        format="json",
    )
    assert response.status_code == 202


@pytest.mark.django_db
def test_alert_channel_list_masks_sensitive_config_fields():
    AlertChannel.objects.create(
        channel_type="wecom",
        name="企业微信机器人",
        enabled=True,
        config={
            "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=secret",
            "secret": "wecom-secret",
            "mentions": "13800000000",
        },
    )

    client = APIClient()
    viewer = _make_user_with_permissions("channel-viewer", "alerts.channels.view")
    client.force_authenticate(user=viewer)
    response = client.get(reverse("alert-channel-list"))

    assert response.status_code == 200
    channels = response.json()["channels"]
    wecom_channel = next(item for item in channels if item["type"] == "wecom")
    assert wecom_channel["config"]["webhook_url"] == "******"
    assert wecom_channel["config"]["secret"] == "******"
    assert wecom_channel["config"]["mentions"] == "13800000000"


@pytest.mark.django_db
def test_alert_channel_update_preserves_masked_sensitive_values():
    channel = AlertChannel.objects.create(
        channel_type="http",
        name="HTTP 回调",
        enabled=True,
        config={
            "url": "https://internal.example.com/hook",
            "headers": '{"Authorization":"Bearer abc"}',
            "body_template": '{"status":"ok"}',
        },
    )

    client = APIClient()
    manager = _make_user_with_permissions("channel-manager", "alerts.channels.update")
    client.force_authenticate(user=manager)
    response = client.put(
        reverse("alert-channel-update", kwargs={"channel_type": channel.channel_type}),
        {
            "enabled": True,
            "config": {
                "url": "******",
                "headers": "******",
                "body_template": '{"status":"changed"}',
            },
        },
        format="json",
    )

    assert response.status_code == 200
    channel.refresh_from_db()
    assert channel.config["url"] == "https://internal.example.com/hook"
    assert channel.config["headers"] == '{"Authorization":"Bearer abc"}'
    assert channel.config["body_template"] == '{"status":"changed"}'


@pytest.mark.django_db
def test_alert_channel_update_rejects_private_callback_url():
    channel = AlertChannel.objects.create(
        channel_type="http",
        name="HTTP 回调",
        enabled=True,
        config={},
    )

    client = APIClient()
    manager = _make_user_with_permissions("channel-manager-private", "alerts.channels.update")
    client.force_authenticate(user=manager)
    response = client.put(
        reverse("alert-channel-update", kwargs={"channel_type": channel.channel_type}),
        {
            "enabled": True,
            "config": {
                "url": "http://127.0.0.1:8080/internal",
                "method": "POST",
            },
        },
        format="json",
    )

    assert response.status_code == 400
    assert "不能指向内网" in response.json()["detail"]


@pytest.mark.django_db
def test_plugin_config_list_masks_sensitive_fields_and_patch_preserves_placeholder():
    plugin = PluginConfig.objects.create(
        name="监控插件",
        type="monitoring_overview",
        enabled=True,
        config={
            "webhook": "https://hooks.internal/plugin",
            "token": "plugin-secret-token",
            "remark": "visible",
        },
    )

    client = APIClient()
    viewer = _make_user_with_permissions("system-viewer", "settings.system.view")
    client.force_authenticate(user=viewer)
    response = client.get(reverse("plugin-config-list"))
    assert response.status_code == 200
    record = next(item for item in response.json() if item["id"] == str(plugin.id))
    assert record["config"]["webhook"] == "******"
    assert record["config"]["token"] == "******"
    assert record["config"]["remark"] == "visible"

    manager = _make_user_with_permissions("system-manager", "settings.system.manage")
    client.force_authenticate(user=manager)
    response = client.patch(
        reverse("plugin-config-detail", kwargs={"pk": plugin.id}),
        {
            "config": {
                "webhook": "******",
                "token": "******",
                "remark": "updated",
            }
        },
        format="json",
    )
    assert response.status_code == 200
    plugin.refresh_from_db()
    assert plugin.config["webhook"] == "https://hooks.internal/plugin"
    assert plugin.config["token"] == "plugin-secret-token"
    assert plugin.config["remark"] == "updated"


@pytest.mark.django_db
def test_plugin_config_update_rejects_private_webhook():
    plugin = PluginConfig.objects.create(
        name="Webhook 插件",
        type="monitoring_overview",
        enabled=True,
        config={},
    )

    client = APIClient()
    manager = _make_user_with_permissions("system-manager-private", "settings.system.manage")
    client.force_authenticate(user=manager)
    response = client.patch(
        reverse("plugin-config-detail", kwargs={"pk": plugin.id}),
        {
            "config": {
                "webhook": "http://127.0.0.1:9000/hook",
            }
        },
        format="json",
    )

    assert response.status_code == 400
    assert "不能指向内网" in str(response.json())


@pytest.mark.django_db
@override_settings(PROBE_BOOTSTRAP_TOKEN=None)
def test_probe_registration_requires_configured_bootstrap_token():
    client = APIClient()
    response = client.post(
        reverse("probe-register"),
        {
            "hostname": "probe-shanghai",
            "network_type": "internal",
            "supported_protocols": ["HTTP"],
        },
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_dashboard_overview_requires_monitoring_overview_view_permission():
    client = APIClient()
    plain_user = _make_user_with_permissions("plain-dashboard-user")
    client.force_authenticate(user=plain_user)
    response = client.get(reverse("dashboard-overview"))
    assert response.status_code == 403

    viewer = _make_user_with_permissions("dashboard-viewer", "monitoring.overview.view")
    client.force_authenticate(user=viewer)
    response = client.get(reverse("dashboard-overview"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_monitoring_request_list_requires_view_permission():
    client = APIClient()
    plain_user = _make_user_with_permissions("plain-request-user")
    client.force_authenticate(user=plain_user)
    response = client.get(reverse("monitoring-request"))
    assert response.status_code == 403

    viewer = _make_user_with_permissions("request-viewer", "detection.schedules.view")
    client.force_authenticate(user=viewer)
    response = client.get(reverse("monitoring-request"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_probe_node_list_requires_view_permission():
    client = APIClient()
    plain_user = _make_user_with_permissions("plain-probe-user")
    client.force_authenticate(user=plain_user)
    response = client.get(reverse("probe-node-list"))
    assert response.status_code == 403

    viewer = _make_user_with_permissions("probe-viewer", "probes.nodes.view")
    client.force_authenticate(user=viewer)
    response = client.get(reverse("probe-node-list"))
    assert response.status_code == 200
