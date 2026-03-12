from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

JsonDict = Dict[str, Any]


class ZabbixConfigurationError(RuntimeError):
    """Raised when Zabbix credential configuration is missing."""


class ZabbixAPIError(RuntimeError):
    """Raised when Zabbix API returns an error or cannot be reached."""


@dataclass
class ZabbixClient:
    base_url: str
    token: str
    timeout: int = 10
    verify: bool = True

    def __post_init__(self) -> None:
        if not self.base_url:
            raise ZabbixConfigurationError("ZABBIX_API_URL is not configured.")
        if not self.token:
            raise ZabbixConfigurationError("ZABBIX_API_TOKEN is not configured.")
        self.base_url = self.base_url.rstrip("/")
        self._request_id = 1
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json-rpc"})

    def _request(self, method: str, params: Optional[JsonDict] = None, *, use_auth: bool = True) -> JsonDict:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._request_id,
            "auth": self.token if use_auth else None,
        }
        self._request_id += 1
        try:
            response = self._session.post(
                self.base_url,
                data=json.dumps(payload),
                timeout=self.timeout,
                verify=self.verify,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Failed to call Zabbix API %s", method)
            raise ZabbixAPIError(f"Zabbix API request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ZabbixAPIError("Cannot decode Zabbix response as JSON") from exc

        if "error" in data:
            error = data["error"]
            message = error.get("data") or error.get("message") or "unknown"
            raise ZabbixAPIError(f"Zabbix API error: {message}")

        return data.get("result", {})

    def api_info(self) -> str:
        result = self._request("apiinfo.version", use_auth=False)
        return str(result)

    def get_queue_stats(self) -> List[JsonDict]:
        result = self._request("queue.get", {})
        return result if isinstance(result, list) else []

    def get_problems(self, limit: int = 10) -> List[JsonDict]:
        params: JsonDict = {
            "output": ["eventid", "name", "severity", "clock"],
            "selectAcknowledges": "extend",
            "selectTags": "extend",
            "sortfield": "eventid",
            "sortorder": "DESC",
            "recent": True,
            "limit": limit,
        }
        result = self._request("problem.get", params)
        return result if isinstance(result, list) else []

    def get_hosts(self) -> List[JsonDict]:
        params: JsonDict = {
            "output": ["hostid", "host", "status", "available", "description", "maintenanceid", "maintenance_status"],
            "selectGroups": ["name"],
            "selectInterfaces": ["ip", "available"],
        }
        result = self._request("host.get", params)
        return result if isinstance(result, list) else []

    def get_proxies(self) -> List[JsonDict]:
        params: JsonDict = {
            "output": ["proxyid", "name", "lastaccess", "state"],
        }
        result = self._request("proxy.get", params)
        return result if isinstance(result, list) else []

    def get_users(self) -> List[JsonDict]:
        params: JsonDict = {
            "output": ["userid", "alias", "name", "lastaccess"],
        }
        result = self._request("user.get", params)
        return result if isinstance(result, list) else []

    def count_triggers(self, filter_params: Optional[JsonDict] = None) -> int:
        params: JsonDict = {"countOutput": True}
        if filter_params:
            params["filter"] = filter_params
        result = self._request("trigger.get", params)
        try:
            return int(result)
        except (TypeError, ValueError):
            return 0

    def get_ha_nodes(self) -> List[JsonDict]:
        result = self._request("ha.get", {})
        return result if isinstance(result, list) else []


def get_client() -> ZabbixClient:
    return ZabbixClient(
        base_url=getattr(settings, "ZABBIX_API_URL", ""),
        token=getattr(settings, "ZABBIX_API_TOKEN", ""),
        timeout=int(getattr(settings, "ZABBIX_API_TIMEOUT", 10)),
        verify=bool(getattr(settings, "ZABBIX_VERIFY_TLS", True)),
    )
