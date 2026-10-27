import http from 'node:http';
import { resolve } from 'node:path';
import { URL } from 'node:url';
import { assertPermission, compileIpRegexFromText, dataScopeMatrix, expandIpRegex, permissionMatrix, roles, workorderStatusMeta } from './domain.mjs';
import { createJsonFilePersistence } from './persistence.mjs';
import { createStore } from './store.mjs';

export function createApp(options = {}) {
  const store = options.store || createStore();

  async function handler(req, res) {
    const url = new URL(req.url || '/', `http://${req.headers.host || '127.0.0.1'}`);
    const role = req.headers['x-oneall-role'] || 'OpsAdmin';

    if (req.method === 'OPTIONS') {
      send(res, 204, null);
      return;
    }

    try {
      const body = await readJson(req);
      const result = route({ method: req.method, pathname: url.pathname, searchParams: url.searchParams, body, role, store });
      send(res, result.status || 200, result.body);
    } catch (error) {
      send(res, error.status || 500, { error: error.message || 'Internal Server Error' });
    }
  }

  return { handler, store };
}

function route({ method, pathname, searchParams, body, role, store }) {
  if (method === 'GET' && pathname === '/healthz') return ok({ status: 'ok' });
  if (method === 'POST' && pathname === '/api/v1/auth/login') return ok({ token: `dev-token-${Date.now()}`, expires_in: 7200 });
  if (method === 'GET' && pathname === '/api/v1/auth/profile') return ok(store.profile(role));
  if (method === 'GET' && pathname === '/api/v1/settings/permissions/catalog') return ok({ roles, permissionMatrix, dataScopeMatrix, workorderStatusMeta });
  if (method === 'GET' && pathname === '/api/v1/monitoring/overview') {
    assertPermission(role, 'monitoringOverview', 'read');
    return ok(store.overview(role));
  }

  if (method === 'GET' && pathname === '/api/v1/assets/models') {
    assertPermission(role, 'assetCenter', 'read');
    return ok({ items: store.listAssetModels() });
  }
  if (method === 'POST' && pathname === '/api/v1/assets/models') {
    assertPermission(role, 'assetCenter', 'create');
    return created(store.createAssetModel(body, role));
  }
  const assetModelSyncPreview = match(pathname, /^\/api\/v1\/assets\/models\/([^/]+)\/sync\/preview$/);
  if (method === 'POST' && assetModelSyncPreview) {
    assertPermission(role, 'assetCenter', 'sync');
    return ok(store.previewAssetSync(assetModelSyncPreview[1], body || {}));
  }
  const assetModelSyncRun = match(pathname, /^\/api\/v1\/assets\/models\/([^/]+)\/sync$/);
  if (method === 'POST' && assetModelSyncRun) {
    assertPermission(role, 'assetCenter', 'sync');
    return ok(store.runAssetSync(assetModelSyncRun[1], body || {}, role));
  }
  const assetModelUpdate = match(pathname, /^\/api\/v1\/assets\/models\/([^/]+)$/);
  if (method === 'PUT' && assetModelUpdate) {
    assertPermission(role, 'assetCenter', 'update');
    return ok(store.updateAssetModel(assetModelUpdate[1], body, role));
  }
  if (method === 'GET' && pathname === '/api/v1/assets/records/query') {
    assertPermission(role, 'assetCenter', 'read');
    const modelId = searchParams.get('model_id');
    const modelCode = searchParams.get('model_code');
    const items = store.listAssetRecords(role).filter((item) => (!modelId || item.model_id === modelId) && (!modelCode || item.model_code === modelCode));
    return ok({ items });
  }
  if (method === 'POST' && pathname === '/api/v1/assets/records/batch') {
    assertPermission(role, 'assetCenter', 'update');
    return ok(store.batchAssetRecords(body, role));
  }
  if (method === 'GET' && pathname === '/api/v1/assets/sync/runs') {
    assertPermission(role, 'assetCenter', 'read');
    return ok({ items: store.state.events.filter((item) => item.event_type.startsWith('asset.sync.')) });
  }

  if (method === 'GET' && pathname === '/api/v1/workorders/requests') {
    assertPermission(role, 'workorders', readWorkorderAction(role));
    return ok({ items: store.listWorkorders(role) });
  }
  if (method === 'POST' && pathname === '/api/v1/workorders/requests') {
    assertPermission(role, 'workorders', 'create');
    return created(store.createWorkorder(body, role));
  }
  if (method === 'POST' && pathname === '/api/v1/workorders/requests/batch') {
    assertPermission(role, 'workorders', body?.action === 'approve' || body?.action === 'reject' ? 'approve' : 'manage');
    return ok(store.batchWorkorders(body, role));
  }
  const workorderAction = match(pathname, /^\/api\/v1\/workorders\/requests\/([^/]+)\/(approve|reject|execute|complete|fail)$/);
  if (method === 'POST' && workorderAction) {
    const [, id, action] = workorderAction;
    const permission = action === 'approve' || action === 'reject' ? 'approve' : 'manage';
    assertPermission(role, 'workorders', permission);
    const nextStatus = { approve: 'approved', reject: 'rejected', execute: 'executing', complete: 'completed', fail: 'failed' }[action];
    return ok(store.transitionWorkorder(id, nextStatus, role));
  }
  const workorderDetail = match(pathname, /^\/api\/v1\/workorders\/requests\/([^/]+)$/);
  if (method === 'GET' && workorderDetail) {
    assertPermission(role, 'workorders', readWorkorderAction(role));
    return ok(store.getWorkorder(workorderDetail[1], role));
  }

  if (method === 'GET' && pathname === '/api/v1/monitoring/strategies') {
    assertPermission(role, 'monitoringPolicies', 'read');
    return ok({ items: store.listStrategies() });
  }
  if (method === 'POST' && pathname === '/api/v1/monitoring/strategies') {
    assertPermission(role, 'monitoringPolicies', 'create');
    return created(store.createStrategy(body, role));
  }
  if (method === 'POST' && pathname === '/api/v1/monitoring/strategies/batch') {
    assertPermission(role, 'monitoringPolicies', 'update');
    return ok(store.batchStrategies(body, role));
  }
  const strategyPreview = match(pathname, /^\/api\/v1\/monitoring\/strategies\/([^/]+)\/preview$/);
  if (method === 'POST' && strategyPreview) {
    assertPermission(role, 'monitoringPolicies', 'execute');
    return ok(store.previewStrategy(strategyPreview[1], body || {}));
  }

  if (method === 'GET' && pathname === '/api/v1/alerts/events') {
    assertPermission(role, 'alertEvents', 'read');
    return ok({ items: store.listAlerts(role) });
  }
  const alertDetail = match(pathname, /^\/api\/v1\/alerts\/events\/([^/]+)$/);
  if (method === 'GET' && alertDetail) {
    assertPermission(role, 'alertEvents', 'read');
    return ok(store.getAlert(alertDetail[1], role));
  }
  if (method === 'POST' && pathname === '/api/v1/alerts/events/batch') {
    assertPermission(role, 'alertEvents', 'close');
    if (body?.action !== 'close') throw badRequest('仅支持 close 批量动作');
    return ok({ items: store.closeAlerts(body.ids || [], role) });
  }

  if (method === 'POST' && pathname === '/api/v1/detection/one-off') {
    assertPermission(role, 'oneOffDetection', 'execute');
    return created(store.createDetection(body, role));
  }
  if (method === 'GET' && pathname === '/api/v1/detection/tasks') {
    assertPermission(role, 'oneOffDetection', 'read');
    return ok({ items: store.listDetectionTasks(role) });
  }
  if (method === 'GET' && pathname === '/api/v1/detection/cmdb/validate') {
    assertPermission(role, 'oneOffDetection', 'read');
    return ok(store.validateCmdbDomain(searchParams.get('domain') || searchParams.get('target') || ''));
  }
  const detectionDetail = match(pathname, /^\/api\/v1\/detection\/tasks\/([^/]+)$/);
  if (method === 'GET' && detectionDetail) {
    assertPermission(role, 'oneOffDetection', 'read');
    return ok(store.getDetectionTask(detectionDetail[1], role));
  }

  if (method === 'POST' && pathname === '/api/v1/probes/register') return created(store.registerProbe(body));
  if (method === 'GET' && pathname === '/api/v1/probes/nodes') {
    assertPermission(role, 'probeNodes', 'read');
    return ok({ items: store.listProbes() });
  }
  if (method === 'GET' && pathname === '/api/v1/probes/nodes/health') {
    assertPermission(role, 'probeNodes', 'read');
    return ok(store.listProbeHealth(positiveInt(searchParams.get('hours'), 6), positiveInt(searchParams.get('interval_minutes'), 10)));
  }
  const probeRuntime = match(pathname, /^\/api\/v1\/probes\/nodes\/([^/]+)\/runtime$/);
  if (method === 'GET' && probeRuntime) {
    assertPermission(role, 'probeNodes', 'read');
    return ok(store.getProbeRuntime(probeRuntime[1]));
  }
  const probeHeartbeat = match(pathname, /^\/api\/v1\/probes\/nodes\/([^/]+)\/heartbeat$/);
  if (method === 'POST' && probeHeartbeat) return ok(store.heartbeatProbe(probeHeartbeat[1], body || {}));
  const probeMetricsHistory = match(pathname, /^\/api\/v1\/probes\/nodes\/([^/]+)\/metrics\/history$/);
  if (method === 'GET' && probeMetricsHistory) {
    assertPermission(role, 'probeNodes', 'read');
    return ok(store.listProbeMetricsHistory(probeMetricsHistory[1], positiveInt(searchParams.get('hours'), 6), positiveInt(searchParams.get('interval_minutes'), 60)));
  }
  const probeRetire = match(pathname, /^\/api\/v1\/probes\/nodes\/([^/]+)\/retire$/);
  if (method === 'POST' && probeRetire) {
    assertPermission(role, 'probeNodes', 'manage');
    return ok(store.retireProbe(probeRetire[1], role));
  }
  const probeConfigRefresh = match(pathname, /^\/api\/v1\/probes\/nodes\/([^/]+)\/config\/refresh$/);
  if (method === 'POST' && probeConfigRefresh) {
    assertPermission(role, 'probeNodes', 'manage');
    return ok(store.refreshProbeConfig(probeConfigRefresh[1], role));
  }
  const probeConfigVersions = match(pathname, /^\/api\/v1\/probes\/nodes\/([^/]+)\/config\/versions$/);
  if (method === 'GET' && probeConfigVersions) {
    assertPermission(role, 'probeNodes', 'read');
    return ok({ items: store.listProbeConfigVersions(probeConfigVersions[1]) });
  }
  const probeConfigRollback = match(pathname, /^\/api\/v1\/probes\/nodes\/([^/]+)\/config\/rollback$/);
  if (method === 'POST' && probeConfigRollback) {
    assertPermission(role, 'probeNodes', 'manage');
    return ok(store.rollbackProbeConfig(probeConfigRollback[1], body || {}, role));
  }
  if (method === 'POST' && pathname === '/api/v1/probes/tasks/claim') return ok({ items: store.claimProbeTasks(body || {}) });
  const probeResult = match(pathname, /^\/api\/v1\/probes\/tasks\/([^/]+)\/result$/);
  if (method === 'POST' && probeResult) return ok(store.submitProbeResult(probeResult[1], body));
  const scheduleResult = match(pathname, /^\/api\/v1\/probes\/schedules\/([^/]+)\/result$/);
  if (method === 'POST' && scheduleResult) return ok({ schedule_id: scheduleResult[1], accepted: true, received_at: new Date().toISOString() });

  if (method === 'GET' && pathname === '/api/v1/settings/users') {
    assertPermission(role, 'usersAndRoles', 'read');
    return ok({ items: store.state.users });
  }
  if (method === 'GET' && pathname === '/api/v1/settings/data-sources') {
    assertPermission(role, 'dataSources', 'read');
    return ok({ items: [{ id: 'ds-1', name: '蓝鲸 CMDB', type: 'blueking_cmdb', status: '已连通' }] });
  }
  if (method === 'GET' && pathname === '/api/v1/settings/credentials') {
    assertPermission(role, 'credentials', 'read');
    return ok({ items: [{ id: 'cred-1', name: 'bk-prod-token', type: 'token', masked_secret: 'bk_p***********' }] });
  }
  if (method === 'GET' && pathname === '/api/v1/settings/notification-channels') {
    assertPermission(role, 'notificationsWebhooks', 'read');
    return ok({ items: [
      { id: 'chn-1', name: '站内通知', type: 'site', status: '已启用' },
      { id: 'chn-2', name: '告警 Webhook', type: 'webhook', status: '已启用' }
    ] });
  }
  if (method === 'GET' && pathname === '/api/v1/settings/notification-templates') {
    assertPermission(role, 'notificationsWebhooks', 'read');
    return ok({ items: [
      { id: 'tpl-1', name: 'P0 告警通知', channel: 'site', variables: ['alert_title', 'asset', 'severity'] },
      { id: 'tpl-2', name: '工单流转通知', channel: 'site', variables: ['workorder_id', 'status'] }
    ] });
  }
  if (method === 'GET' && pathname === '/api/v1/settings/webhooks') {
    assertPermission(role, 'notificationsWebhooks', 'read');
    return ok({ items: [{ id: 'wh-1', name: '告警出站 Webhook', status: '已启用' }] });
  }
  const webhookTest = match(pathname, /^\/api\/v1\/settings\/webhooks\/([^/]+)\/test$/);
  if (method === 'POST' && webhookTest) {
    assertPermission(role, 'notificationsWebhooks', 'update');
    return ok({ id: webhookTest[1], status: 'delivered', trace_id: `trace-${Date.now()}` });
  }
  if (method === 'GET' && pathname === '/api/v1/settings/audit-logs') {
    assertPermission(role, 'auditLogs', 'read');
    return ok({ items: store.listAuditLogs() });
  }

  if (method === 'GET' && pathname === '/api/v1/notifications') return ok({ items: store.listNotifications() });
  if (method === 'GET' && pathname === '/api/v1/notifications/stream') return ok({ items: store.listNotifications(), mode: 'snapshot' });
  if (method === 'GET' && pathname === '/api/v1/search') {
    const q = searchParams.get('q') || '';
    return ok({
      items: [
        ...store.listAlerts(role).filter((item) => item.title.includes(q) || item.asset.includes(q)).map((item) => ({ type: 'alert', id: item.id, title: item.title })),
        ...store.listWorkorders(role).filter((item) => item.title.includes(q) || item.id.includes(q)).map((item) => ({ type: 'workorder', id: item.id, title: item.title }))
      ]
    });
  }
  if (method === 'POST' && pathname === '/api/v1/tools/ip-regex/compile') return ok(compileIpRegexFromText(body?.input || ''));
  if (method === 'POST' && pathname === '/api/v1/tools/ip-regex/expand') return ok(expandIpRegex(body?.regex || '', body?.limit || 500));

  throw notFound('接口不存在');
}

function ok(body) {
  return { status: 200, body };
}

function created(body) {
  return { status: 201, body };
}

function match(value, pattern) {
  return value.match(pattern);
}

function badRequest(message) {
  const error = new Error(message);
  error.status = 400;
  return error;
}

function readWorkorderAction(role) {
  if (role === 'Viewer') return 'read';
  if (role === 'Approver') return 'approve';
  if (role === 'OpsEngineer') return 'execute';
  return 'manage';
}

function positiveInt(value, fallback) {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function notFound(message) {
  const error = new Error(message);
  error.status = 404;
  return error;
}

async function readJson(req) {
  if (!['POST', 'PUT', 'PATCH'].includes(req.method || '')) return undefined;
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const text = Buffer.concat(chunks).toString('utf8').trim();
  if (!text) return {};
  return JSON.parse(text);
}

function send(res, status, body) {
  res.writeHead(status, {
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
    'access-control-allow-headers': 'content-type,x-oneall-role',
    'content-type': 'application/json; charset=utf-8'
  });
  if (status === 204) {
    res.end();
    return;
  }
  res.end(JSON.stringify(body));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const port = Number(process.env.PORT || 5184);
  const dataFile = resolve(process.env.ONEALL_DATA_FILE || 'data/oneall-state.json');
  const { handler } = createApp({ store: createStore({ persistence: createJsonFilePersistence(dataFile) }) });
  http.createServer(handler).listen(port, '127.0.0.1', () => {
    console.log(`OneAll API listening on http://127.0.0.1:${port}`);
    console.log(`OneAll API data file: ${dataFile}`);
  });
}
