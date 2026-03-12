from __future__ import annotations

import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone as django_timezone

from apps.monitoring.integrations.zabbix_adapter import (
    ZabbixAPIError,
    ZabbixClient,
    ZabbixConfigurationError,
    get_client,
)
from apps.settings.models import SystemSettings, ZABBIX_REFRESH_INTERVALS

logger = logging.getLogger(__name__)

SNAPSHOT_CACHE_KEY = "monitoring:zabbix:dashboard"
SNAPSHOT_LOCK_KEY = "monitoring:zabbix:dashboard:lock"
DASHBOARD_CACHE_KEY = "monitoring:zabbix:sync-history"
HISTORY_TTL_SECONDS = 6 * 60 * 60
HISTORY_LIMIT = 5
HOST_CACHE_KEY = "monitoring:zabbix:hosts"
ALERT_CACHE_KEY = "monitoring:zabbix:alerts"
SYSTEM_CACHE_KEY = "monitoring:zabbix:system"
DEFAULT_REFRESH_SECONDS = 60

SEVERITY_LABELS = {
    0: "Not classified",
    1: "Information",
    2: "Warning",
    3: "Average",
    4: "High",
    5: "Disaster",
}


class ZabbixServiceError(RuntimeError):
    """Raised when dashboard aggregation fails."""


def _human_duration(delta: timedelta) -> str:
    seconds = max(int(delta.total_seconds()), 0)
    if seconds < 60:
        return f"{seconds}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {sec:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def _severity_label(raw: Any) -> str:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return "Unknown"
    return SEVERITY_LABELS.get(value, "Unknown")


def _problem_started(problem: Dict[str, Any]) -> datetime | None:
    try:
        clock = int(problem.get("clock", 0))
    except (TypeError, ValueError):
        return None
    if not clock:
        return None
    return datetime.fromtimestamp(clock, tz=timezone.utc)


def _format_alert(problem: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    started = _problem_started(problem) or now
    duration = _human_duration(now - started)
    hosts = problem.get("hosts") or []
    host_name = hosts[0].get("host") if hosts else ""
    return {
        "id": problem.get("eventid") or problem.get("id"),
        "severity": _severity_label(problem.get("severity")),
        "host": host_name or "--",
        "message": problem.get("name") or "未命名告警",
        "duration": duration,
        "started_at": started.isoformat(),
    }


def _categorize_hosts(hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
    healthy = offline = unknown = disabled = maintenance = 0
    for host in hosts:
        status = str(host.get("status", ""))
        maintenance_status = str(host.get("maintenance_status", "0"))
        if status == "1":
            disabled += 1
            continue
        if maintenance_status == "1" or str(host.get("maintenanceid", "0")) not in {"0", "", None}:
            maintenance += 1
            continue
        availability = _resolve_host_availability(host)
        if availability == "1":
            healthy += 1
        elif availability == "2":
            offline += 1
        else:
            unknown += 1
    total = len(hosts)
    return {
        "total": total,
        "breakdown": {
            "healthy": healthy,
            "offline": offline,
            "unknown": unknown,
            "maintenance": maintenance,
            "disabled": disabled,
        },
        "items": [
            {
                "label": "运行中",
                "description": "Agent 可用且处于监控状态",
                "value": healthy,
                "status": "ok",
            },
            {
                "label": "状态未知",
                "description": "Agent 状态未知或未上报",
                "value": unknown,
                "status": "warn",
            },
            {
                "label": "不可达",
                "description": "Agent 不可用或连接失败",
                "value": offline,
                "status": "danger",
            },
            {
                "label": "禁用 / 维护",
                "description": "Zabbix 中被禁用或处于维护窗口",
                "value": disabled + maintenance,
                "status": "warn",
            },
        ],
    }


def _resolve_host_availability(host: Dict[str, Any]) -> str:
    availability = host.get("available")
    if availability is not None:
        return str(availability)
    interfaces = host.get("interfaces") or []
    for interface in interfaces:
        if "available" in interface:
            return str(interface.get("available"))
    return "0"


def _record_history_entry(host_count: int, alert_count: int, duration_ms: float, source: str) -> List[Dict[str, Any]]:
    timestamp = django_timezone.localtime()
    entry = {
        "time": timestamp.strftime("%Y-%m-%d %H:%M"),
        "scope": source,
        "duration": f"{int(duration_ms)} ms",
        "result": "成功",
        "message": f"主机 {host_count} · 告警 {alert_count}",
    }
    history: List[Dict[str, Any]] = cache.get(DASHBOARD_CACHE_KEY, [])
    updated = [entry, *history][:HISTORY_LIMIT]
    cache.set(DASHBOARD_CACHE_KEY, updated, HISTORY_TTL_SECONDS)
    return updated


def _get_history() -> List[Dict[str, Any]]:
    history = cache.get(DASHBOARD_CACHE_KEY, [])
    if isinstance(history, list):
        return history
    return []


def _safe_client() -> ZabbixClient:
    try:
        return get_client()
    except ZabbixConfigurationError as exc:
        raise ZabbixServiceError(str(exc)) from exc


def resolve_refresh_interval_seconds() -> int:
    settings_obj = SystemSettings.objects.order_by("-updated_at").first()
    value = getattr(settings_obj, "zabbix_dashboard_refresh_seconds", DEFAULT_REFRESH_SECONDS)
    if value not in ZABBIX_REFRESH_INTERVALS:
        return DEFAULT_REFRESH_SECONDS
    return value


def refresh_alerts_snapshot() -> Dict[str, Any]:
    client = _safe_client()
    now = datetime.now(timezone.utc)
    try:
        problems = client.get_problems(limit=10)
    except ZabbixAPIError as exc:
        raise ZabbixServiceError(str(exc)) from exc
    alerts = [_format_alert(problem, now) for problem in problems]
    severity_breakdown = _build_severity_breakdown(alerts)
    problem_hosts = {
        host["hostid"]
        for problem in problems
        for host in problem.get("hosts", [])
        if host.get("hostid")
    }
    payload = {
        "alerts": alerts,
        "severity_breakdown": severity_breakdown,
        "problem_host_count": len(problem_hosts),
        "avg_problem_age_seconds": _average_problem_age(alerts, now),
        "refreshed_at": django_timezone.now().isoformat(),
    }
    cache.set(ALERT_CACHE_KEY, payload, None)
    return payload


def refresh_host_snapshot(alert_count: int) -> Dict[str, Any]:
    client = _safe_client()
    start = time.perf_counter()
    try:
        hosts = client.get_hosts()
    except ZabbixAPIError as exc:
        raise ZabbixServiceError(str(exc)) from exc
    duration_ms = (time.perf_counter() - start) * 1000
    host_summary = _categorize_hosts(hosts)
    history = _record_history_entry(host_summary["total"], alert_count, duration_ms, "host.get")
    payload = {
        "host_overview": host_summary,
        "sync_history": history,
        "refreshed_at": django_timezone.now().isoformat(),
    }
    cache.set(HOST_CACHE_KEY, payload, None)
    return payload


def refresh_system_snapshot() -> Dict[str, Any]:
    client = _safe_client()
    server_version = _safe_fetch(client.api_info, "")
    proxies = _safe_fetch(lambda: client.get_proxies(), [])
    users = _safe_fetch(lambda: client.get_users(), [])
    ha_nodes = _safe_fetch(lambda: client.get_ha_nodes(), [], silence=True)
    trigger_stats = _collect_trigger_stats(client)
    proxy_stats = _collect_proxy_stats(proxies)
    user_stats = {"total": len(users)}
    payload = {
        "proxy_stats": proxy_stats,
        "trigger_stats": trigger_stats,
        "user_stats": user_stats,
        "server_version": server_version,
        "ha_nodes": ha_nodes,
        "refreshed_at": django_timezone.now().isoformat(),
    }
    cache.set(SYSTEM_CACHE_KEY, payload, None)
    return payload


def get_alerts_snapshot() -> Dict[str, Any] | None:
    payload = cache.get(ALERT_CACHE_KEY)
    if isinstance(payload, dict):
        return payload
    return None


def get_host_snapshot() -> Dict[str, Any] | None:
    payload = cache.get(HOST_CACHE_KEY)
    if isinstance(payload, dict):
        return payload
    return None


def get_system_snapshot() -> Dict[str, Any] | None:
    payload = cache.get(SYSTEM_CACHE_KEY)
    if isinstance(payload, dict):
        return payload
    return None


def needs_refresh(payload: Dict[str, Any] | None, interval_seconds: int) -> bool:
    if not payload:
        return True
    refreshed_at = payload.get("refreshed_at")
    if not refreshed_at:
        return True
    try:
        refreshed_dt = datetime.fromisoformat(refreshed_at)
    except ValueError:
        return True
    return (django_timezone.now() - refreshed_dt).total_seconds() >= interval_seconds


def assemble_dashboard_payload(
    host_snapshot: Dict[str, Any],
    alert_snapshot: Dict[str, Any],
    system_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    host_overview = host_snapshot.get("host_overview") or {"total": 0, "breakdown": {}, "items": []}
    alerts = alert_snapshot.get("alerts") or []
    severity_breakdown = alert_snapshot.get("severity_breakdown") or {}
    proxy_stats = system_snapshot.get("proxy_stats") or {"total": 0, "online": 0, "offline": 0}
    trigger_stats = system_snapshot.get("trigger_stats") or {"total": 0, "disabled": 0, "enabled": 0, "problem": 0}
    user_stats = system_snapshot.get("user_stats") or {"total": 0}
    server_version = system_snapshot.get("server_version") or ""
    ha_nodes = system_snapshot.get("ha_nodes") or []
    host_breakdown = host_overview.get("breakdown", {})
    host_items = host_overview.get("items", [])

    def _coerce_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _item_value(label: str) -> int:
        for entry in host_items:
            if entry.get("label") == label:
                return _coerce_int(entry.get("value"))
        return 0

    def _resolve_host_metric(key: str, fallback_label: str | None = None) -> int:
        value = host_breakdown.get(key)
        if value is not None:
            return _coerce_int(value)
        if fallback_label:
            return _item_value(fallback_label)
        return 0

    system_info = _build_system_info(
        host_breakdown,
        trigger_stats,
        user_stats,
        server_version,
        _resolve_ha_status(ha_nodes),
    )

    metrics = {
        "total_hosts": host_overview.get("total", 0),
        "problem_hosts": alert_snapshot.get("problem_host_count", 0),
        "open_problems": len(alerts),
        "avg_problem_age_seconds": alert_snapshot.get("avg_problem_age_seconds", 0.0),
        "available_hosts": _resolve_host_metric("healthy", "运行中"),
        "unavailable_hosts": _resolve_host_metric("offline", "不可达"),
        "maintenance_hosts": _resolve_host_metric("maintenance", "禁用 / 维护"),
    }

    refreshed_at = max(
        [
            host_snapshot.get("refreshed_at"),
            alert_snapshot.get("refreshed_at"),
            system_snapshot.get("refreshed_at"),
        ],
        default=None,
    )

    return {
        "metrics": metrics,
        "alerts": alerts,
        "host_overview": host_overview,
        "sync_history": host_snapshot.get("sync_history") or _get_history(),
        "proxy_stats": proxy_stats,
        "severity_breakdown": severity_breakdown,
        "system_info": system_info,
        "refreshed_at": refreshed_at,
    }


def fetch_dashboard_snapshot(*, record_history: bool = False, force_refresh: bool = False) -> Dict[str, Any]:
    interval = resolve_refresh_interval_seconds()
    alert_snapshot = get_alerts_snapshot()
    if force_refresh or record_history or needs_refresh(alert_snapshot, interval):
        alert_snapshot = refresh_alerts_snapshot()
    if alert_snapshot is None:
        alert_snapshot = refresh_alerts_snapshot()

    system_snapshot = get_system_snapshot()
    if force_refresh or record_history or needs_refresh(system_snapshot, interval):
        system_snapshot = refresh_system_snapshot()
    if system_snapshot is None:
        system_snapshot = refresh_system_snapshot()

    host_snapshot = get_host_snapshot()
    alert_count = len(alert_snapshot.get("alerts") or [])
    if force_refresh or record_history or needs_refresh(host_snapshot, interval):
        host_snapshot = refresh_host_snapshot(alert_count)
    if host_snapshot is None:
        host_snapshot = refresh_host_snapshot(alert_count)

    return assemble_dashboard_payload(host_snapshot, alert_snapshot, system_snapshot)


def get_cached_snapshot() -> Dict[str, Any] | None:
    payload = cache.get(SNAPSHOT_CACHE_KEY)
    if isinstance(payload, dict) and isinstance(payload.get("snapshot"), dict):
        return payload
    return None


def store_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "snapshot": snapshot,
        "refreshed_at": django_timezone.now().isoformat(),
    }
    cache.set(SNAPSHOT_CACHE_KEY, payload, None)
    return payload


def is_snapshot_fresh(payload: Dict[str, Any] | None, interval_seconds: int) -> bool:
    if not payload:
        return False
    refreshed_at = payload.get("refreshed_at")
    if not refreshed_at:
        return False
    try:
        refreshed_dt = datetime.fromisoformat(refreshed_at)
    except ValueError:
        return False
    return (django_timezone.now() - refreshed_dt).total_seconds() < interval_seconds


def _average_problem_age(alerts: List[Dict[str, Any]], now: datetime) -> float:
    if not alerts:
        return 0.0
    total_seconds = 0.0
    for alert in alerts:
        started = alert.get("started_at")
        if not started:
            continue
        try:
            started_dt = datetime.fromisoformat(started)
        except ValueError:
            continue
        total_seconds += max((now - started_dt).total_seconds(), 0.0)
    divisor = max(len(alerts), 1)
    return round(total_seconds / divisor, 2)


def _collect_trigger_stats(client: ZabbixClient) -> Dict[str, int]:
    try:
        total = client.count_triggers()
        disabled = client.count_triggers({"status": 1})
        problem = client.count_triggers({"value": 1})
    except ZabbixAPIError:
        logger.exception("Failed to fetch trigger statistics from Zabbix")
        return {"total": 0, "disabled": 0, "problem": 0}
    enabled = max(total - disabled, 0)
    return {"total": total, "disabled": disabled, "enabled": enabled, "problem": problem}


def _collect_proxy_stats(raw_proxies: List[Dict[str, Any]]) -> Dict[str, int]:
    total = len(raw_proxies)
    now_ts = int(time.time())
    threshold = now_ts - 300
    online = 0
    for proxy in raw_proxies:
        try:
            last_access = int(proxy.get("lastaccess") or 0)
        except (TypeError, ValueError):
            last_access = 0
        if last_access and last_access >= threshold:
            online += 1
    offline = max(total - online, 0)
    return {"total": total, "online": online, "offline": offline}


def _collect_user_stats(raw_users: List[Dict[str, Any]]) -> Dict[str, int]:
    total = len(raw_users)
    now_ts = int(time.time())
    threshold = now_ts - 300
    online = 0
    for user in raw_users:
        try:
            last_access = int(user.get("lastaccess") or 0)
        except (TypeError, ValueError):
            last_access = 0
        if last_access and last_access >= threshold:
            online += 1
    return {"total": total, "online": online}


def _build_system_info(
    host_breakdown: Dict[str, int],
    trigger_stats: Dict[str, int],
    user_stats: Dict[str, int],
    server_version: str,
    ha_status: str,
) -> Dict[str, Any]:
    enabled_hosts = (
        host_breakdown.get("healthy", 0)
        + host_breakdown.get("unknown", 0)
        + host_breakdown.get("offline", 0)
        + host_breakdown.get("maintenance", 0)
    )
    disabled_hosts = host_breakdown.get("disabled", 0)
    server_address = getattr(settings, "ZABBIX_API_URL", "")
    checked_at = django_timezone.localtime().isoformat()
    return {
        "is_running": bool(server_version),
        "server_address": server_address,
        "server_version": server_version or "未知",
        "frontend_version": server_version or "未知",
        "update_checked_at": checked_at,
        "latest_release": server_version or "未知",
        "latest_release_notes": "",
        "hosts_enabled": enabled_hosts,
        "hosts_disabled": disabled_hosts,
        "triggers_total": trigger_stats.get("total", 0),
        "triggers_problem": trigger_stats.get("problem", 0),
        "users_total": user_stats.get("total", 0),
        "users_online": user_stats.get("online", 0),
        "ha_status": ha_status,
    }


def _build_severity_breakdown(alerts: List[Dict[str, Any]]) -> Dict[str, int]:
    mapping = {
        "disaster": 0,
        "high": 0,
        "average": 0,
        "warning": 0,
        "information": 0,
    }
    for alert in alerts:
        severity = str(alert.get("severity", "")).lower()
        if severity in mapping:
            mapping[severity] += 1
    return mapping


def _resolve_ha_status(ha_nodes: List[Dict[str, Any]]) -> str:
    if not ha_nodes:
        return "disabled"
    for node in ha_nodes:
        state = node.get("status") or node.get("state")
        if str(state).lower() in {"active", "primary"}:
            return "active"
    return "standby"


def _safe_fetch(func, default, silence: bool = False):
    try:
        return func()
    except ZabbixAPIError:
        log_func = logger.debug if silence else logger.exception
        log_func("Zabbix API call failed for %s", getattr(func, "__name__", "unknown"))
        return default


def test_connectivity() -> Dict[str, Any]:
    client = _safe_client()
    try:
        version = client.api_info()
    except ZabbixAPIError as exc:
        raise ZabbixServiceError(str(exc)) from exc
    return {"version": version}


def trigger_manual_sync() -> Dict[str, Any]:
    snapshot = fetch_dashboard_snapshot(record_history=True, force_refresh=True)
    payload = store_snapshot(snapshot)
    return {
        "status": "ok",
        "history": snapshot["sync_history"],
        "metrics": snapshot["metrics"],
        "refreshed_at": payload.get("refreshed_at"),
    }
