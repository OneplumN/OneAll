from __future__ import annotations

from django.conf import settings


def test_celery_routes_have_configured_queues():
    queue_names = {queue.name for queue in settings.CELERY_TASK_QUEUES}
    assert queue_names, "Celery queues should be configured"

    routed_queues = {route.get("queue") for route in settings.CELERY_TASK_ROUTES.values() if route.get("queue")}
    assert routed_queues.issubset(queue_names)

    assert settings.CELERY_TASK_DEFAULT_QUEUE in queue_names
    assert settings.CELERY_TASK_CREATE_MISSING_QUEUES is True
