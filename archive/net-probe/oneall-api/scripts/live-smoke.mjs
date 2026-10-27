import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const base = process.env.ONEALL_API_BASE;

if (!base) {
  console.error('ONEALL_API_BASE is required, for example http://127.0.0.1:5184');
  process.exit(1);
}

const contract = readFileSync(new URL('../../oneall-antd-prototype/src/platformContracts.ts', import.meta.url), 'utf8');
const endpoints = [...contract.matchAll(/\{\s*key:\s*'([^']+)',\s*domain:\s*'([^']+)',\s*method:\s*'([^']+)',\s*path:\s*'([^']+)'/g)]
  .map((match) => ({ key: match[1], domain: match[2], method: match[3], path: match[4] }));

const report = [];
const context = {};

await run('healthz', 'GET', '/healthz');
for (const endpoint of endpoints) {
  await smoke(endpoint);
}

assert.equal(report.length, endpoints.length + 1);
assert.equal(report.every((item) => item.status >= 200 && item.status < 300), true);

console.log(JSON.stringify({
  base,
  passed: true,
  checks: report.length,
  endpoints: endpoints.length,
  steps: report
}, null, 2));

async function smoke(endpoint) {
  const unique = Date.now();
  const handlers = {
    'search.global': () => run(endpoint.key, 'GET', '/api/v1/search?q=oneall'),
    'auth.login': () => run(endpoint.key, 'POST', endpoint.path, { username: 'ops', password: 'dev' }),
    'auth.profile': () => run(endpoint.key, 'GET', endpoint.path),
    'notifications.list': () => run(endpoint.key, 'GET', endpoint.path),
    'notifications.stream': () => run(endpoint.key, 'GET', endpoint.path),
    'detection.oneOff.create': async () => {
      const body = await run(endpoint.key, 'POST', endpoint.path, { type: 'http', target: `https://smoke-${unique}.oneall.internal/health` }, 'OpsEngineer');
      context.taskId = body.id;
    },
    'detection.tasks.list': () => run(endpoint.key, 'GET', endpoint.path),
    'detection.task.detail': async () => {
      await ensureTask();
      return run(endpoint.key, 'GET', endpoint.path.replace('{id}', context.taskId));
    },
    'detection.cmdb.validate': () => run(endpoint.key, 'GET', `${endpoint.path}?domain=api.oneall.internal`),
    'workorders.create': async () => {
      const body = await run(endpoint.key, 'POST', endpoint.path, { type: '拨测监控申请', title: `Smoke 工单 ${unique}` }, 'OpsEngineer');
      context.workorderId = body.id;
    },
    'workorders.list': () => run(endpoint.key, 'GET', endpoint.path),
    'workorders.detail': async () => {
      await ensureWorkorder();
      return run(endpoint.key, 'GET', endpoint.path.replace('{id}', context.workorderId));
    },
    'workorders.approve': async () => {
      const workorder = await createWorkorderForTransition('审批');
      return run(endpoint.key, 'POST', endpoint.path.replace('{id}', workorder.id), {}, 'Approver');
    },
    'workorders.reject': async () => {
      const workorder = await createWorkorderForTransition('驳回');
      return run(endpoint.key, 'POST', endpoint.path.replace('{id}', workorder.id), {}, 'Approver');
    },
    'workorders.batch': async () => {
      const workorder = await createWorkorderForTransition('批量审批');
      return run(endpoint.key, 'POST', endpoint.path, { ids: [workorder.id], action: 'approve' }, 'Approver');
    },
    'assets.models.list': () => run(endpoint.key, 'GET', endpoint.path),
    'assets.models.create': async () => {
      const body = await run(endpoint.key, 'POST', endpoint.path, modelPayload(unique));
      context.modelId = body.id;
      context.modelCode = body.code;
    },
    'assets.models.update': async () => {
      await ensureModel();
      return run(endpoint.key, 'PUT', endpoint.path.replace('{model_id}', context.modelId), {
        name: `Smoke 模型更新 ${unique}`,
        fields: modelFields()
      });
    },
    'assets.records.query': () => run(endpoint.key, 'GET', endpoint.path),
    'assets.records.batch': async () => {
      await ensureModel();
      return run(endpoint.key, 'POST', endpoint.path, {
        model_id: context.modelId,
        records: [{ name: `api-${unique}.oneall.internal`, ip: '10.1.1.9', environment: 'prod' }]
      });
    },
    'assets.sync.preview': async () => {
      await ensureModel();
      return run(endpoint.key, 'POST', endpoint.path.replace('{model_id}', context.modelId), { source: 'manual' });
    },
    'assets.sync.run': async () => {
      await ensureModel();
      return run(endpoint.key, 'POST', endpoint.path.replace('{model_id}', context.modelId), { source: 'manual' });
    },
    'assets.sync.history': () => run(endpoint.key, 'GET', endpoint.path),
    'monitoring.overview': () => run(endpoint.key, 'GET', endpoint.path),
    'monitoring.strategies.list': () => run(endpoint.key, 'GET', endpoint.path),
    'monitoring.strategies.create': async () => {
      const body = await run(endpoint.key, 'POST', endpoint.path, strategyPayload(unique));
      context.strategyId = body.id;
    },
    'monitoring.strategies.batch': async () => {
      await ensureStrategy();
      return run(endpoint.key, 'POST', endpoint.path, { ids: [context.strategyId], action: 'enable' });
    },
    'alerts.events.list': async () => {
      await ensureAlert();
      return run(endpoint.key, 'GET', endpoint.path);
    },
    'alerts.events.detail': async () => {
      await ensureAlert();
      return run(endpoint.key, 'GET', endpoint.path.replace('{id}', context.alertId));
    },
    'alerts.events.batch': async () => {
      await ensureAlert();
      return run(endpoint.key, 'POST', endpoint.path, { ids: [context.alertId], action: 'close' });
    },
    'probes.register': async () => {
      const body = await run(endpoint.key, 'POST', endpoint.path, { name: `probe-smoke-${unique}`, region: '华东', capabilities: ['HTTP', 'DNS'] });
      context.probeId = body.id;
    },
    'probes.nodes.list': () => run(endpoint.key, 'GET', endpoint.path),
    'probes.nodes.runtime': async () => {
      await ensureProbe();
      return run(endpoint.key, 'GET', endpoint.path.replace('{id}', context.probeId));
    },
    'probes.config.versions': async () => {
      await ensureProbe();
      return run(endpoint.key, 'GET', endpoint.path.replace('{id}', context.probeId));
    },
    'probes.tasks.claim': () => run(endpoint.key, 'POST', endpoint.path, {}),
    'probes.tasks.result': async () => {
      const task = await createTaskForResult();
      return run(endpoint.key, 'POST', endpoint.path.replace('{task_id}', task.id), { success: true, latency_ms: 36, status_code: 200 });
    },
    'probes.schedules.result': () => run(endpoint.key, 'POST', endpoint.path.replace('{schedule_id}', 'sch-smoke'), { success: true }),
    'settings.permissions.catalog': () => run(endpoint.key, 'GET', endpoint.path, undefined, 'PlatformAdmin'),
    'settings.users.list': () => run(endpoint.key, 'GET', endpoint.path, undefined, 'PlatformAdmin'),
    'settings.dataSources.list': () => run(endpoint.key, 'GET', endpoint.path, undefined, 'PlatformAdmin'),
    'settings.credentials.list': () => run(endpoint.key, 'GET', endpoint.path, undefined, 'PlatformAdmin'),
    'settings.notificationChannels.list': () => run(endpoint.key, 'GET', endpoint.path, undefined, 'PlatformAdmin'),
    'settings.notificationTemplates.list': () => run(endpoint.key, 'GET', endpoint.path, undefined, 'PlatformAdmin'),
    'settings.webhooks.list': () => run(endpoint.key, 'GET', endpoint.path, undefined, 'PlatformAdmin'),
    'settings.webhooks.test': () => run(endpoint.key, 'POST', endpoint.path.replace('{id}', 'webhook-1'), {}, 'PlatformAdmin'),
    'settings.auditLogs.list': () => run(endpoint.key, 'GET', endpoint.path, undefined, 'PlatformAdmin'),
    'tools.ipRegex.compile': () => run(endpoint.key, 'POST', endpoint.path, { input: '10.0.0.1\n10.0.0.2' }),
    'tools.ipRegex.expand': () => run(endpoint.key, 'POST', endpoint.path, { regex: '^(10\\.0\\.0\\.1|10\\.0\\.0\\.2)$' })
  };

  const handler = handlers[endpoint.key];
  assert.ok(handler, `Missing smoke handler for ${endpoint.key}`);
  await handler();
}

async function ensureModel() {
  if (context.modelId) return;
  const unique = Date.now();
  const body = await raw('POST', '/api/v1/assets/models', modelPayload(unique));
  context.modelId = body.id;
  context.modelCode = body.code;
}

async function ensureStrategy() {
  if (context.strategyId) return;
  const body = await raw('POST', '/api/v1/monitoring/strategies', strategyPayload(Date.now()));
  context.strategyId = body.id;
}

async function ensureTask() {
  if (context.taskId) return;
  const body = await raw('POST', '/api/v1/detection/one-off', { type: 'http', target: `https://task-${Date.now()}.oneall.internal/health` }, 'OpsEngineer');
  context.taskId = body.id;
}

async function ensureWorkorder() {
  if (context.workorderId) return;
  const body = await raw('POST', '/api/v1/workorders/requests', { type: '拨测监控申请', title: `Smoke 工单 ${Date.now()}` }, 'OpsEngineer');
  context.workorderId = body.id;
}

async function ensureProbe() {
  if (context.probeId) return;
  const body = await raw('POST', '/api/v1/probes/register', { name: `probe-smoke-${Date.now()}`, region: '华东', capabilities: ['HTTP'] });
  context.probeId = body.id;
}

async function ensureAlert() {
  if (context.alertId) return;
  await ensureStrategy();
  const task = await createTaskForResult();
  await raw('POST', `/api/v1/probes/tasks/${task.id}/result`, { success: false, latency_ms: 5001, status_code: 0 });
  const alerts = await raw('GET', '/api/v1/alerts/events');
  context.alertId = alerts.items[0].id;
}

async function createTaskForResult() {
  const body = await raw('POST', '/api/v1/detection/one-off', { type: 'http', target: `https://result-${Date.now()}.oneall.internal/health` }, 'OpsEngineer');
  return body;
}

async function createWorkorderForTransition(label) {
  return raw('POST', '/api/v1/workorders/requests', { type: '拨测监控申请', title: `Smoke ${label} ${Date.now()}` }, 'OpsEngineer');
}

function modelPayload(unique) {
  return {
    name: `Smoke 域名模型 ${unique}`,
    code: `smoke_domain_${unique}`,
    fields: modelFields()
  };
}

function modelFields() {
  return [
    { key: 'name', type: 'string', required: true },
    { key: 'environment', type: 'enum', options: ['prod', 'staging'], required: true }
  ];
}

function strategyPayload(unique) {
  return {
    name: `Smoke HTTP 可用性 ${unique}`,
    rule: {
      scope: { asset_model: context.modelCode || 'smoke_domain', asset_filter: { environment: 'prod' } },
      signal: { metric: 'probe.success', source: 'probe_result' },
      condition: { operator: 'eq', value: false, consecutive: 1 },
      severity: 'critical',
      actions: { notify_channels: ['site'], create_workorder: true }
    }
  };
}

async function run(key, method, path, body, role = 'OpsAdmin') {
  const response = await fetch(`${base}${path}`, requestOptions(method, body, role));
  const item = { key, method, path, status: response.status };
  report.push(item);
  if (response.status < 200 || response.status >= 300) {
    item.body = await safeJson(response);
    throw new Error(`${key} ${method} ${path} returned ${response.status}: ${JSON.stringify(item.body)}`);
  }
  return safeJson(response);
}

async function raw(method, path, body, role = 'OpsAdmin') {
  const response = await fetch(`${base}${path}`, requestOptions(method, body, role));
  const payload = await safeJson(response);
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`${method} ${path} returned ${response.status}: ${JSON.stringify(payload)}`);
  }
  return payload;
}

function requestOptions(method, body, role) {
  return {
    method,
    headers: { 'content-type': 'application/json', 'x-oneall-role': role },
    body: body === undefined || method === 'GET' ? undefined : JSON.stringify(body)
  };
}

async function safeJson(response) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) return {};
  return response.json();
}
