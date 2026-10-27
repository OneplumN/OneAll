# OneAll Go API Target

This directory is the Go/Gin target service skeleton for the OneAll rewrite.

The runnable reference API currently lives in `oneall-api` and is used to stabilize the `/api/v1` business contract and the end-to-end business loop. This Go service fixes the intended production shape:

- Gin HTTP router under `/api/v1`
- PostgreSQL via `DATABASE_URL`
- JWT/LDAP/RBAC boundary via config and middleware-ready route grouping
- route parity with `oneall-antd-prototype/src/platformContracts.ts`

## Status

The route surface is registered and the first stable business contracts are implemented first in Go:

- permission catalog: roles, permission matrix, data scopes, and workorder status metadata
- asset model list/create with user-defined field validation
- asset record batch write/query with model field validation
- alert strategy list/create with DSL validation
- one-off detection, probe heartbeat, probe task claim/result, generated alert, generated workorder
- notification and audit-log list endpoints for lifecycle evidence
- workorder create/list/detail and approval transition with RBAC checks
- profile endpoint based on the current `x-oneall-role`
- CMDB domain validation, asset sync preview/run/history, probe registration/runtime/config versions, batch strategy/workorder/alert operations, global search, login, monitoring overview, webhook test, and IP regex tools

All endpoints declared in `oneall-antd-prototype/src/platformContracts.ts` now have a handler in the Go target service. The main business loop has been verified both with the in-memory store and with PostgreSQL through `DATABASE_URL`. The remaining production work is finishing PostgreSQL replacements for auxiliary compatibility flows that still inherit the memory fallback, plus hardening auth, migrations, and deployment packaging.

The HTTP layer now depends on `store.Store` rather than `MemoryStore`. `NewRuntimeStore(DATABASE_URL)` keeps local runs on the in-memory store and selects `PostgresStore` when `DATABASE_URL` is set, so the PostgreSQL migration can proceed behind the same handler contract.

`PostgresStore` now covers the main business chain with SQL-backed paths: asset model list/create/update, asset record batch write/query, strategy list/create, detection list/create/claim/result, failed-probe alert generation, automatic/manual workorder creation, workorder transition, notifications, audit logs, and event outbox writes. These writes record lifecycle evidence in audit logs, notifications, and outbox events instead of only returning API payloads.

The Go router includes a CORS middleware for local Vite integration, including the `x-oneall-role` header used by the frontend role switcher.

The repository also includes a real local probe agent at `cmd/oneall-probe-agent`. It heartbeats to the API, claims pending detection tasks, executes HTTP/HTTPS, TCP, DNS, and certificate checks, then posts the result back to `/api/v1/probes/tasks/{task_id}/result`.

The probe communication path now handles normal unstable-network cases:

- the agent retries with exponential backoff when the API is unreachable;
- failed result callbacks are stored in a local JSON spool and replayed before claiming new work;
- result payloads include a deterministic `result_id` for idempotent callbacks;
- every heartbeat, claim, and result callback carries `x-oneall-probe-id`, `Authorization: Bearer <token>`, and `x-oneall-trace-id`;
- the backend ignores duplicate callbacks for already-completed tasks;
- running tasks are returned to `pending` after a timeout window so a lost agent does not leave work stuck forever;
- probe list/runtime views degrade nodes after missed heartbeats and mark them offline after longer silence.

Verified commands:

```sh
GOPROXY=https://goproxy.cn,direct go test ./...
ONEALL_API_BASE=http://127.0.0.1:61984 pnpm --dir ../oneall-api e2e:business-loop
DATABASE_URL=postgres://lihaonan@127.0.0.1:61985/oneall_e2e?sslmode=disable ONEALL_API_BASE=http://127.0.0.1:61986 pnpm --dir ../oneall-api e2e:business-loop
```

## Expected Commands

```sh
go mod tidy
go test ./...
node scripts/real-probe-smoke.mjs
go run ./cmd/oneall-api
```

Run a local probe agent after registering a probe and copying the one-time token from the registration response:

```sh
ONEALL_API_BASE=http://127.0.0.1:5184 \
ONEALL_PROBE_ID=PRB-0001 \
ONEALL_PROBE_TOKEN=probe_token_xxx \
ONEALL_PROBE_SPOOL_PATH=/var/lib/oneall/probe-pending-results.json \
go run ./cmd/oneall-probe-agent
```

For a single poll/execute/report cycle:

```sh
go run ./cmd/oneall-probe-agent \
  -api http://127.0.0.1:5184 \
  -probe-id PRB-0001 \
  -token probe_token_xxx \
  -once
```

After handlers are implemented, run the shared business loop against the Go service:

```sh
ONEALL_API_BASE=http://127.0.0.1:5184 pnpm --dir ../oneall-api e2e:business-loop
```

The acceptance target is the same as the reference API: asset model creation, record validation, alert strategy creation, one-off detection, probe result, generated alert, generated workorder, notification, audit log, and data-scope filtering.
