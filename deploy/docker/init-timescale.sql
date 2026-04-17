-- TimescaleDB 初始化脚本
-- 此脚本在容器首次启动时自动执行

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 探针运行时指标表
CREATE TABLE IF NOT EXISTS probe_runtime_metrics (
    id BIGSERIAL NOT NULL,
    probe_id UUID NOT NULL,
    node_name TEXT NOT NULL,
    uptime_seconds BIGINT NOT NULL,
    cpu_usage DOUBLE PRECISION NULL,
    memory_usage_mb DOUBLE PRECISION NULL,
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

-- 拨测结果表
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

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_runtime_metrics_probe_id ON probe_runtime_metrics (probe_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_detection_results_probe_id ON probe_detection_results (probe_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_detection_results_status ON probe_detection_results (status, recorded_at DESC);
