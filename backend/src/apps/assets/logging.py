"""Structured logging field definitions for assets module."""

ASSET_SYNC_SCHEMA = {
    "event": "asset.sync",
    "fields": [
        "source",
        "total_records",
        "duration_ms",
        "status",
    ],
}

ASSET_CONFLICT_SCHEMA = {
    "event": "asset.conflict",
    "fields": [
        "source",
        "external_id",
        "anchor_id",
        "duplicate_ids",
    ],
}

LOGGING_SCHEMAS = [ASSET_SYNC_SCHEMA, ASSET_CONFLICT_SCHEMA]
