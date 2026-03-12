from __future__ import annotations

from celery import shared_task


@shared_task(name="apps.probes.tasks.health_checks.ping")
def ping() -> str:
    return "pong"
