import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import http from 'node:http';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createJsonFilePersistence } from '../src/persistence.mjs';
import { createApp } from '../src/server.mjs';
import { createStore } from '../src/store.mjs';

const externalBase = process.env.ONEALL_API_BASE;
const report = [];

async function main() {
  if (externalBase) {
    await runAgainst(externalBase);
    printReport(externalBase);
    return;
  }

  const dir = mkdtempSync(join(tmpdir(), 'oneall-e2e-'));
  const persistence = createJsonFilePersistence(join(dir, 'state.json'));
  const { handler } = createApp({ store: createStore({ persistence }) });
  const server = http.createServer(handler);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();
  const base = `http://127.0.0.1:${port}`;

  try {
    await runAgainst(base);
    printReport(base);
  } finally {
    await new Promise((resolve) => server.close(resolve));
    rmSync(dir, { recursive: true, force: true });
  }
}

async function runAgainst(base) {
  const unique = Date.now();
  const model = await step('create asset model', () => post(base, '/api/v1/assets/models', {
    name: `E2E 域名服务 ${unique}`,
    code: `e2e_domain_service_${unique}`,
    fields: [
      { key: 'name', type: 'string', required: true },
      { key: 'ip', type: 'ip', required: true },
      { key: 'environment', type: 'enum', options: ['prod', 'staging'], required: true }
    ]
  }));
  assert.equal(model.status, 'active');

  const invalidRecord = await postRaw(base, '/api/v1/assets/records/batch', {
    model_id: model.id,
    records: [{ name: 'bad.e2e.oneall.internal', ip: '999.1.1.1', environment: 'prod' }]
  });
  assert.equal(invalidRecord.status, 400);
  report.push({ step: 'reject invalid asset record', status: invalidRecord.status, evidence: invalidRecord.body.error });

  const records = await step('write asset record', () => post(base, '/api/v1/assets/records/batch', {
    model_id: model.id,
    records: [{ name: `checkout-${unique}.oneall.internal`, ip: '10.10.10.8', environment: 'prod' }]
  }));
  assert.equal(records.count, 1);

  const strategy = await step('create alert strategy', () => post(base, '/api/v1/monitoring/strategies', {
    name: `E2E HTTP 可用性 ${unique}`,
    rule: {
      scope: { asset_model: model.code, asset_filter: { environment: 'prod' } },
      signal: { metric: 'probe.success', source: 'probe_result' },
      condition: { operator: 'eq', value: false, consecutive: 1 },
      severity: 'critical',
      actions: { notify_channels: ['site'], create_workorder: true }
    }
  }));
  assert.equal(strategy.rule.actions.create_workorder, true);

  const task = await step('create one-off detection', () => post(base, '/api/v1/detection/one-off', {
    type: 'http',
    target: `https://checkout-${unique}.oneall.internal/health`,
    related_asset: `checkout-${unique}.oneall.internal`,
    environment: 'prod',
    business_line: '支付业务'
  }, 'OpsEngineer'));
  assert.equal(task.status, 'pending');

  const claimed = await step('probe claims task', () => post(base, '/api/v1/probes/tasks/claim', {}));
  assert.equal(claimed.items.some((item) => item.id === task.id), true);

  const result = await step('probe reports failure', () => post(base, `/api/v1/probes/tasks/${task.id}/result`, {
    success: false,
    latency_ms: 5000,
    status_code: 0,
    message: 'E2E forced failure'
  }));
  assert.equal(result.status, 'failed');

  const alerts = await step('alert generated', () => get(base, '/api/v1/alerts/events'));
  const alert = alerts.items.find((item) => item.sourceTaskId === task.id);
  assert.ok(alert, 'alert should be linked to detection task');
  assert.match(alert.workorder, /^WO-/);

  const workorder = await step('workorder generated', () => get(base, `/api/v1/workorders/requests/${alert.workorder}`));
  assert.equal(workorder.relatedAlertId, alert.id);
  assert.equal(workorder.status, 'submitted');

  const approved = await step('workorder approved', () => post(base, `/api/v1/workorders/requests/${workorder.id}/approve`, {}, 'Approver'));
  assert.equal(approved.status, 'approved');

  const notifications = await step('notifications recorded', () => get(base, '/api/v1/notifications'));
  assert.equal(notifications.items.some((item) => item.title.includes(workorder.id)), true);

  const audits = await step('audit logs recorded', () => get(base, '/api/v1/settings/audit-logs'));
  assert.equal(audits.items.some((item) => item.object === workorder.id || item.object === task.id || item.object === model.id), true);

  const viewerRecords = await step('viewer data scope filters records', () => get(base, `/api/v1/assets/records/query?model_id=${model.id}`, 'Viewer'));
  assert.deepEqual(viewerRecords.items.map((item) => item.environment), ['prod']);

  return { model, task, alert, workorder: approved };
}

async function step(name, fn) {
  const result = await fn();
  report.push({ step: name, status: 'ok', evidence: summarize(result) });
  return result;
}

async function get(base, path, role = 'OpsAdmin') {
  const response = await fetch(`${base}${path}`, {
    headers: { 'x-oneall-role': role }
  });
  const body = await response.json();
  if (!response.ok) throw new Error(`GET ${path} ${response.status}: ${JSON.stringify(body)}`);
  return body;
}

async function post(base, path, body, role = 'OpsAdmin') {
  const response = await postRaw(base, path, body, role);
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`POST ${path} ${response.status}: ${JSON.stringify(response.body)}`);
  }
  return response.body;
}

async function postRaw(base, path, body, role = 'OpsAdmin') {
  const response = await fetch(`${base}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-oneall-role': role },
    body: JSON.stringify(body)
  });
  return { status: response.status, body: await response.json() };
}

function summarize(value) {
  if (value?.id) return value.id;
  if (value?.items) return `${value.items.length} items`;
  if (value?.count !== undefined) return `${value.count} records`;
  return 'ok';
}

function printReport(base) {
  console.log(JSON.stringify({ base, passed: true, steps: report }, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({ passed: false, error: error.message, steps: report }, null, 2));
  process.exitCode = 1;
});
