from __future__ import annotations

from django.db import transaction

from apps.settings.models import SystemSettings

DEFAULT_NOTIFICATION_CHANNELS = {
    "email": "ops@example.com",
    "webhook": "",
}


def get_system_settings() -> SystemSettings:
    settings = SystemSettings.objects.first()
    if settings:
        return settings

    with transaction.atomic():
        settings = SystemSettings.objects.first()
        if settings:
            return settings
        return SystemSettings.objects.create(
            notification_channels=DEFAULT_NOTIFICATION_CHANNELS
        )


def get_integration_settings(section: str) -> dict:
    settings = get_system_settings()
    integrations = settings.integrations or {}
    return dict(integrations.get(section) or {})


def update_integration_settings(section: str, payload: dict) -> dict:
    settings = get_system_settings()
    integrations = dict(settings.integrations or {})
    current_section = dict(integrations.get(section) or {})
    current_section.update(payload or {})
    integrations[section] = current_section
    settings.integrations = integrations
    settings.save(update_fields=["integrations", "updated_at"])
    return dict(current_section)
