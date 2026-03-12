"""Structured logging field definitions for monitoring module."""

DETECTION_LOG_SCHEMA = {
    "event": "detection.execute",
    "fields": [
        "task_id",
        "target",
        "protocol",
        "probe_id",
        "status",
        "response_time_ms",
    ],
}

ITSM_LOG_SCHEMA = {
    "event": "itsm.callback",
    "fields": [
        "request_id",
        "itsm_ticket_id",
        "status",
        "latency_seconds",
    ],
}

LOGGING_SCHEMAS = [DETECTION_LOG_SCHEMA, ITSM_LOG_SCHEMA]
