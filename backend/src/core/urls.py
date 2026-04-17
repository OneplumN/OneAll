from django.contrib import admin
from django.urls import include, path

from apps.core.api.audit_log_view import AuditLogListView
from apps.core.api.auth_views import ChangePasswordView, LoginView, MeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login", LoginView.as_view(), name="auth-login"),
    path("api/auth/me", MeView.as_view(), name="auth-me"),
    path("api/auth/profile", MeView.as_view(), name="auth-profile"),
    path("api/auth/change-password", ChangePasswordView.as_view(), name="auth-change-password"),
    path("api/audit/logs", AuditLogListView.as_view(), name="audit-log-list"),
    path("api/", include("apps.probes.api.urls")),
    path("api/", include("apps.dashboard.api.urls")),
    path("api/", include("apps.settings.api.urls")),
    path("api/", include("apps.monitoring.api.urls")),
    path("api/", include("apps.assets.api.urls")),
    path("api/", include("apps.tools.api.urls")),
    path("api/", include("apps.alerts.api.urls")),
]
