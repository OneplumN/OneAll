from __future__ import annotations

import environ

from core.settings.env_loader import load_env

env = environ.Env(
    TIMESCALE_HOST=(str, "localhost"),
    TIMESCALE_PORT=(int, 5432),
    TIMESCALE_DB=(str, "oneall_metrics"),
    TIMESCALE_USER=(str, "postgres"),
    TIMESCALE_PASSWORD=(str, "postgres"),
)

load_env()

TIMESCALE_DATABASE = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": env("TIMESCALE_DB"),
    "USER": env("TIMESCALE_USER"),
    "PASSWORD": env("TIMESCALE_PASSWORD"),
    "HOST": env("TIMESCALE_HOST"),
    "PORT": env("TIMESCALE_PORT"),
    "OPTIONS": {
        "options": "-c search_path=public",
    },
}

HYPERTABLE_BOOTSTRAP_SQL = """
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS probe_runtime_metrics (
    id BIGSERIAL NOT NULL,
    probe_id UUID NOT NULL,
    node_name TEXT NOT NULL,
    uptime_seconds BIGINT NOT NULL,
    heartbeats_sent BIGINT NOT NULL,
    heartbeats_failed BIGINT NOT NULL,
    heartbeats_last_success TIMESTAMPTZ NULL,
    tasks_fetched BIGINT NOT NULL,
    tasks_executed BIGINT NOT NULL,
    tasks_failed BIGINT NOT NULL,
    queue_depth BIGINT NOT NULL,
    queue_capacity BIGINT NOT NULL,
    active_workers BIGINT NOT NULL,
    metrics_generated_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, recorded_at)
);

SELECT create_hypertable('probe_runtime_metrics', 'recorded_at', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS probe_detection_results (
    detection_id UUID NOT NULL,
    probe_id UUID NULL,
    protocol VARCHAR(32) NOT NULL,
    target TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    response_time_ms INTEGER NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (detection_id, recorded_at)
);

SELECT create_hypertable('probe_detection_results', 'recorded_at', if_not_exists => TRUE);
"""
