from __future__ import annotations

from celery.schedules import crontab
from kombu import Queue

TASK_QUEUE_NAMES = (
    "celery",
    "monitoring",
    "probes",
    "analytics",
    "settings",
    "assets",
)

CELERY_TASK_ROUTES = {
    "apps.monitoring.tasks.*": {"queue": "monitoring"},
    "apps.probes.tasks.*": {"queue": "probes"},
    "apps.analytics.tasks.*": {"queue": "analytics"},
    "apps.settings.tasks.*": {"queue": "settings"},
    "apps.assets.tasks.*": {"queue": "assets"},
}

CELERY_BEAT_SCHEDULE = {
    "monitoring-overview-refresh": {
        "task": "apps.dashboard.tasks.overview_refresh.refresh_metrics",
        "schedule": crontab(minute="*/5"),
    },
    "zabbix-dashboard-refresh": {
        "task": "apps.monitoring.tasks.zabbix_dashboard_refresh.refresh_snapshot",
        "schedule": 30.0,
        "options": {"queue": "monitoring"},
    },
    "plugin-health-check": {
        "task": "apps.settings.tasks.plugin_health_check",
        "schedule": crontab(minute="0", hour="*/1"),
    },
    "asset-sync": {
        "task": "apps.assets.tasks.sync_assets",
        "schedule": crontab(minute="0", hour="2"),
    },
}

CELERY_IMPORTS = (
    "apps.monitoring.tasks.execute_detection",
    "apps.monitoring.tasks.zabbix_dashboard_refresh",
    "apps.probes.tasks.health_checks",
    "apps.analytics.tasks.report_export_task",
    "apps.settings.tasks.plugin_health_check",
    "apps.assets.tasks.asset_sync_task",
)

CELERY_TASK_QUEUES = tuple(Queue(name, routing_key=name) for name in TASK_QUEUE_NAMES)
CELERY_TASK_DEFAULT_QUEUE = "celery"
CELERY_TASK_CREATE_MISSING_QUEUES = True
