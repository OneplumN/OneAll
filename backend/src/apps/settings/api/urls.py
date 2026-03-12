from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .branding_view import PublicBrandingView
from .system_settings_view import SystemSettingsView
from .plugin_config_view import PluginConfigViewSet
from .role_views import (
    LDAPSyncView,
    PermissionCatalogView,
    RoleViewSet,
    UserDeleteView,
    UserRoleListView,
    UserRoleUpdateView,
)
from .alert_channel_views import AlertChannelListView, AlertChannelTestView, AlertChannelUpdateView
from .alert_template_views import AlertTemplateViewSet

router = DefaultRouter()
router.register(r"settings/plugins", PluginConfigViewSet, basename="plugin-config")
router.register(r"settings/roles", RoleViewSet, basename="role")
router.register(r"settings/alerts/templates", AlertTemplateViewSet, basename="alert-template")

urlpatterns = [
    path("public/branding", PublicBrandingView.as_view(), name="public-branding"),
    path("settings/system", SystemSettingsView.as_view(), name="system-settings"),
    path("settings/permissions/catalog", PermissionCatalogView.as_view(), name="permission-catalog"),
    path("settings/users", UserRoleListView.as_view(), name="user-roles"),
    path("settings/users/<uuid:user_id>", UserDeleteView.as_view(), name="user-delete"),
    path("settings/users/<uuid:user_id>/roles", UserRoleUpdateView.as_view(), name="user-role-update"),
    path("settings/users/sync-ldap", LDAPSyncView.as_view(), name="ldap-sync"),
    path("settings/alerts/channels", AlertChannelListView.as_view(), name="alert-channel-list"),
    path(
        "settings/alerts/channels/<str:channel_type>",
        AlertChannelUpdateView.as_view(),
        name="alert-channel-update",
    ),
    path(
        "settings/alerts/channels/<str:channel_type>/test",
        AlertChannelTestView.as_view(),
        name="alert-channel-test",
    ),
    path("", include(router.urls)),
]
