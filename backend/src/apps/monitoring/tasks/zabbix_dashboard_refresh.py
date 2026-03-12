from __future__ import annotations

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

from apps.monitoring.services import zabbix_service
from apps.monitoring.services.zabbix_service import (
    ZabbixServiceError,
    fetch_dashboard_snapshot,
    get_cached_snapshot,
    is_snapshot_fresh,
    resolve_refresh_interval_seconds,
    store_snapshot,
    SNAPSHOT_LOCK_KEY,
)


@shared_task(name="apps.monitoring.tasks.zabbix_dashboard_refresh.refresh_snapshot")
def refresh_zabbix_dashboard_snapshot(force: bool = False):
    interval = resolve_refresh_interval_seconds()
    cached = get_cached_snapshot()
    if not force and cached and is_snapshot_fresh(cached, interval):
        return cached
    lock_acquired = cache.add(SNAPSHOT_LOCK_KEY, timezone.now().isoformat(), timeout=30)
    if not lock_acquired and not force:
        return cached
    try:
        snapshot = fetch_dashboard_snapshot()
        stored = store_snapshot(snapshot)
        return stored
    except ZabbixServiceError:
        zabbix_service.logger.exception("Failed to refresh Zabbix dashboard snapshot")
        return cached
    finally:
        if lock_acquired:
            cache.delete(SNAPSHOT_LOCK_KEY)
