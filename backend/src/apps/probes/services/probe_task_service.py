from __future__ import annotations

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_EXPECT_STATUS = 200


def timeout_from_metadata(metadata: dict | None) -> int:
    payload = _extract_payload(metadata)
    return _coerce_positive_int(payload.get("timeout_seconds"), default=DEFAULT_TIMEOUT_SECONDS)


def expect_status_from_metadata(metadata: dict | None) -> int:
    payload = _extract_payload(metadata)
    return _coerce_status_code(payload.get("expect_status"), default=DEFAULT_EXPECT_STATUS)


def _extract_payload(metadata: dict | None) -> dict:
    if not isinstance(metadata, dict):
        return {}
    nested = metadata.get("config")
    if isinstance(nested, dict):
        merged = dict(metadata)
        merged.update(nested)
        return merged
    return metadata


def _coerce_positive_int(value, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _coerce_status_code(value, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if 100 <= parsed <= 599:
        return parsed
    return default

