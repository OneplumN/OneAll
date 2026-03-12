from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class ITSMClient:
    base_url: str
    client_id: str | None = None
    token: str | None = None

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def create_ticket(self, monitoring_request) -> str:
        # Placeholder implementation – return generated ticket id without network call.
        return f"TICKET-{monitoring_request.id}"

    def update_ticket(self, ticket_id: str, payload: dict[str, Any]) -> None:
        # Placeholder stub for future real integration.
        return None


def get_client() -> ITSMClient:
    from apps.settings.services.system_settings_service import get_integration_settings

    config = get_integration_settings("itsm")
    base_url = config.get("base_url") or os.getenv("ITSM_BASE_URL", "https://itsm.example.com/api")
    client_id = config.get("client_id") or os.getenv("ITSM_CLIENT_ID")
    token = config.get("client_secret") or os.getenv("ITSM_API_TOKEN")
    return ITSMClient(base_url=base_url, client_id=client_id, token=token)
