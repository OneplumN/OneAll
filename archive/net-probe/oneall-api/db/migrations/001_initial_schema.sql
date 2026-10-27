-- OneAll target PostgreSQL schema, phase 1.
-- Runtime reference API still uses JSON-file persistence; this migration is the target contract for Go/Gin + PostgreSQL.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE oneall_users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('PlatformAdmin', 'OpsAdmin', 'OpsEngineer', 'Approver', 'Viewer')),
  department TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE asset_models (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  fields JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'active',
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT asset_models_fields_array CHECK (jsonb_typeof(fields) = 'array')
);

CREATE TABLE asset_records (
  id TEXT PRIMARY KEY,
  model_id TEXT NOT NULL REFERENCES asset_models(id),
  model_code TEXT NOT NULL,
  name TEXT,
  owner TEXT,
  environment TEXT,
  business_line TEXT,
  fields JSONB NOT NULL DEFAULT '{}'::jsonb,
  source TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT asset_records_fields_object CHECK (jsonb_typeof(fields) = 'object')
);

CREATE TABLE asset_sync_runs (
  id TEXT PRIMARY KEY,
  model_id TEXT NOT NULL REFERENCES asset_models(id),
  source TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('previewed', 'running', 'completed', 'failed')),
  preview JSONB NOT NULL DEFAULT '{}'::jsonb,
  result JSONB NOT NULL DEFAULT '{}'::jsonb,
  started_by TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ
);

CREATE TABLE monitoring_strategies (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  scope TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT true,
  version TEXT NOT NULL DEFAULT 'v1',
  rule JSONB NOT NULL,
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT monitoring_strategies_rule_object CHECK (jsonb_typeof(rule) = 'object')
);

CREATE TABLE detection_tasks (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  target TEXT NOT NULL,
  probe TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'success', 'failed', 'canceled')),
  related_asset TEXT,
  business_line TEXT,
  environment TEXT,
  protocol TEXT,
  port INTEGER,
  timeout_seconds INTEGER NOT NULL DEFAULT 10,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  result JSONB NOT NULL DEFAULT '{}'::jsonb,
  result_id TEXT,
  claimed_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  claimed_by_probe_id TEXT,
  latency_ms INTEGER,
  message TEXT,
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_detection_tasks_result_id
  ON detection_tasks(result_id)
  WHERE result_id IS NOT NULL;

CREATE TABLE alert_events (
  id TEXT PRIMARY KEY,
  severity TEXT NOT NULL,
  title TEXT NOT NULL,
  asset TEXT NOT NULL,
  owner TEXT,
  business_line TEXT,
  environment TEXT,
  status TEXT NOT NULL,
  notify_status TEXT,
  workorder_id TEXT,
  source_task_id TEXT REFERENCES detection_tasks(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

CREATE TABLE workorder_requests (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  applicant TEXT NOT NULL,
  assignee TEXT,
  status TEXT NOT NULL CHECK (status IN ('draft', 'submitted', 'rejected', 'approved', 'executing', 'completed', 'failed', 'canceled', 'withdrawn')),
  sla TEXT,
  related_object TEXT,
  related_alert_id TEXT REFERENCES alert_events(id),
  business_line TEXT,
  environment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE alert_events
  ADD CONSTRAINT alert_events_workorder_fk
  FOREIGN KEY (workorder_id) REFERENCES workorder_requests(id);

CREATE TABLE probe_nodes (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  region TEXT NOT NULL,
  capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL CHECK (status IN ('registered', 'online', 'degraded', 'offline', 'retired')),
  token_hash TEXT NOT NULL,
  heartbeat_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT probe_nodes_capabilities_array CHECK (jsonb_typeof(capabilities) = 'array')
);

CREATE TABLE notifications (
  id TEXT PRIMARY KEY,
  target TEXT NOT NULL,
  channel TEXT NOT NULL DEFAULT 'site',
  title TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'unread',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  delivered_at TIMESTAMPTZ
);

CREATE TABLE audit_logs (
  id TEXT PRIMARY KEY,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  object TEXT NOT NULL,
  result TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE event_outbox (
  event_id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  producer TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'pending',
  retry_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at TIMESTAMPTZ
);

CREATE INDEX idx_asset_records_model ON asset_records(model_id);
CREATE INDEX idx_asset_records_environment ON asset_records(environment);
CREATE INDEX idx_asset_records_fields_gin ON asset_records USING gin(fields);
CREATE INDEX idx_monitoring_strategies_rule_gin ON monitoring_strategies USING gin(rule);
CREATE INDEX idx_detection_tasks_status_probe ON detection_tasks(status, probe);
CREATE INDEX idx_alert_events_status_severity ON alert_events(status, severity);
CREATE INDEX idx_workorder_requests_status_assignee ON workorder_requests(status, assignee);
CREATE INDEX idx_probe_nodes_status_heartbeat ON probe_nodes(status, heartbeat_at);
CREATE INDEX idx_notifications_target_status ON notifications(target, status);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_event_outbox_status_created ON event_outbox(status, created_at);

-- Optional TimescaleDB extension belongs in a later migration when high-frequency probe metrics are enabled.
-- It must not store asset models, RBAC rules, workorder states, audit logs, or event outbox facts.
