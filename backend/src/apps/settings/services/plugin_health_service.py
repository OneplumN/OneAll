from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import logging

import requests

from apps.core.outbound import UnsafeOutboundURLError, validate_outbound_hook_url
from apps.settings.models import PluginConfig


logger = logging.getLogger(__name__)

def run_health_check_for_plugin(plugin: PluginConfig) -> Dict[str, Any]:
    # Placeholder logic; real implementation would probe external services.
    return {"status": "healthy", "message": "OK"}


def _dispatch_failure_webhook(plugin: PluginConfig, payload: Dict[str, Any]) -> None:
    webhook_url = (plugin.config or {}).get("webhook")
    if not webhook_url:
        return

    try:
        validate_outbound_hook_url(str(webhook_url), resolve_dns=True)
        requests.post(webhook_url, json=payload, timeout=5)
    except UnsafeOutboundURLError as exc:
        logger.warning("Skipped unsafe plugin failure webhook: %s", exc)
    except requests.RequestException as exc:  # pragma: no cover - network failures
        logger.warning("Failed to send plugin failure webhook: %s", exc)


def evaluate_plugin_health() -> None:
    for plugin in PluginConfig.objects.filter(enabled=True):
        result = run_health_check_for_plugin(plugin)
        plugin.status = result.get("status", "unknown")
        plugin.last_message = result.get("message", "")
        plugin.last_checked_at = datetime.now(timezone.utc)
        plugin.save(update_fields=["status", "last_message", "last_checked_at", "updated_at"])

        if plugin.status not in {"healthy", "ok"}:
            _dispatch_failure_webhook(
                plugin,
                {
                    "plugin": plugin.name,
                    "status": plugin.status,
                    "message": plugin.last_message,
                    "checked_at": plugin.last_checked_at.isoformat(),
                },
            )
