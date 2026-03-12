from apps.core.middleware.audit_middleware import sanitize_metadata
from apps.monitoring import logging as monitoring_logging
from apps.tools import logging as tools_logging


def test_logging_schema_definitions_exist():
    assert monitoring_logging.LOGGING_SCHEMAS
    assert tools_logging.LOGGING_SCHEMAS
    assert any("tool.execution" == schema["event"] for schema in tools_logging.LOGGING_SCHEMAS)


def test_sanitize_metadata_masks_sensitive_fields():
    payload = {
        "token": "abcd",
        "nested": {"password": "secret"},
        "safe": "value",
    }
    result = sanitize_metadata(payload)
    assert result["token"] == "***"
    assert result["nested"]["password"] == "***"
    assert result["safe"] == "value"
