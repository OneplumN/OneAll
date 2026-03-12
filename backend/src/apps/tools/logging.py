"""Structured logging field definitions for tools module."""

TOOL_EXECUTION_SCHEMA = {
    "event": "tool.execution",
    "fields": [
        "tool_id",
        "tool_name",
        "run_id",
        "status",
        "parameters_keys",
        "duration_ms",
    ],
}

REPOSITORY_SCHEMA = {
    "event": "tool.repository",
    "fields": [
        "tool_id",
        "version",
        "operation",
        "checksum",
    ],
}

LOGGING_SCHEMAS = [TOOL_EXECUTION_SCHEMA, REPOSITORY_SCHEMA]
