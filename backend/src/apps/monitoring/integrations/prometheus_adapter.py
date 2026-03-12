from __future__ import annotations

from typing import Any, Dict


def query_prometheus(query: str) -> Dict[str, Any]:
    return {"data": {"result": []}}


def fetch_metrics(query: str) -> Dict[str, Any]:
    return query_prometheus(query)
