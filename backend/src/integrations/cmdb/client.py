from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class CMDBClient:
    def __init__(self, base_url: str, token: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip('/')
        self.token = token

    def fetch_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/domains/{domain}"
        headers = {}
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"

        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return None


def get_client() -> CMDBClient:
    base_url = os.getenv('CMDB_BASE_URL', 'http://cmdb.example.com/api')
    token = os.getenv('CMDB_API_TOKEN')
    return CMDBClient(base_url, token)
