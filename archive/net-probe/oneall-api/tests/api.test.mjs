import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import http from 'node:http';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';
import { createJsonFilePersistence } from '../src/persistence.mjs';
import { createApp } from '../src/server.mjs';
import { createStore } from '../src/store.mjs';

async function withServer(fn, appOptions = {}) {
  const { handler } = createApp(appOptions);
  const server = http.createServer(handler);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();
  try {
    await fn(`http://127.0.0.1:${port}`);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
}

async function request(base, path, options = {}) {
  const response = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      'content-type': 'application/json',
      'x-oneall-role': options.role || 'OpsAdmin',
      ...(options.headers || {})
    },
    body: options.body ? JSON.stringify(options.body) : undefined
  });
  const body = await response.json();
  return { response, body };
}

test('asset center starts without fixed models and allows user-created model', async () => {
  await withServer(async (base) => {
    const empty = await request(base, '/api/v1/assets/models');
    assert.equal(empty.response.status, 200);
    assert.equal(empty.body.items.length, 0);

    const created = await request(base, '/api/v1/assets/models', {
      method: 'POST',
      body: { name: '支付域名服务', code: 'pay_domain_service', fields: [{ key: 'domain', type: 'string' }] }
    });
    assert.equal(created.response.status, 201);
    assert.equal(created.body.code, 'pay_domain_service');
  });
});

test('asset model fields and records are validated against the user definition', async () => {
  await withServer(async (base) => {
    const invalidModel = await request(base, '/api/v1/assets/models', {
      method: 'POST',
      body: { name: '坏模型', code: 'bad_model', fields: [{ key: '1bad', type: 'string' }] }
    });
    assert.equal(invalidModel.response.status, 400);

    const model = await request(base, '/api/v1/assets/models', {
      method: 'POST',
      body: {
        name: '域名资产',
        code: 'domain_asset',
        fields: [
          { key: 'name', type: 'string', required: true },
          { key: 'ip', type: 'ip', required: true },
          { key: 'environment', type: 'enum', options: ['prod', 'staging'], required: true }
        ]
      }
    });
    assert.equal(model.response.status, 201);

    const invalidRecord = await request(base, '/api/v1/assets/records/batch', {
      method: 'POST',
      body: { model_id: model.body.id, records: [{ name: 'api.oneall.internal', ip: '999.1.1.1' }] }
    });
    assert.equal(invalidRecord.response.status, 400);
    assert.match(invalidRecord.body.error, /ip 必须是 IPv4/);

    const validRecord = await request(base, '/api/v1/assets/records/batch', {
      method: 'POST',
      body: { model_id: model.body.id, records: [{ name: 'api.oneall.internal', ip: '10.0.0.1', environment: 'prod' }] }
    });
    assert.equal(validRecord.response.status, 200);
    assert.equal(validRecord.body.items[0].model_code, 'domain_asset');
  });
});

test('workorder status machine rejects invalid transitions and accepts approvals', async () => {
  await withServer(async (base) => {
    const invalid = await request(base, '/api/v1/workorders/requests/WO-0014/complete', { method: 'POST' });
    assert.equal(invalid.response.status, 409);

    const approved = await request(base, '/api/v1/workorders/requests/WO-0014/approve', { method: 'POST', role: 'Approver' });
    assert.equal(approved.response.status, 200);
    assert.equal(approved.body.status, 'approved');
  });
});

test('alert rule endpoint validates DSL before creating strategy', async () => {
  await withServer(async (base) => {
    const bad = await request(base, '/api/v1/monitoring/strategies', {
      method: 'POST',
      body: { name: '坏规则', rule: { scope: {}, actions: {} } }
    });
    assert.equal(bad.response.status, 400);

    const good = await request(base, '/api/v1/monitoring/strategies', {
      method: 'POST',
      body: {
        name: 'HTTP 可用性',
        rule: {
          scope: { asset_model: 'pay_domain_service' },
          signal: { metric: 'http_status', source: 'probe_result' },
          condition: { operator: 'not_in', value: [200], consecutive: 1 },
          severity: 'critical',
          actions: { notify_channels: ['site'], create_workorder: true }
        }
      }
    });
    assert.equal(good.response.status, 201);
    assert.equal(good.body.name, 'HTTP 可用性');
  });
});

test('permissions protect management APIs', async () => {
  await withServer(async (base) => {
    const denied = await request(base, '/api/v1/assets/models', {
      method: 'POST',
      role: 'Viewer',
      body: { name: '无权模型', code: 'denied_model' }
    });
    assert.equal(denied.response.status, 403);
  });
});

test('data scopes filter assets alerts workorders and search by role', async () => {
  await withServer(async (base) => {
    const model = await request(base, '/api/v1/assets/models', {
      method: 'POST',
      body: {
        name: '数据范围模型',
        code: 'scope_model',
        fields: [
          { key: 'name', type: 'string', required: true },
          { key: 'environment', type: 'enum', options: ['prod', 'staging'], required: true }
        ]
      }
    });
    await request(base, '/api/v1/assets/records/batch', {
      method: 'POST',
      body: {
        model_id: model.body.id,
        records: [
          { name: 'prod.oneall.internal', environment: 'prod' },
          { name: 'staging.oneall.internal', environment: 'staging' }
        ]
      }
    });

    const adminRecords = await request(base, '/api/v1/assets/records/query');
    const viewerRecords = await request(base, '/api/v1/assets/records/query', { role: 'Viewer' });
    assert.equal(adminRecords.body.items.length, 2);
    assert.equal(viewerRecords.body.items.length, 1);
    assert.equal(viewerRecords.body.items[0].name, 'prod.oneall.internal');

    const approverWorkorders = await request(base, '/api/v1/workorders/requests', { role: 'Approver' });
    assert.equal(approverWorkorders.response.status, 200);
    assert.deepEqual(approverWorkorders.body.items.map((item) => item.id), ['WO-0014']);

    const forbiddenDetail = await request(base, '/api/v1/workorders/requests/WO-0015', { role: 'Approver' });
    assert.equal(forbiddenDetail.response.status, 403);

    const scopedSearch = await request(base, '/api/v1/search?q=WO-0015', { role: 'Approver' });
    assert.equal(scopedSearch.response.status, 200);
    assert.equal(scopedSearch.body.items.length, 0);

    const catalog = await request(base, '/api/v1/settings/permissions/catalog');
    assert.equal(catalog.body.dataScopeMatrix.Viewer.assets, 'prod');
  });
});

test('probe and detection APIs form a minimal execution loop', async () => {
  await withServer(async (base) => {
    const task = await request(base, '/api/v1/detection/one-off', {
      method: 'POST',
      role: 'OpsEngineer',
      body: { type: 'http', target: 'https://api.oneall.internal/health' }
    });
    assert.equal(task.response.status, 201);

    const claimed = await request(base, '/api/v1/probes/tasks/claim', { method: 'POST' });
    assert.equal(claimed.body.items[0].id, task.body.id);

    const result = await request(base, `/api/v1/probes/tasks/${task.body.id}/result`, {
      method: 'POST',
      body: { success: false, latency_ms: 5018, status_code: 0 }
    });
    assert.equal(result.body.status, 'failed');

    const listed = await request(base, '/api/v1/detection/tasks');
    assert.equal(listed.response.status, 200);
    assert.equal(listed.body.items[0].id, task.body.id);
  });
});

test('JSON persistence restores state across store instances', () => {
  const dir = mkdtempSync(join(tmpdir(), 'oneall-api-'));
  const file = join(dir, 'state.json');
  try {
    const persistence = createJsonFilePersistence(file);
    const first = createStore({ persistence });
    const model = first.createAssetModel({ name: '支付域名服务', code: 'pay_domain_service' }, 'OpsAdmin');
    assert.equal(model.id, 'MDL-0001');

    const second = createStore({ persistence });
    assert.equal(second.listAssetModels()[0].code, 'pay_domain_service');
    assert.match(readFileSync(file, 'utf8'), /pay_domain_service/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('business actions write audit logs notifications and events', async () => {
  await withServer(async (base) => {
    await request(base, '/api/v1/assets/models', {
      method: 'POST',
      body: { name: '应用服务', code: 'app_service' }
    });
    const audit = await request(base, '/api/v1/settings/audit-logs');
    assert.equal(audit.response.status, 200);
    assert.equal(audit.body.items[0].action, '创建资产模型');

    const notifications = await request(base, '/api/v1/notifications');
    assert.equal(notifications.response.status, 200);
    assert.match(notifications.body.items[0].title, /资产模型已创建/);

    const syncRuns = await request(base, '/api/v1/assets/sync/runs');
    assert.equal(syncRuns.body.items[0].event_type, 'asset.sync.started');
  });
});

test('monitoring loop creates alert and workorder after failed probe result', async () => {
  await withServer(async (base) => {
    const task = await request(base, '/api/v1/detection/one-off', {
      method: 'POST',
      role: 'OpsEngineer',
      body: { type: 'http', target: 'https://checkout.oneall.internal/health', related_asset: 'checkout.oneall.internal' }
    });
    const result = await request(base, `/api/v1/probes/tasks/${task.body.id}/result`, {
      method: 'POST',
      body: { success: false, latency_ms: 5000, status_code: 0 }
    });
    assert.equal(result.response.status, 200);

    const alerts = await request(base, '/api/v1/alerts/events');
    assert.notEqual(alerts.body.items[0].id, 'ALT-0001');
    assert.notEqual(alerts.body.items[0].id, 'ALT-0002');
    assert.equal(alerts.body.items[0].sourceTaskId, task.body.id);
    assert.equal(alerts.body.items[0].asset, 'checkout.oneall.internal');
    assert.match(alerts.body.items[0].workorder, /^WO-/);

    const workorders = await request(base, '/api/v1/workorders/requests');
    assert.notEqual(workorders.body.items[0].id, 'WO-0014');
    assert.notEqual(workorders.body.items[0].id, 'WO-0015');
    assert.equal(workorders.body.items[0].related_object, alerts.body.items[0].id);
    assert.equal(workorders.body.items[0].relatedAlertId, alerts.body.items[0].id);

    const notifications = await request(base, '/api/v1/notifications');
    assert.match(notifications.body.items.map((item) => item.title).join('\n'), /告警已自动创建工单/);
  });
});

test('declared core v1 endpoints cover asset sync workorder alert probe and cmdb flows', async () => {
  await withServer(async (base) => {
    const created = await request(base, '/api/v1/assets/models', {
      method: 'POST',
      body: { name: '域名服务', code: 'domain_service', fields: [{ key: 'name', type: 'string' }] }
    });
    assert.equal(created.response.status, 201);

    const updated = await request(base, `/api/v1/assets/models/${created.body.id}`, {
      method: 'PUT',
      body: { fields: [{ key: 'name', type: 'string' }, { key: 'owner', type: 'user' }] }
    });
    assert.equal(updated.response.status, 200);
    assert.equal(updated.body.fields.length, 2);

    const preview = await request(base, `/api/v1/assets/models/${created.body.id}/sync/preview`, {
      method: 'POST',
      body: { source: 'blueking_cmdb', owner: 'OpsAdmin' }
    });
    assert.equal(preview.response.status, 200);
    assert.equal(preview.body.model_id, created.body.id);

    const sync = await request(base, `/api/v1/assets/models/${created.body.id}/sync`, {
      method: 'POST',
      body: { source: 'blueking_cmdb', owner: 'OpsAdmin' }
    });
    assert.equal(sync.response.status, 200);
    assert.equal(sync.body.records.length, 1);

    const records = await request(base, `/api/v1/assets/records/query?model_id=${created.body.id}`);
    assert.equal(records.response.status, 200);
    assert.equal(records.body.items.length, 1);

    const cmdb = await request(base, `/api/v1/detection/cmdb/validate?domain=${records.body.items[0].name}`);
    assert.equal(cmdb.response.status, 200);
    assert.equal(cmdb.body.matched, true);

    const alert = await request(base, '/api/v1/alerts/events/ALT-0001');
    assert.equal(alert.response.status, 200);
    assert.equal(alert.body.id, 'ALT-0001');

    const workorder = await request(base, '/api/v1/workorders/requests/WO-0014');
    assert.equal(workorder.response.status, 200);
    assert.equal(workorder.body.related_object, 'ALT-0001');

    const batch = await request(base, '/api/v1/workorders/requests/batch', {
      method: 'POST',
      role: 'Approver',
      body: { action: 'approve', ids: ['WO-0014'] }
    });
    assert.equal(batch.response.status, 200);
    assert.equal(batch.body.items[0].status, 'approved');

    const runtime = await request(base, '/api/v1/probes/nodes/PRB-0001/runtime');
    assert.equal(runtime.response.status, 200);
    assert.equal(runtime.body.name, 'probe-sh-01');
    assert.equal(runtime.body.probe.id, 'PRB-0001');

    const health = await request(base, '/api/v1/probes/nodes/health?hours=1&interval_minutes=10');
    assert.equal(health.response.status, 200);
    assert.equal(health.body.items[0].probe_id, 'PRB-0001');

    const metrics = await request(base, '/api/v1/probes/nodes/PRB-0001/metrics/history?hours=1&interval_minutes=15');
    assert.equal(metrics.response.status, 200);
    assert.equal(metrics.body.points.length, 4);

    const versions = await request(base, '/api/v1/probes/nodes/PRB-0001/config/versions');
    assert.equal(versions.response.status, 200);
    assert.equal(versions.body.items[0].status, 'acknowledged');

    const refreshed = await request(base, '/api/v1/probes/nodes/PRB-0001/config/refresh', { method: 'POST' });
    assert.equal(refreshed.response.status, 200);
    assert.equal(refreshed.body.id, 'PRB-0001');

    const rolledBack = await request(base, '/api/v1/probes/nodes/PRB-0001/config/rollback', { method: 'POST', body: { version: 1 } });
    assert.equal(rolledBack.response.status, 200);
    assert.equal(rolledBack.body.version, 'v1');
  });
});

test('supporting v1 endpoints cover auth notifications batch strategy webhooks and ip tools', async () => {
  await withServer(async (base) => {
    const login = await request(base, '/api/v1/auth/login', {
      method: 'POST',
      body: { username: 'ops', password: 'dev' }
    });
    assert.equal(login.response.status, 200);
    assert.match(login.body.token, /^dev-token-/);

    const strategy = await request(base, '/api/v1/monitoring/strategies', {
      method: 'POST',
      body: {
        name: '批量启停验证',
        rule: {
          scope: { asset_model: 'domain_service' },
          signal: { metric: 'http_status', source: 'probe_result' },
          condition: { operator: 'not_in', value: [200] },
          severity: 'warning',
          actions: { notify_channels: ['site'], create_workorder: false }
        }
      }
    });
    const batch = await request(base, '/api/v1/monitoring/strategies/batch', {
      method: 'POST',
      body: { action: 'disable', ids: [strategy.body.id] }
    });
    assert.equal(batch.response.status, 200);
    assert.equal(batch.body.items[0].enabled, false);

    const stream = await request(base, '/api/v1/notifications/stream');
    assert.equal(stream.response.status, 200);
    assert.equal(stream.body.mode, 'snapshot');

    const webhook = await request(base, '/api/v1/settings/webhooks/wh-1/test', { method: 'POST' });
    assert.equal(webhook.response.status, 200);
    assert.equal(webhook.body.status, 'delivered');

    const compiled = await request(base, '/api/v1/tools/ip-regex/compile', {
      method: 'POST',
      body: { input: '192.168.1.10\n192.168.1.11' }
    });
    const expanded = await request(base, '/api/v1/tools/ip-regex/expand', {
      method: 'POST',
      body: { regex: compiled.body.regex }
    });
    assert.deepEqual(expanded.body.items, ['192.168.1.10', '192.168.1.11']);
  });
});

test('backend routes every endpoint declared by frontend api v1 contract', async () => {
  const contractSource = readFileSync(new URL('../../oneall-antd-prototype/src/platformContracts.ts', import.meta.url), 'utf8');
  const endpoints = [...contractSource.matchAll(/\{\s*key:\s*'([^']+)'.*?method:\s*'([^']+)'.*?path:\s*'([^']+)'/gs)]
    .map((match) => ({ key: match[1], method: match[2], path: match[3] }));

  await withServer(async (base) => {
    const model = await request(base, '/api/v1/assets/models', {
      method: 'POST',
      body: { name: '契约路由模型', code: 'contract_route_model', fields: [{ key: 'name', type: 'string' }] }
    });
    const task = await request(base, '/api/v1/detection/one-off', {
      method: 'POST',
      role: 'OpsEngineer',
      body: { type: 'http', target: 'https://contract.oneall.internal/health', related_asset: 'contract.oneall.internal' }
    });
    const workorder = await request(base, '/api/v1/workorders/requests', {
      method: 'POST',
      role: 'OpsEngineer',
      body: { type: '拨测监控申请', title: '契约路由工单' }
    });
    const strategy = await request(base, '/api/v1/monitoring/strategies', {
      method: 'POST',
      body: {
        name: '契约路由策略',
        rule: {
          scope: { asset_model: model.body.code },
          signal: { metric: 'http_status', source: 'probe_result' },
          condition: { operator: 'not_in', value: [200] },
          severity: 'warning',
          actions: { notify_channels: ['site'], create_workorder: false }
        }
      }
    });

    const replacements = {
      '{model_id}': model.body.id,
      '{id}': task.body.id,
      '{task_id}': task.body.id,
      '{schedule_id}': 'SCH-0001'
    };

    for (const endpoint of endpoints) {
      let path = endpoint.path;
      if (endpoint.key.startsWith('workorders.')) path = path.replace('{id}', workorder.body.id);
      if (endpoint.key.startsWith('alerts.')) path = path.replace('{id}', 'ALT-0001');
      if (endpoint.key.startsWith('probes.nodes') || endpoint.key.startsWith('probes.config')) path = path.replace('{id}', 'PRB-0001');
      for (const [token, value] of Object.entries(replacements)) path = path.replaceAll(token, value);
      if (endpoint.key === 'detection.cmdb.validate') path += '?domain=contract.oneall.internal';
      if (endpoint.key === 'search.global') path += '?q=contract';

      const response = await request(base, path, {
        method: endpoint.method,
        role: roleForEndpoint(endpoint.key),
        body: endpoint.method === 'GET' ? undefined : bodyForEndpoint(endpoint.key, { model, task, workorder, strategy })
      });
      assert.notEqual(response.response.status, 404, `${endpoint.method} ${endpoint.path} (${endpoint.key}) should be routed`);
    }
  });
});

function roleForEndpoint(key) {
  if (key.startsWith('workorders.approve') || key.startsWith('workorders.reject') || key === 'workorders.batch') return 'Approver';
  if (key.startsWith('detection.')) return key === 'detection.oneOff.create' ? 'OpsEngineer' : 'OpsAdmin';
  return 'OpsAdmin';
}

function bodyForEndpoint(key, fixture) {
  if (key === 'auth.login') return { username: 'ops', password: 'dev' };
  if (key === 'detection.oneOff.create') return { type: 'http', target: 'https://contract-extra.oneall.internal/health' };
  if (key === 'workorders.create') return { type: '拨测监控申请', title: '契约新增工单' };
  if (key === 'workorders.batch') return { action: 'approve', ids: [fixture.workorder.body.id] };
  if (key === 'assets.models.create') return { name: '契约新增模型', code: `contract_model_${Date.now()}` };
  if (key === 'assets.models.update') return { fields: [{ key: 'name', type: 'string' }, { key: 'owner', type: 'user' }] };
  if (key === 'assets.records.batch') return { model_id: fixture.model.body.id, records: [{ name: 'contract.oneall.internal', owner: 'OpsAdmin' }] };
  if (key === 'assets.sync.preview' || key === 'assets.sync.run') return { source: 'blueking_cmdb' };
  if (key === 'monitoring.strategies.create') {
    return {
      name: '契约新增策略',
      rule: {
        scope: { asset_model: fixture.model.body.code },
        signal: { metric: 'http_status', source: 'probe_result' },
        condition: { operator: 'not_in', value: [200] },
        severity: 'warning',
        actions: { notify_channels: ['site'], create_workorder: false }
      }
    };
  }
  if (key === 'monitoring.strategies.batch') return { action: 'disable', ids: [fixture.strategy.body.id] };
  if (key === 'alerts.events.batch') return { action: 'close', ids: ['ALT-0001'] };
  if (key === 'probes.register') return { name: `probe-contract-${Date.now()}`, region: 'contract', capabilities: ['HTTP'] };
  if (key === 'probes.config.rollback') return { version: 1 };
  if (key === 'probes.tasks.result') return { success: true, latency_ms: 12 };
  if (key === 'probes.schedules.result') return { success: true, latency_ms: 12 };
  if (key === 'settings.webhooks.test') return { payload: { ping: true } };
  if (key === 'tools.ipRegex.compile') return { input: '10.0.0.1' };
  if (key === 'tools.ipRegex.expand') return { regex: '^(10\\.0\\.0\\.1)$' };
  return {};
}

test('postgres schema covers core business facts and persistence boundaries', () => {
  const schema = readFileSync(new URL('../db/migrations/001_initial_schema.sql', import.meta.url), 'utf8');

  for (const table of [
    'oneall_users',
    'asset_models',
    'asset_records',
    'asset_sync_runs',
    'monitoring_strategies',
    'detection_tasks',
    'alert_events',
    'workorder_requests',
    'probe_nodes',
    'notifications',
    'audit_logs',
    'event_outbox'
  ]) {
    assert.match(schema, new RegExp(`CREATE TABLE ${table}\\b`), `${table} should be in initial schema`);
  }

  for (const jsonbColumn of [
    'fields JSONB',
    'rule JSONB',
    'result JSONB',
    'capabilities JSONB',
    'payload JSONB',
    'preview JSONB'
  ]) {
    assert.match(schema, new RegExp(jsonbColumn), `${jsonbColumn} should be stored as JSONB`);
  }

  assert.match(schema, /REFERENCES asset_models\(id\)/);
  assert.match(schema, /REFERENCES detection_tasks\(id\)/);
  assert.match(schema, /REFERENCES alert_events\(id\)/);
  assert.match(schema, /event_outbox[\s\S]+status TEXT NOT NULL DEFAULT 'pending'/);
  assert.match(schema, /USING gin\(fields\)/);
  assert.match(schema, /idx_workorder_requests_status_assignee/);
  assert.match(schema, /TimescaleDB[\s\S]+must not store asset models, RBAC rules, workorder states, audit logs, or event outbox facts/);
});

test('business loop e2e script is available and covers the required lifecycle', () => {
  const packageJson = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
  const script = readFileSync(new URL('../scripts/e2e-business-loop.mjs', import.meta.url), 'utf8');
  const smokeScript = readFileSync(new URL('../scripts/live-smoke.mjs', import.meta.url), 'utf8');

  assert.equal(packageJson.scripts['e2e:business-loop'], 'node scripts/e2e-business-loop.mjs');
  assert.equal(packageJson.scripts['smoke:live'], 'node scripts/live-smoke.mjs');
  for (const phrase of [
    'create asset model',
    'reject invalid asset record',
    'create alert strategy',
    'create one-off detection',
    'probe reports failure',
    'alert generated',
    'workorder generated',
    'workorder approved',
    'notifications recorded',
    'audit logs recorded',
    'viewer data scope filters records'
  ]) {
    assert.match(script, new RegExp(phrase));
  }
  assert.match(script, /ONEALL_API_BASE/);
  assert.match(smokeScript, /platformContracts\.ts/);
  assert.match(smokeScript, /endpoints\.length \+ 1/);
  assert.match(smokeScript, /settings\.notificationChannels\.list/);
  assert.match(smokeScript, /settings\.auditLogs\.list/);
});

test('go gin target service declares every frontend api contract route key', () => {
  const contractSource = readFileSync(new URL('../../oneall-antd-prototype/src/platformContracts.ts', import.meta.url), 'utf8');
  const routerSource = readFileSync(new URL('../../oneall-go-api/internal/httpapi/router.go', import.meta.url), 'utf8');
  const domainSource = readFileSync(new URL('../../oneall-go-api/internal/domain/contracts.go', import.meta.url), 'utf8');
  const storeSource = readFileSync(new URL('../../oneall-go-api/internal/store/memory.go', import.meta.url), 'utf8');
  const storeInterfaceSource = readFileSync(new URL('../../oneall-go-api/internal/store/store.go', import.meta.url), 'utf8');
  const postgresSource = readFileSync(new URL('../../oneall-go-api/internal/store/postgres.go', import.meta.url), 'utf8');
  const goMod = readFileSync(new URL('../../oneall-go-api/go.mod', import.meta.url), 'utf8');
  const goSum = readFileSync(new URL('../../oneall-go-api/go.sum', import.meta.url), 'utf8');
  const readme = readFileSync(new URL('../../oneall-go-api/README.md', import.meta.url), 'utf8');
  const endpointKeys = [...contractSource.matchAll(/\{\s*key:\s*'([^']+)'.*?path:\s*'([^']+)'/gs)]
    .map((match) => match[1]);

  assert.match(goMod, /github\.com\/gin-gonic\/gin/);
  assert.match(goMod, /github\.com\/jackc\/pgx\/v5/);
  assert.match(goSum, /github\.com\/gin-gonic\/gin/);
  assert.match(goSum, /github\.com\/jackc\/pgx\/v5/);
  assert.match(routerSource, /func RegisterRoutes/);
  assert.match(routerSource, /func corsMiddleware/);
  assert.match(routerSource, /Access-Control-Allow-Origin/);
  assert.match(routerSource, /X-OneAll-Role/);
  assert.match(readme, /All endpoints declared/);
  assert.doesNotMatch(routerSource, /contractHandler\("([^"]+)"\)/);
  assert.doesNotMatch(routerSource, /StatusNotImplemented|501/);
  assert.match(routerSource, /Store\s+store\.Store/);
  assert.match(routerSource, /store\.NewRuntimeStore\(cfg\.DatabaseURL\)/);
  assert.match(storeInterfaceSource, /type Store interface/);
  assert.match(storeInterfaceSource, /func NewRuntimeStore\(databaseURL string\) Store/);
  assert.match(storeInterfaceSource, /return NewPostgresStore\(databaseURL\)/);
  assert.match(postgresSource, /type PostgresStore struct/);
  assert.match(postgresSource, /pgxpool\.New/);
  assert.match(postgresSource, /postgresSchemaContract/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) ListAssetModels/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) CreateAssetModel/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) UpdateAssetModel/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) BatchAssetRecords/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) ListStrategies/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) CreateStrategy/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) CreateDetection/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) ListDetectionTasks/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) SubmitProbeResult/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) createAlertAndMaybeWorkorderPostgres/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) CreateWorkorder/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) TransitionWorkorder/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) ListNotifications/);
  assert.match(postgresSource, /func \(s \*PostgresStore\) ListAuditLogs/);
  assert.match(postgresSource, /regexp_replace\(%s, '\[\^0-9\]'/);
  assert.match(postgresSource, /INSERT INTO asset_models/);
  assert.match(postgresSource, /INSERT INTO asset_records/);
  assert.match(postgresSource, /INSERT INTO monitoring_strategies/);
  assert.match(postgresSource, /INSERT INTO detection_tasks/);
  assert.match(postgresSource, /UPDATE detection_tasks/);
  assert.match(postgresSource, /INSERT INTO alert_events/);
  assert.match(postgresSource, /INSERT INTO workorder_requests/);
  assert.match(postgresSource, /COALESCE\(related_alert_id, ''\)/);
  assert.match(postgresSource, /UPDATE alert_events/);
  assert.match(postgresSource, /UPDATE workorder_requests/);
  assert.match(postgresSource, /INSERT INTO audit_logs/);
  assert.match(postgresSource, /INSERT INTO notifications/);
  assert.match(postgresSource, /INSERT INTO event_outbox/);
  assert.match(domainSource, /var PermissionMatrix/);
  assert.match(domainSource, /func ValidateAssetFields/);
  assert.match(domainSource, /func ValidateAssetRecord/);
  assert.match(domainSource, /func ValidateAlertRule/);
  assert.match(domainSource, /func CompileIPRegexFromText/);
  assert.match(domainSource, /func ExpandIPRegex/);
  assert.match(domainSource, /func TransitionWorkorder/);
  assert.match(domainSource, /RelatedAlertID\s+string\s+`json:"relatedAlertId,omitempty"`/);
  assert.match(domainSource, /type WorkorderStatusMetadata struct/);
  assert.match(domainSource, /Tab:\s*"待我审批"/);
  assert.match(storeSource, /func \(s \*MemoryStore\) CreateAssetModel/);
  assert.match(storeSource, /func \(s \*MemoryStore\) UpdateAssetModel/);
  assert.match(storeSource, /func \(s \*MemoryStore\) BatchAssetRecords/);
  assert.match(storeSource, /func \(s \*MemoryStore\) PreviewAssetSync/);
  assert.match(storeSource, /func \(s \*MemoryStore\) RunAssetSync/);
  assert.match(storeSource, /func \(s \*MemoryStore\) ValidateCMDBDomain/);
  assert.match(storeSource, /func \(s \*MemoryStore\) RegisterProbe/);
  assert.match(storeSource, /func \(s \*MemoryStore\) GetProbeRuntime/);
  assert.match(storeSource, /func \(s \*MemoryStore\) CreateStrategy/);
  assert.match(storeSource, /func \(s \*MemoryStore\) BatchStrategies/);
  assert.match(storeSource, /func \(s \*MemoryStore\) CreateDetection/);
  assert.match(storeSource, /func \(s \*MemoryStore\) SubmitProbeResult/);
  assert.match(storeSource, /func \(s \*MemoryStore\) createAlertAndMaybeWorkorderLocked/);
  assert.match(storeSource, /func \(s \*MemoryStore\) CloseAlerts/);
  assert.match(storeSource, /func \(s \*MemoryStore\) ListNotifications/);
  assert.match(storeSource, /func \(s \*MemoryStore\) ListAuditLogs/);
  assert.match(routerSource, /permissionCatalogHandler/);
  assert.match(routerSource, /createAssetModelHandler/);
  assert.match(routerSource, /batchAssetRecordsHandler/);
  assert.match(routerSource, /createStrategyHandler/);
  assert.match(routerSource, /createDetectionHandler/);
  assert.match(routerSource, /listDetectionTasksHandler/);
  assert.match(routerSource, /submitProbeResultHandler/);
  assert.match(routerSource, /validateCMDBDomainHandler/);
  assert.match(routerSource, /runAssetSyncHandler/);
  assert.match(routerSource, /registerProbeHandler/);
  assert.match(routerSource, /compileIPRegexHandler/);
  assert.match(routerSource, /listNotificationsHandler/);
  assert.match(routerSource, /listAuditLogsHandler/);
  assert.match(routerSource, /transitionWorkorderHandler/);

  for (const key of endpointKeys) {
    assert.match(routerSource, new RegExp(`routeKey\\("${escapeRegex(key)}"`), `${key} should be registered in Go router`);
  }
});

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
