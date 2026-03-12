from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {"password", "secret", "token", "access_key", "secret_key", "credential"}


def _mask(value: Any) -> Any:
    if isinstance(value, str):
        return "***"
    if isinstance(value, (list, tuple)):
        return ["***" for _ in value]
    if isinstance(value, dict):
        return {key: "***" for key in value.keys()}
    return "***"


def sanitize_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}

    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        if key.lower() in SENSITIVE_KEYS:
            sanitized[key] = _mask(value)
        elif isinstance(value, Mapping):
            sanitized[key] = sanitize_metadata(value)
        else:
            sanitized[key] = value
    return sanitized
