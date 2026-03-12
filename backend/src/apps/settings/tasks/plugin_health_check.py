from __future__ import annotations

from celery import shared_task

from apps.settings.services import plugin_health_service


@shared_task(name="apps.settings.tasks.plugin_health_check")
def plugin_health_check() -> None:
    plugin_health_service.evaluate_plugin_health()
