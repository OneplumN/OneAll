from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

SECRET_MASK = "******"
DEFAULT_SENSITIVE_KEY_TOKENS = (
    "password",
    "secret",
    "token",
    "authorization",
    "cookie",
    "webhook",
)


def is_sensitive_config_key(key: str, *, extra_keys: Iterable[str] = ()) -> bool:
    normalized = str(key or "").strip().lower()
    if not normalized:
        return False

    normalized_extra_keys = {str(item or "").strip().lower() for item in extra_keys if str(item or "").strip()}
    if normalized in normalized_extra_keys:
        return True

    return any(token in normalized for token in DEFAULT_SENSITIVE_KEY_TOKENS)


def mask_sensitive_config(
    config: Mapping[str, Any] | None,
    *,
    extra_keys: Iterable[str] = (),
) -> dict[str, Any]:
    masked = dict(config or {})
    for key, value in list(masked.items()):
        if is_sensitive_config_key(str(key), extra_keys=extra_keys) and value not in (None, "", [], {}, ()):
            masked[str(key)] = SECRET_MASK
    return masked


def merge_sensitive_config(
    current: Mapping[str, Any] | None,
    incoming: Mapping[str, Any] | None,
    *,
    extra_keys: Iterable[str] = (),
) -> dict[str, Any]:
    merged = dict(current or {})
    for key, value in dict(incoming or {}).items():
        key_str = str(key)
        if is_sensitive_config_key(key_str, extra_keys=extra_keys) and value == SECRET_MASK:
            continue
        merged[key_str] = value
    return merged
