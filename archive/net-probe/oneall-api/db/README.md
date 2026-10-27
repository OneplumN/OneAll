# OneAll Database Contract

This directory records the target PostgreSQL schema for the OneAll rewrite.

The current `oneall-api` runtime is still a Node reference API with JSON-file persistence. The SQL migration is the authoritative target contract for the later Go/Gin service and database migration.

## Boundaries

- PostgreSQL stores business facts: asset models, asset records, alert events, workorders, probes, notifications, audit logs, and event outbox.
- JSONB is used for dynamic asset fields, alert rule DSL, event payloads, notification payloads, sync previews, and probe capabilities.
- Redis Streams may deliver outbox events, but `event_outbox` remains the source of truth.
- TimescaleDB is optional and only for high-frequency probe metrics and aggregates. It must not own asset models, RBAC, workorder state, audit logs, or outbox facts.

## Migration

Apply migrations in lexical order:

```sh
psql "$DATABASE_URL" -f oneall-api/db/migrations/001_initial_schema.sql
```

The phase-1 schema intentionally keeps dynamic asset values in `asset_records.fields` while duplicating common query fields such as `name`, `owner`, `environment`, and `business_line` for filtering and permissions.

## Verification

Run the repeatable minimum business loop from the API package:

```sh
pnpm e2e:business-loop
```

To verify a running API instead of the temporary in-process server:

```sh
ONEALL_API_BASE=http://127.0.0.1:5184 pnpm e2e:business-loop
```

The script validates asset model creation, field validation, asset record write, alert strategy creation, one-off detection, probe task claim/result, generated alert, generated workorder, workorder approval, notification, audit log, and role data-scope filtering.
