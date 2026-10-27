import { extractTargetHost } from './detectionContracts';

const viteEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
const API_BASE = viteEnv?.VITE_ONEALL_API_BASE || 'http://127.0.0.1:5184';
const USE_REMOTE_API = Boolean(viteEnv?.VITE_ONEALL_API_BASE);
const ROLE_STORAGE_KEY = 'oneall.currentRole';
const LOCAL_ASSET_MODELS_KEY = 'oneall.assetModels';
const LOCAL_ASSET_MODEL_DELETIONS_KEY = 'oneall.assetModelDeletions';
const LOCAL_ASSET_RECORDS_KEY = 'oneall.assetRecords';
const LOCAL_ASSET_SYNC_SCRIPTS_KEY = 'oneall.assetSyncScripts';
const LOCAL_ASSET_SYNC_RUNS_KEY = 'oneall.assetSyncRuns';
const LOCAL_AUDIT_LOGS_KEY = 'oneall.auditLogs';
const LOCAL_ALERTS_KEY = 'oneall.alertEvents';
const LOCAL_WORKORDERS_KEY = 'oneall.workorders';
const LOCAL_STRATEGIES_KEY = 'oneall.monitoringStrategies';
const LOCAL_PROBES_KEY = 'oneall.probeNodes';
const LOCAL_PROBE_CONFIG_VERSIONS_KEY = 'oneall.probeConfigVersions';
const LOCAL_DETECTIONS_KEY = 'oneall.detectionTasks';
const LOCAL_NOTIFICATIONS_KEY = 'oneall.notifications';

export type ApiRole = 'PlatformAdmin' | 'OpsAdmin' | 'OpsEngineer' | 'Approver' | 'Viewer';

export const apiRoles: ApiRole[] = ['PlatformAdmin', 'OpsAdmin', 'OpsEngineer', 'Approver', 'Viewer'];
export const defaultApiRole: ApiRole = 'OpsAdmin';

export function getCurrentApiRole(): ApiRole {
  if (typeof window === 'undefined') return defaultApiRole;
  const stored = window.localStorage.getItem(ROLE_STORAGE_KEY);
  return apiRoles.includes(stored as ApiRole) ? stored as ApiRole : defaultApiRole;
}

export function setCurrentApiRole(role: ApiRole) {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(ROLE_STORAGE_KEY, role);
  }
}

function nowText() {
  const date = new Date();
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

async function getJson<T>(path: string, role = getCurrentApiRole()): Promise<T> {
  if (!USE_REMOTE_API) throw new Error(`Remote API is not configured: ${path}`);
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'x-oneall-role': role }
  });
  if (!response.ok) throw new Error(`API ${path} failed: ${response.status}`);
  return response.json();
}

async function postJson<T>(path: string, body: unknown, role = getCurrentApiRole()): Promise<T> {
  if (!USE_REMOTE_API) throw new Error(`Remote API is not configured: ${path}`);
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-oneall-role': role },
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(`API ${path} failed: ${response.status}`);
  return response.json();
}

async function putJson<T>(path: string, body: unknown, role = getCurrentApiRole()): Promise<T> {
  if (!USE_REMOTE_API) throw new Error(`Remote API is not configured: ${path}`);
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json', 'x-oneall-role': role },
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(`API ${path} failed: ${response.status}`);
  return response.json();
}

async function deleteJson<T>(path: string, role = getCurrentApiRole()): Promise<T> {
  if (!USE_REMOTE_API) throw new Error(`Remote API is not configured: ${path}`);
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'DELETE',
    headers: { 'x-oneall-role': role }
  });
  if (!response.ok) throw new Error(`API ${path} failed: ${response.status}`);
  return response.json();
}

export type ApiList<T> = { items: T[] };

export type ApiAlertEvent = {
  id: string;
  severity: string;
  title: string;
  asset: string;
  duration: string;
  owner: string;
  notify: string;
  workorder: string;
  status: string;
  protocol?: string;
  strategy?: string;
  strategy_id?: string;
  probe?: string;
  trigger_at?: string;
  updated_at?: string;
  acknowledged_by?: string;
  close_reason?: string;
  evidence?: Array<{ time: string; probe: string; result: string; latency: string; message: string }>;
  timeline?: Array<{ time: string; action: string; actor: string; remark: string }>;
};

export type ApiWorkorder = {
  id: string;
  type: string;
  title: string;
  applicant: string;
  assignee: string;
  status: string;
  sla: string;
  related_object?: string;
  relatedAlertId?: string;
  request_data?: WorkorderRequestData;
  strategy_id?: string;
  approval_records?: WorkorderApprovalRecord[];
};

export type WorkorderApprovalRecord = {
  step: string;
  actor: string;
  result: string;
  time: string;
  remark?: string;
};

export type WorkorderRequestData = {
  target: string;
  systemName: string;
  networkType: string;
  owner: string;
  alertContacts: string;
  protocol: string;
  frequencyValue: number;
  frequencyUnit: string;
  probes: string[];
  triggerMode: string;
  failureCount: number;
  windowCount?: number;
  expectedStatusCodes: string;
  timeoutSeconds: number;
  alertSeverity: string;
  recoverySuccessCount: number;
};

export type ApiAssetModel = {
  id: string;
  name: string;
  code: string;
  fields: Array<{ key: string; type: string; label?: string; required?: boolean; editable?: boolean; unique?: boolean; disabled?: boolean }>;
  primary_key?: string;
  status: string;
  created_by: string;
  created_at: string;
};

export type ApiAssetRecord = {
  id: string;
  model_id: string;
  model_code: string;
  name?: string;
  owner?: string;
  environment?: string;
  source?: string;
  created_by?: string;
  created_at?: string;
  updated_at: string;
} & Record<string, unknown>;

export type ApiAssetSyncRun = {
  event_id: string;
  event_type: string;
  producer: string;
  payload: {
    model_id?: string;
    source?: string;
    script?: string;
    script_id?: string;
    script_version?: string;
    count?: number;
    update_count?: number;
    fail_count?: number;
    operator?: string;
    error_type?: 'script' | 'mapping' | 'permission' | 'data' | 'system';
    error_message?: string;
    error_detail?: string;
    suggestion?: string;
    reason?: string;
  };
  created_at: string;
};

export type ApiAssetSyncScriptVersion = {
  id: string;
  version: string;
  script_name: string;
  content_hash: string;
  mapping_hash: string;
  updated_by: string;
  updated_at: string;
};

export type ApiAssetSyncScript = {
  id: string;
  name: string;
  model_id: string;
  script_name: string;
  script_content: string;
  field_mapping: Record<string, string>;
  current_version: string;
  script_versions: ApiAssetSyncScriptVersion[];
  enabled: boolean;
  updated_by: string;
  updated_at: string;
  created_at: string;
};

export type ApiAssetSyncPreview = {
  model_id: string;
  source: string;
  creates: number;
  updates: number;
  deletes: number;
  issues?: string[];
  samples: Array<Record<string, unknown>>;
};

export type ApiAssetSyncResult = {
  model_id: string;
  source: string;
  count: number;
  records: ApiAssetRecord[];
};

export type ApiAuditLog = {
  id: string;
  actor: string;
  action: string;
  object: string;
  result: string;
  created_at: string;
};

export type ApiMonitoringStrategy = {
  id: string;
  name: string;
  scope: string;
  enabled: boolean;
  version: string;
  protocol?: string;
  severity?: string;
  probes?: string[];
  notify_channels?: string[];
  recent_trigger?: string;
  updated_at?: string;
  rule: {
    signal?: { metric?: string };
    condition?: { operator?: string; value?: unknown; consecutive?: number };
  };
  source_workorder_id?: string;
};

export type ApiProbeNode = {
  id: string;
  name: string;
  region: string;
  network_type?: string;
  ip_address?: string;
  capabilities: string[];
  status: string;
  heartbeat_at: string;
  version?: string;
  active_tasks?: number;
  success_rate?: number;
  avg_latency_ms?: number;
  queue_depth?: number;
  executions?: number;
  failed?: number;
  cpu_usage?: number | null;
  memory_usage_mb?: number | null;
  memory_usage_pct?: number | null;
  load_avg?: number | null;
  uptime?: string;
  connection_status?: string;
  config_status?: string;
  gateway_url?: string;
  bootstrap_token_hint?: string;
  registered_at?: string;
  last_config_sync_at?: string;
  agent_config?: {
    heartbeat_interval_seconds: number;
    task_poll_interval_seconds: number;
    max_concurrent_tasks: number;
    enabled_protocols: string[];
    transport: 'https-json' | 'grpc';
  };
};

export type ApiProbeConfigVersion = {
  id: string;
  probe_id: string;
  version: number;
  status: 'published' | 'acknowledged' | 'rolled_back';
  content_hash: string;
  published_at: string;
  acknowledged_at?: string | null;
  rollback_from?: number | null;
  created_by?: string | null;
  config: ApiProbeNode['agent_config'];
};

export type ApiProbeHealthItem = ApiProbeNode & {
  heartbeat_delay_seconds: number | null;
  uptime_seconds?: number | null;
};

export type ApiProbeHealthResponse = {
  items: ApiProbeHealthItem[];
  window: {
    hours: number;
    interval_minutes: number;
  };
};

export type ApiProbeRuntimePayload = {
  probe: ApiProbeNode;
  heartbeat_delay_seconds: number | null;
  tasks: {
    active: number;
    queue_depth: number;
    executed: number;
    failed: number;
  };
  resource_metrics: {
    cpu_usage: number | null;
    memory_usage_mb: number | null;
    memory_usage_pct: number | null;
    load_avg: number | null;
  };
};

export type ApiProbeMetricsHistoryPoint = {
  timestamp: string;
  cpu_usage: number;
  memory_usage_mb: number;
  queue_depth: number;
  active_workers: number;
  tasks_executed: number;
  heartbeats_sent: number;
};

export type ApiProbeMetricsHistoryResponse = {
  from: string;
  to: string;
  points: ApiProbeMetricsHistoryPoint[];
};

export type ApiDetectionTask = {
  id: string;
  type: string;
  target: string;
  probe: string;
  status: string;
  related_asset: string;
  created_at: string;
  claimed_at?: string;
  completed_at?: string;
  claimed_by_probe_id?: string;
  protocol?: string;
  latency_ms?: number;
  message?: string;
  port?: number;
  timeout_seconds?: number;
  certificate_days?: number;
  cmdb_matched?: boolean;
  cmdb_record?: Record<string, unknown> | null;
  metadata?: Record<string, unknown>;
  result_payload?: Record<string, unknown>;
};

export type ApiNotification = {
  id: string;
  target: string;
  title: string;
  status: string;
  created_at: string;
};

export type ApiPermissionCatalog = {
  roles: ApiRole[];
  permissionMatrix: Record<string, Record<ApiRole, string[]>>;
  dataScopeMatrix: Record<ApiRole, Record<string, string>>;
  workorderStatusMeta: Record<string, { tab: string; actions: string[] }>;
};

export function listAlertEvents() {
  return getJson<ApiList<ApiAlertEvent>>('/api/v1/alerts/events')
    .then((remote) => mergeLocalAlerts(remote.items))
    .catch(() => localListAlertEvents());
}

export function listAssetModels() {
  return getJson<ApiList<ApiAssetModel>>('/api/v1/assets/models')
    .then((remote) => mergeLocalAssetModels(remote.items))
    .catch(() => localListAssetModels());
}

export function createAssetModel(input: { id?: string; name: string; code: string; fields?: ApiAssetModel['fields']; primary_key?: string }) {
  return postJson<ApiAssetModel>('/api/v1/assets/models', input).catch(() => localCreateAssetModel(input));
}

export function updateAssetModel(id: string, input: { name?: string; fields?: ApiAssetModel['fields']; primary_key?: string; status?: string }) {
  return putJson<ApiAssetModel>(`/api/v1/assets/models/${encodeURIComponent(id)}`, input).catch(() => localUpdateAssetModel(id, input));
}

export function deleteAssetModel(id: string) {
  return deleteJson<{ id: string; deleted: boolean }>(`/api/v1/assets/models/${encodeURIComponent(id)}`).catch(() => localDeleteAssetModel(id));
}

export function listDeletedAssetModelKeys() {
  return readLocalJson<string[]>(LOCAL_ASSET_MODEL_DELETIONS_KEY, []);
}

export function listAssetRecords(modelId?: string) {
  if (modelId && hasLocalAssetRecords(modelId)) {
    return Promise.resolve(localListAssetRecords(modelId));
  }
  return getJson<ApiList<ApiAssetRecord>>(`/api/v1/assets/records/query${modelId ? `?model_id=${encodeURIComponent(modelId)}` : ''}`).catch(() => localListAssetRecords(modelId));
}

export function createAssetRecord(model: { id: string; code: string }, values: Record<string, unknown>) {
  return Promise.resolve(localCreateAssetRecord(model, values));
}

export function updateAssetRecord(modelId: string, recordId: string, values: Record<string, unknown>) {
  return Promise.resolve(localUpdateAssetRecord(modelId, recordId, values));
}

export function deleteAssetRecord(modelId: string, recordId: string) {
  try {
    return Promise.resolve(localDeleteAssetRecord(modelId, recordId));
  } catch (error) {
    return Promise.reject(error);
  }
}

export function listAssetSyncRuns() {
  return getJson<ApiList<ApiAssetSyncRun>>('/api/v1/assets/sync/runs').catch(() => localListAssetSyncRuns());
}

export function listAssetSyncScripts() {
  return getJson<ApiList<ApiAssetSyncScript>>('/api/v1/assets/sync/scripts').catch(() => localListAssetSyncScripts());
}

export function saveAssetSyncScript(input: Omit<ApiAssetSyncScript, 'id' | 'current_version' | 'script_versions' | 'updated_by' | 'updated_at' | 'created_at'> & { id?: string }) {
  return postJson<ApiAssetSyncScript>('/api/v1/assets/sync/scripts', input).catch(() => localSaveAssetSyncScript(input));
}

type AssetSyncInput = {
  source?: string;
  script?: string;
  scriptId?: string;
  scriptVersion?: string;
  mapping?: Record<string, string>;
  model?: ApiAssetModel;
};

type AssetSyncFailureInput = {
  modelId?: string;
  source?: string;
  script?: string;
  scriptId?: string;
  scriptVersion?: string;
  errorType: NonNullable<ApiAssetSyncRun['payload']['error_type']>;
  errorMessage: string;
  errorDetail?: string;
  suggestion?: string;
};

export function previewAssetSync(modelId: string, input: AssetSyncInput = {}) {
  if (findLocalAssetModel(modelId)) {
    return Promise.resolve(localPreviewAssetSync(modelId, input));
  }
  return postJson<ApiAssetSyncPreview>(`/api/v1/assets/models/${encodeURIComponent(modelId)}/sync/preview`, input).catch(() => localPreviewAssetSync(modelId, input));
}

export function runAssetSync(modelId: string, input: AssetSyncInput = {}) {
  if (findLocalAssetModel(modelId)) {
    return Promise.resolve(localRunAssetSync(modelId, input));
  }
  return postJson<ApiAssetSyncResult>(`/api/v1/assets/models/${encodeURIComponent(modelId)}/sync`, input).catch(() => localRunAssetSync(modelId, input));
}

export function recordAssetSyncFailure(input: AssetSyncFailureInput) {
  return postJson<ApiAssetSyncRun>('/api/v1/assets/sync/runs/failure', input).catch(() => localRecordAssetSyncFailure(input));
}

export function validateCmdbDomain(domain: string) {
  return getJson<{ domain: string; matched: boolean; model_id: string | null; asset_id: string | null; recommendation: string }>(`/api/v1/detection/cmdb/validate?domain=${encodeURIComponent(domain)}`)
    .catch(() => localValidateCmdbDomain(domain));
}

export function listWorkorderRequests() {
  return getJson<ApiList<ApiWorkorder>>('/api/v1/workorders/requests')
    .then((remote) => mergeLocalWorkorders(remote.items))
    .catch(() => localListWorkorders());
}

export function createWorkorderRequest(input: { type: string; title: string; related_object?: string; relatedAlertId?: string; request_data?: WorkorderRequestData; status?: string }) {
  return postJson<ApiWorkorder>('/api/v1/workorders/requests', input).catch(() => localCreateWorkorder(input));
}

export function createWorkorderFromAlert(alert: ApiAlertEvent) {
  if (findLocalAlert(alert.id)) return Promise.resolve(localCreateWorkorderFromAlert(alert));
  return postJson<ApiWorkorder>('/api/v1/workorders/requests', {
    type: '告警处理',
    title: `处理 ${alert.title}`,
    related_object: alert.asset,
    relatedAlertId: alert.id
  }).catch(() => localCreateWorkorderFromAlert(alert));
}

export function updateWorkorderRequest(id: string, input: { type?: string; title?: string; related_object?: string; request_data?: WorkorderRequestData; status?: string; remark?: string }) {
  return postJson<ApiWorkorder>(`/api/v1/workorders/requests/${id}`, input).catch(() => localUpdateWorkorder(id, input));
}

export function deleteWorkorderRequest(id: string) {
  return postJson<{ id: string }>(`/api/v1/workorders/requests/${id}/delete`, {}).catch(() => localDeleteWorkorder(id));
}

export function approveWorkorder(id: string) {
  return postJson<ApiWorkorder>(`/api/v1/workorders/requests/${id}/approve`, {}).catch(() => localTransitionWorkorder(id, 'approved'));
}

export function rejectWorkorder(id: string, reason = '不符合申请条件') {
  return postJson<ApiWorkorder>(`/api/v1/workorders/requests/${id}/reject`, { reason }).catch(() => localTransitionWorkorder(id, 'rejected', reason));
}

export function withdrawWorkorder(id: string, reason = '申请人撤回') {
  return postJson<ApiWorkorder>(`/api/v1/workorders/requests/${id}/withdraw`, { reason }).catch(() => localTransitionWorkorder(id, 'withdrawn', reason));
}

export function executeWorkorder(id: string) {
  if (findLocalWorkorder(id)) return Promise.resolve(localTransitionWorkorder(id, 'executing'));
  return postJson<{ items: ApiWorkorder[] }>('/api/v1/workorders/requests/batch', { ids: [id], action: 'execute' })
    .then((data) => data.items[0])
    .catch(() => localTransitionWorkorder(id, 'executing'));
}

export function completeWorkorder(id: string) {
  if (findLocalWorkorder(id)) return Promise.resolve(localTransitionWorkorder(id, 'completed'));
  return postJson<{ items: ApiWorkorder[] }>('/api/v1/workorders/requests/batch', { ids: [id], action: 'complete' })
    .then((data) => data.items[0])
    .catch(() => localTransitionWorkorder(id, 'completed'));
}

export function acknowledgeAlertEvent(id: string) {
  if (findLocalAlert(id)) return Promise.resolve(localAcknowledgeAlert(id));
  return postJson<{ items: ApiAlertEvent[] }>('/api/v1/alerts/events/batch', { ids: [id], action: 'acknowledge' })
    .then((data) => data.items[0])
    .catch(() => localAcknowledgeAlert(id));
}

export function closeAlertEvent(id: string, reason = '人工确认恢复') {
  if (findLocalAlert(id)) return Promise.resolve(localCloseAlert(id, reason));
  return postJson<{ items: ApiAlertEvent[] }>('/api/v1/alerts/events/batch', { ids: [id], action: 'close', reason })
    .then((data) => data.items[0])
    .catch(() => localCloseAlert(id, reason));
}

export function listAuditLogs() {
  return getJson<ApiList<ApiAuditLog>>('/api/v1/settings/audit-logs').catch(() => localListAuditLogs());
}

export function listMonitoringStrategies() {
  return getJson<ApiList<ApiMonitoringStrategy>>('/api/v1/monitoring/strategies')
    .then((remote) => mergeLocalStrategies(remote.items))
    .catch(() => localListStrategies());
}

export function createMonitoringStrategy(input: { name: string; scope: string; enabled?: boolean; rule?: ApiMonitoringStrategy['rule']; source_workorder_id?: string }) {
  const body = {
    ...input,
    rule: input.rule ?? { scope: { asset_model: input.scope }, signal: { metric: 'http_status', source: 'probe_result' }, condition: { operator: 'not_in', value: [200, 301, 302], consecutive: 3 }, severity: 'critical', actions: { notify_channels: ['site'], create_workorder: true } }
  };
  return postJson<ApiMonitoringStrategy>('/api/v1/monitoring/strategies', body).catch(() => localCreateStrategy(input));
}

export function toggleMonitoringStrategy(id: string, enabled: boolean) {
  if (findLocalStrategy(id)) return Promise.resolve(localToggleStrategy(id, enabled));
  return postJson<{ items: ApiMonitoringStrategy[] }>('/api/v1/monitoring/strategies/batch', { ids: [id], action: enabled ? 'enable' : 'disable' })
    .then((data) => data.items[0])
    .catch(() => localToggleStrategy(id, enabled));
}

export function deleteMonitoringStrategy(id: string) {
  if (findLocalStrategy(id)) return Promise.resolve(localDeleteStrategy(id));
  return postJson<{ id: string }>('/api/v1/monitoring/strategies/delete', { id }).catch(() => localDeleteStrategy(id));
}

export function listProbeNodes() {
  return getJson<ApiList<ApiProbeNode>>('/api/v1/probes/nodes')
    .then((remote) => mergeLocalProbes(remote.items))
    .catch(() => localListProbes());
}

export function listProbeHealth(params?: { hours?: number; interval_minutes?: number }) {
  const query = new URLSearchParams();
  if (params?.hours) query.set('hours', String(params.hours));
  if (params?.interval_minutes) query.set('interval_minutes', String(params.interval_minutes));
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return getJson<ApiProbeHealthResponse>(`/api/v1/probes/nodes/health${suffix}`).catch(() => localListProbeHealth(params));
}

export function getProbeRuntime(id: string) {
  return getJson<ApiProbeRuntimePayload>(`/api/v1/probes/nodes/${encodeURIComponent(id)}/runtime`).catch(() => localGetProbeRuntime(id));
}

export function registerProbeNode(input: { name: string; region: string; capabilities: string[]; network_type?: string; ip_address?: string }) {
  return postJson<ApiProbeNode>('/api/v1/probes/register', input).catch(() => localRegisterProbe(input));
}

export function refreshProbeConfig(id: string) {
  return postJson<ApiProbeNode>(`/api/v1/probes/nodes/${encodeURIComponent(id)}/config/refresh`, {}).catch(() => localRefreshProbeConfig(id));
}

export function retireProbeNode(id: string) {
  return postJson<ApiProbeNode>(`/api/v1/probes/nodes/${encodeURIComponent(id)}/retire`, {}).catch(() => localRetireProbe(id));
}

export function listProbeConfigVersions(id: string) {
  return getJson<ApiList<ApiProbeConfigVersion>>(`/api/v1/probes/nodes/${encodeURIComponent(id)}/config/versions`).catch(() => localListProbeConfigVersions(id));
}

export function listProbeMetricsHistory(id: string, params?: { hours?: number; interval_minutes?: number }) {
  const query = new URLSearchParams();
  if (params?.hours) query.set('hours', String(params.hours));
  if (params?.interval_minutes) query.set('interval_minutes', String(params.interval_minutes));
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return getJson<ApiProbeMetricsHistoryResponse>(`/api/v1/probes/nodes/${encodeURIComponent(id)}/metrics/history${suffix}`).catch(() => localListProbeMetricsHistory(id, params));
}

export function rollbackProbeConfig(id: string, version: number) {
  return postJson<ApiProbeNode>(`/api/v1/probes/nodes/${encodeURIComponent(id)}/config/rollback`, { version }).catch(() => localRollbackProbeConfig(id, version));
}

export function listDetectionTasks() {
  return getJson<ApiList<ApiDetectionTask>>('/api/v1/detection/tasks').catch(() => localListDetections());
}

export function createDetectionTask(input: { type: string; target: string; related_asset?: string; probe?: string; protocol?: string; port?: number; timeout_seconds?: number; metadata?: Record<string, unknown> }) {
  return postJson<ApiDetectionTask>('/api/v1/detection/one-off', input).catch(() => localCreateDetection(input));
}

export function claimProbeTasks(input: { probe_id: string; limit?: number }) {
  return postJson<unknown>('/api/v1/probes/tasks/claim', input)
    .then(normalizeProbeTaskClaimResponse)
    .catch(() => localClaimProbeTasks(input));
}

export function submitProbeTaskResult(taskId: string, input: { probe_id: string; status: 'success' | 'failed'; response_time_ms?: number; status_code?: string; message?: string; metadata?: Record<string, unknown> }) {
  return postJson<ApiDetectionTask>(`/api/v1/probes/tasks/${encodeURIComponent(taskId)}/result`, input)
    .catch(() => localSubmitProbeTaskResult(taskId, input));
}

export function listNotifications() {
  return getJson<ApiList<ApiNotification>>('/api/v1/notifications').catch(() => localListNotifications());
}

export function getPermissionCatalog() {
  return getJson<ApiPermissionCatalog>('/api/v1/settings/permissions/catalog');
}

function canUseLocalStorage() {
  return typeof window !== 'undefined' && Boolean(window.localStorage);
}

function readLocalJson<T>(key: string, fallback: T): T {
  if (!canUseLocalStorage()) return fallback;
  const raw = window.localStorage.getItem(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeLocalJson<T>(key: string, value: T) {
  if (canUseLocalStorage()) {
    window.localStorage.setItem(key, JSON.stringify(value));
  }
}

function nowIso() {
  return new Date().toISOString();
}

function localAudit(action: string, object: string, result = '成功') {
  const rows = readLocalJson<ApiAuditLog[]>(LOCAL_AUDIT_LOGS_KEY, []);
  const nextRows = [
    {
      id: `AUD-local-${Date.now()}`,
      actor: getCurrentApiRole(),
      action,
      object,
      result,
      created_at: nowIso()
    },
    ...rows
  ].slice(0, 50);
  writeLocalJson(LOCAL_AUDIT_LOGS_KEY, nextRows);
}

function localNotify(target: string, title: string, status = '已投递') {
  const rows = readLocalJson<ApiNotification[]>(LOCAL_NOTIFICATIONS_KEY, []);
  const nextRows = [
    {
      id: `NTF-local-${Date.now()}`,
      target,
      title,
      status,
      created_at: nowIso()
    },
    ...rows
  ].slice(0, 50);
  writeLocalJson(LOCAL_NOTIFICATIONS_KEY, nextRows);
}

function defaultAlertEvents(): ApiAlertEvent[] {
  return [
    {
      id: 'ALERT-local-1',
      severity: '致命',
      title: 'api.oneall.internal HTTP 检测连续超时',
      asset: 'api.oneall.internal',
      duration: '18 分钟',
      owner: '张三',
      notify: '已投递',
      workorder: 'WO-local-1',
      status: '处理中',
      protocol: 'HTTP',
      strategy: 'HTTP 可用性',
      strategy_id: 'STR-local-1',
      probe: '上海探针',
      trigger_at: nowText(),
      updated_at: nowText(),
      acknowledged_by: '张三',
      evidence: [
        { time: '09:21:00', probe: '上海探针', result: '失败', latency: '5001ms', message: 'HTTP 请求超时' },
        { time: '09:22:00', probe: '上海探针', result: '失败', latency: '5018ms', message: 'HTTP 请求超时' },
        { time: '09:23:00', probe: '上海探针', result: '失败', latency: '5032ms', message: '触发连续失败规则' }
      ],
      timeline: [
        { time: '09:23', action: '触发告警', actor: '系统', remark: '连续 3 次失败，生成致命告警' },
        { time: '09:24', action: '通知投递', actor: '系统', remark: '站内信、Webhook 已投递' },
        { time: '09:26', action: '事件认领', actor: '张三', remark: '进入处理中' }
      ]
    },
    {
      id: 'ALERT-local-2',
      severity: '严重',
      title: 'www.oneall.internal 证书 7 天后过期',
      asset: 'www.oneall.internal',
      duration: '2 小时',
      owner: '李四',
      notify: '待重试',
      workorder: '-',
      status: '待认领',
      protocol: 'CERTIFICATE',
      strategy: '证书有效期',
      strategy_id: 'STR-local-cert',
      probe: '上海探针',
      trigger_at: nowText(),
      updated_at: nowText(),
      evidence: [
        { time: '10:00:00', probe: '上海探针', result: '失败', latency: '128ms', message: '证书剩余 7 天' }
      ],
      timeline: [
        { time: '10:00', action: '触发告警', actor: '系统', remark: '证书剩余天数低于阈值' },
        { time: '10:01', action: '通知投递', actor: '系统', remark: 'Webhook 待重试' }
      ]
    }
  ];
}

function localListAlertEvents(): ApiList<ApiAlertEvent> {
  const rows = normalizeAlertEvents(readLocalJson<ApiAlertEvent[]>(LOCAL_ALERTS_KEY, defaultAlertEvents()));
  writeLocalJson(LOCAL_ALERTS_KEY, rows);
  return { items: rows };
}

function normalizeAlertEvents(rows: ApiAlertEvent[]): ApiAlertEvent[] {
  const defaults = defaultAlertEvents();
  return rows.map((row) => {
    const fallback = defaults.find((item) => item.id === row.id) ?? defaults[0];
    const severity = row.severity === 'P0' ? '致命' : row.severity === 'P1' ? '严重' : row.severity === 'P2' ? '预警' : row.severity;
    return {
      ...fallback,
      ...row,
      severity,
      protocol: row.protocol ?? fallback.protocol,
      strategy: row.strategy ?? fallback.strategy,
      strategy_id: row.strategy_id ?? fallback.strategy_id,
      probe: row.probe ?? fallback.probe,
      trigger_at: row.trigger_at ?? fallback.trigger_at,
      updated_at: row.updated_at ?? fallback.updated_at,
      evidence: row.evidence?.length ? row.evidence : fallback.evidence,
      timeline: row.timeline?.length ? row.timeline : fallback.timeline
    };
  });
}

function mergeLocalAlerts(remoteItems: ApiAlertEvent[]): ApiList<ApiAlertEvent> {
  const localItems = readLocalJson<ApiAlertEvent[]>(LOCAL_ALERTS_KEY, []);
  const remoteIds = new Set(remoteItems.map((item) => item.id));
  return { items: [...localItems.filter((item) => !remoteIds.has(item.id)), ...remoteItems] };
}

function localAcknowledgeAlert(id: string): ApiAlertEvent {
  const rows = localListAlertEvents().items;
  const index = rows.findIndex((row) => row.id === id);
  if (index < 0) throw new Error(`Local alert not found: ${id}`);
  const current = rows[index];
  const next = {
    ...current,
    status: current.status === '已恢复' ? current.status : '处理中',
    acknowledged_by: getCurrentApiRole(),
    updated_at: nowText(),
    timeline: [
      ...(current.timeline ?? []),
      { time: nowText(), action: '事件认领', actor: getCurrentApiRole(), remark: '告警进入处理中' }
    ]
  };
  const nextRows = [...rows];
  nextRows[index] = next;
  writeLocalJson(LOCAL_ALERTS_KEY, nextRows);
  localAudit('认领告警', id);
  localNotify(next.owner, `告警已认领：${next.title}`);
  return next;
}

function localCloseAlert(id: string, reason: string): ApiAlertEvent {
  const rows = localListAlertEvents().items;
  const index = rows.findIndex((row) => row.id === id);
  if (index < 0) throw new Error(`Local alert not found: ${id}`);
  const current = rows[index];
  const next = {
    ...current,
    status: '已恢复',
    duration: '已关闭',
    close_reason: reason,
    updated_at: nowText(),
    timeline: [
      ...(current.timeline ?? []),
      { time: nowText(), action: '关闭告警', actor: getCurrentApiRole(), remark: reason }
    ]
  };
  const nextRows = [...rows];
  nextRows[index] = next;
  writeLocalJson(LOCAL_ALERTS_KEY, nextRows);
  localAudit('关闭告警', id);
  localNotify(next.owner, `告警已关闭：${next.title}`);
  return next;
}

function findLocalAlert(id: string) {
  return readLocalJson<ApiAlertEvent[]>(LOCAL_ALERTS_KEY, defaultAlertEvents()).some((row) => row.id === id);
}

function defaultWorkorders(): ApiWorkorder[] {
  return [
    {
      id: 'WO-local-1',
      type: '拨测监控申请',
      title: '新增 api.oneall.internal HTTP 监控',
      applicant: '张三',
      assignee: '李四',
      status: 'submitted',
      sla: '3h 20m',
      related_object: 'api.oneall.internal',
      relatedAlertId: 'ALERT-local-1',
      request_data: {
        target: 'api.oneall.internal',
        systemName: '支付业务',
        networkType: '互联网',
        owner: '张三',
        alertContacts: '00001',
        protocol: 'HTTP',
        frequencyValue: 1,
        frequencyUnit: '分钟',
        probes: ['上海探针'],
        triggerMode: 'consecutive',
        failureCount: 3,
        expectedStatusCodes: '200,204',
        timeoutSeconds: 5,
        alertSeverity: '严重',
        recoverySuccessCount: 2
      }
    },
    { id: 'WO-local-2', type: '告警处理', title: 'pay DNS 解析异常处理', applicant: '系统', assignee: '王五', status: 'executing', sla: '42m', related_object: 'pay.oneall.internal' }
  ];
}

function localListWorkorders(): ApiList<ApiWorkorder> {
  const rows = readLocalJson<ApiWorkorder[]>(LOCAL_WORKORDERS_KEY, defaultWorkorders());
  writeLocalJson(LOCAL_WORKORDERS_KEY, rows);
  return { items: rows };
}

function mergeLocalWorkorders(remoteItems: ApiWorkorder[]): ApiList<ApiWorkorder> {
  const localItems = readLocalJson<ApiWorkorder[]>(LOCAL_WORKORDERS_KEY, []);
  const remoteIds = new Set(remoteItems.map((item) => item.id));
  return { items: [...localItems.filter((item) => !remoteIds.has(item.id)), ...remoteItems] };
}

function localCreateWorkorder(input: { type: string; title: string; related_object?: string; relatedAlertId?: string; request_data?: WorkorderRequestData; status?: string }): ApiWorkorder {
  const rows = localListWorkorders().items;
  const status = input.status ?? 'submitted';
  const row: ApiWorkorder = {
    id: `WO-local-${Date.now()}`,
    type: input.type,
    title: input.title,
    applicant: getCurrentApiRole(),
    assignee: input.type.includes('审批') ? 'Approver' : 'OpsAdmin',
    status,
    sla: '4h',
    related_object: input.related_object,
    relatedAlertId: input.relatedAlertId,
    request_data: input.request_data,
    approval_records: [
      {
        step: status === 'draft' ? '保存草稿' : '提交申请',
        actor: getCurrentApiRole(),
        result: status === 'draft' ? '草稿' : '已提交',
        time: nowText(),
        remark: status === 'draft' ? '暂未进入审批' : '等待业务审批'
      }
    ]
  };
  writeLocalJson(LOCAL_WORKORDERS_KEY, [row, ...rows]);
  localAudit(status === 'draft' ? '保存工单草稿' : '提交工单', row.id);
  if (status !== 'draft') {
    localNotify(row.assignee, `待处理工单：${row.title}`);
  }
  return row;
}

function localCreateWorkorderFromAlert(alert: ApiAlertEvent): ApiWorkorder {
  const workorder = localCreateWorkorder({
    type: '告警处理',
    title: `处理 ${alert.title}`,
    related_object: alert.asset,
    relatedAlertId: alert.id
  });
  const alerts = localListAlertEvents().items;
  const index = alerts.findIndex((item) => item.id === alert.id);
  if (index >= 0) {
    const current = alerts[index];
    const nextAlerts = [...alerts];
    nextAlerts[index] = {
      ...current,
      status: current.status === '已恢复' ? current.status : '处理中',
      workorder: workorder.id,
      updated_at: nowText(),
      timeline: [
        ...(current.timeline ?? []),
        { time: nowText(), action: '创建工单', actor: getCurrentApiRole(), remark: `已关联 ${workorder.id}` }
      ]
    };
    writeLocalJson(LOCAL_ALERTS_KEY, nextAlerts);
  }
  localAudit('告警转工单', `${alert.id} -> ${workorder.id}`);
  return workorder;
}

function localUpdateWorkorder(id: string, input: { type?: string; title?: string; related_object?: string; request_data?: WorkorderRequestData; status?: string; remark?: string }): ApiWorkorder {
  const rows = localListWorkorders().items;
  const index = rows.findIndex((row) => row.id === id);
  if (index < 0) throw new Error(`Local workorder not found: ${id}`);
  const current = rows[index];
  const status = input.status ?? current.status;
  const record = buildWorkorderUpdateRecord(current, status, input.remark);
  const patch: Omit<typeof input, 'remark'> = { ...input };
  delete (patch as typeof input).remark;
  const next: ApiWorkorder = {
    ...current,
    ...patch,
    status,
    approval_records: record ? [...(current.approval_records ?? []), record] : current.approval_records
  };
  const nextRows = [...rows];
  nextRows[index] = next;
  writeLocalJson(LOCAL_WORKORDERS_KEY, nextRows);
  localAudit(status === 'draft' ? '更新工单草稿' : '提交工单草稿', id);
  if (current.status === 'draft' && status === 'submitted') {
    localNotify(next.assignee, `待处理工单：${next.title}`);
  }
  return next;
}

function buildWorkorderUpdateRecord(row: ApiWorkorder, status: string, remark?: string): WorkorderApprovalRecord | null {
  if (status === 'draft') {
    return { step: '更新草稿', actor: getCurrentApiRole(), result: '草稿', time: nowText(), remark: '草稿内容已更新' };
  }
  if (status === 'submitted') {
    return {
      step: row.status === 'draft' ? '提交申请' : '重新提交',
      actor: getCurrentApiRole(),
      result: '已提交',
      time: nowText(),
      remark: row.status === 'draft' ? '草稿已提交，等待业务审批' : '申请已重新提交，等待业务审批'
    };
  }
  if (status === 'failed') {
    return { step: '平台执行', actor: getCurrentApiRole(), result: '执行失败', time: nowText(), remark: remark || '策略下发失败' };
  }
  return null;
}

function localDeleteWorkorder(id: string) {
  const rows = localListWorkorders().items;
  const target = rows.find((row) => row.id === id);
  if (!target) throw new Error(`Local workorder not found: ${id}`);
  if (target.status !== 'draft') throw new Error('Only draft workorders can be deleted');
  writeLocalJson(LOCAL_WORKORDERS_KEY, rows.filter((row) => row.id !== id));
  localAudit('删除工单草稿', id);
  return { id };
}

function localTransitionWorkorder(id: string, status: string, remark?: string): ApiWorkorder {
  const rows = localListWorkorders().items;
  const index = rows.findIndex((row) => row.id === id);
  if (index < 0) throw new Error(`Local workorder not found: ${id}`);
  const current = rows[index];
  const nextRecord = buildWorkorderTransitionRecord(current, status, remark);
  const next = {
    ...current,
    status,
    approval_records: nextRecord ? [...(current.approval_records ?? []), nextRecord] : current.approval_records
  };
  const nextRows = [...rows];
  nextRows[index] = next;
  writeLocalJson(LOCAL_WORKORDERS_KEY, nextRows);
  localAudit(`工单状态变更为 ${status}`, id);
  localNotify(next.applicant, `工单状态更新：${next.title} / ${status}`);
  return next;
}

function buildWorkorderTransitionRecord(row: ApiWorkorder, status: string, remark?: string): WorkorderApprovalRecord | null {
  if (status === 'approved') {
    return { step: '业务审批', actor: getCurrentApiRole(), result: '已通过', time: nowText(), remark: '审批通过，准备下发策略' };
  }
  if (status === 'rejected') {
    return { step: '业务审批', actor: getCurrentApiRole(), result: '已驳回', time: nowText(), remark: remark || '不符合申请条件' };
  }
  if (status === 'withdrawn') {
    return { step: '撤回申请', actor: getCurrentApiRole(), result: '已撤回', time: nowText(), remark: remark || '申请人撤回' };
  }
  if (status === 'executing') {
    return { step: '平台执行', actor: getCurrentApiRole(), result: '执行中', time: nowText(), remark: '策略下发中' };
  }
  if (status === 'completed') {
    return { step: '完成审计', actor: getCurrentApiRole(), result: '已完成', time: nowText(), remark: row.strategy_id ? `已关联策略 ${row.strategy_id}` : '处理完成' };
  }
  return null;
}

function findLocalWorkorder(id: string) {
  return readLocalJson<ApiWorkorder[]>(LOCAL_WORKORDERS_KEY, defaultWorkorders()).some((row) => row.id === id);
}

function defaultStrategies(): ApiMonitoringStrategy[] {
  return [
    {
      id: 'STR-local-1',
      name: 'HTTP 可用性',
      scope: '支付域名服务模型 / prod',
      enabled: true,
      version: 'v18',
      protocol: 'HTTP',
      severity: '严重',
      probes: ['上海探针'],
      notify_channels: ['站内信', 'Webhook'],
      recent_trigger: '18 分钟前',
      updated_at: nowText(),
      rule: { signal: { metric: 'http_status' }, condition: { operator: 'not_in', value: [200, 301, 302], consecutive: 3 } }
    }
  ];
}

function localListStrategies(): ApiList<ApiMonitoringStrategy> {
  const rows = readLocalJson<ApiMonitoringStrategy[]>(LOCAL_STRATEGIES_KEY, defaultStrategies());
  writeLocalJson(LOCAL_STRATEGIES_KEY, rows);
  return { items: rows };
}

function mergeLocalStrategies(remoteItems: ApiMonitoringStrategy[]): ApiList<ApiMonitoringStrategy> {
  const localItems = readLocalJson<ApiMonitoringStrategy[]>(LOCAL_STRATEGIES_KEY, []);
  const remoteIds = new Set(remoteItems.map((item) => item.id));
  return { items: [...localItems.filter((item) => !remoteIds.has(item.id)), ...remoteItems] };
}

function findLocalStrategy(id: string) {
  return readLocalJson<ApiMonitoringStrategy[]>(LOCAL_STRATEGIES_KEY, defaultStrategies()).some((row) => row.id === id);
}

function localCreateStrategy(input: { name: string; scope: string; enabled?: boolean; rule?: ApiMonitoringStrategy['rule']; source_workorder_id?: string }): ApiMonitoringStrategy {
  const rows = localListStrategies().items;
  const row: ApiMonitoringStrategy = {
    id: `STR-local-${Date.now()}`,
    name: input.name,
    scope: input.scope,
    enabled: input.enabled ?? true,
    version: 'v1',
    protocol: input.rule?.signal?.metric === 'certificate_expire_days' ? 'CERTIFICATE' : 'HTTP',
    severity: '严重',
    probes: ['上海探针'],
    notify_channels: ['站内信'],
    recent_trigger: '-',
    updated_at: nowText(),
    rule: input.rule ?? { signal: { metric: 'http_status' }, condition: { operator: 'not_in', value: [200, 301, 302], consecutive: 3 } },
    source_workorder_id: input.source_workorder_id
  };
  writeLocalJson(LOCAL_STRATEGIES_KEY, [row, ...rows]);
  if (input.source_workorder_id) {
    const workorders = localListWorkorders().items;
    const index = workorders.findIndex((item) => item.id === input.source_workorder_id);
    if (index >= 0) {
      const nextWorkorders = [...workorders];
      const current = nextWorkorders[index];
      nextWorkorders[index] = {
        ...current,
        status: 'completed',
        strategy_id: row.id,
        approval_records: [
          ...(current.approval_records ?? []),
          { step: '平台执行', actor: getCurrentApiRole(), result: '已下发', time: nowText(), remark: `生成策略 ${row.id}` },
          { step: '完成审计', actor: getCurrentApiRole(), result: '已完成', time: nowText(), remark: '监控策略已生效' }
        ]
      };
      writeLocalJson(LOCAL_WORKORDERS_KEY, nextWorkorders);
      localAudit('工单策略下发完成', input.source_workorder_id);
    }
  }
  localAudit('创建监控策略', row.id);
  return row;
}

function localToggleStrategy(id: string, enabled: boolean): ApiMonitoringStrategy {
  const rows = localListStrategies().items;
  const index = rows.findIndex((row) => row.id === id);
  if (index < 0) throw new Error(`Local strategy not found: ${id}`);
  const next = { ...rows[index], enabled, version: `v${Number(rows[index].version.replace(/^v/, '')) + 1 || 1}`, updated_at: nowText() };
  const nextRows = [...rows];
  nextRows[index] = next;
  writeLocalJson(LOCAL_STRATEGIES_KEY, nextRows);
  localAudit(enabled ? '启用监控策略' : '停用监控策略', id);
  return next;
}

function localDeleteStrategy(id: string) {
  const rows = localListStrategies().items;
  const target = rows.find((row) => row.id === id);
  if (!target) throw new Error(`Local strategy not found: ${id}`);
  writeLocalJson(LOCAL_STRATEGIES_KEY, rows.filter((row) => row.id !== id));
  localAudit('删除监控策略', id);
  return { id };
}

function defaultProbes(): ApiProbeNode[] {
  const registeredAt = '2026-06-01 09:30';
  return [
    { id: 'PROBE-local-1', name: 'probe-sh-01', region: '上海', network_type: '互联网', ip_address: '10.10.1.21', capabilities: ['HTTP', 'TCP', 'DNS', 'CERTIFICATE'], status: 'online', heartbeat_at: nowIso(), version: 'v18', active_tasks: 2, success_rate: 99.3, avg_latency_ms: 41, queue_depth: 0, executions: 1286, failed: 9, cpu_usage: 32, memory_usage_mb: 612, memory_usage_pct: 41, load_avg: 0.72, uptime: '18 天', connection_status: 'connected', config_status: 'acknowledged', registered_at: registeredAt, last_config_sync_at: nowText(), ...makeProbeAccessDefaults('PROBE-local-1', ['HTTP', 'TCP', 'DNS', 'CERTIFICATE']) },
    { id: 'PROBE-local-2', name: 'probe-bj-01', region: '北京', network_type: '专线', ip_address: '10.20.2.18', capabilities: ['HTTP', 'TCP', 'CERTIFICATE'], status: 'online', heartbeat_at: nowIso(), version: 'v18', active_tasks: 1, success_rate: 98.1, avg_latency_ms: 58, queue_depth: 1, executions: 934, failed: 18, cpu_usage: 27, memory_usage_mb: 584, memory_usage_pct: 38, load_avg: 0.51, uptime: '11 天', connection_status: 'connected', config_status: 'acknowledged', registered_at: registeredAt, last_config_sync_at: nowText(), ...makeProbeAccessDefaults('PROBE-local-2', ['HTTP', 'TCP', 'CERTIFICATE']) },
    { id: 'PROBE-local-3', name: 'probe-gz-01', region: '广州', network_type: '互联网', ip_address: '10.30.3.9', capabilities: ['HTTP', 'DNS'], status: 'offline', heartbeat_at: '2026-06-12 09:10:00', version: 'v17', active_tasks: 0, success_rate: 91.5, avg_latency_ms: 86, queue_depth: 4, executions: 413, failed: 35, cpu_usage: null, memory_usage_mb: null, memory_usage_pct: null, load_avg: null, uptime: '3 天', connection_status: 'disconnected', config_status: 'pending', registered_at: registeredAt, last_config_sync_at: '2026-06-12 09:00', ...makeProbeAccessDefaults('PROBE-local-3', ['HTTP', 'DNS']) }
  ];
}

function buildDefaultAgentConfig(capabilities: string[]) {
  return {
    heartbeat_interval_seconds: 30,
    task_poll_interval_seconds: 5,
    max_concurrent_tasks: 8,
    enabled_protocols: normalizeProbeCapabilityList(capabilities),
    transport: 'https-json' as const
  };
}

function normalizeProbeCapabilityList(capabilities: string[]) {
  return Array.from(new Set(capabilities.map((item) => item.trim().toUpperCase()).filter(Boolean)));
}

function makeProbeAccessDefaults(id: string, capabilities: string[]) {
  const tokenSeed = id.replace(/[^a-zA-Z0-9]/g, '').slice(-8).padStart(8, '0');
  return {
    gateway_url: `${API_BASE}/api/v1/probes/tasks/claim`,
    bootstrap_token_hint: `oa_probe_${tokenSeed}****`,
    agent_config: buildDefaultAgentConfig(capabilities)
  };
}

function normalizeProbeNode(item: ApiProbeNode, fallback?: ApiProbeNode): ApiProbeNode {
  const capabilities = item.capabilities?.length ? normalizeProbeCapabilityList(item.capabilities) : fallback?.capabilities ?? [];
  return {
    ...(fallback ?? {}),
    ...item,
    network_type: item.network_type || fallback?.network_type || '互联网',
    ip_address: item.ip_address || fallback?.ip_address || '',
    capabilities,
    version: item.version || fallback?.version || 'v1',
    active_tasks: item.active_tasks ?? fallback?.active_tasks ?? 0,
    success_rate: item.success_rate ?? fallback?.success_rate ?? 100,
    avg_latency_ms: item.avg_latency_ms ?? fallback?.avg_latency_ms ?? 0,
    queue_depth: item.queue_depth ?? fallback?.queue_depth ?? 0,
    executions: item.executions ?? fallback?.executions ?? 0,
    failed: item.failed ?? fallback?.failed ?? 0,
    cpu_usage: item.cpu_usage ?? fallback?.cpu_usage ?? null,
    memory_usage_mb: item.memory_usage_mb ?? fallback?.memory_usage_mb ?? null,
    memory_usage_pct: item.memory_usage_pct ?? fallback?.memory_usage_pct ?? null,
    load_avg: item.load_avg ?? fallback?.load_avg ?? null,
    uptime: item.uptime || fallback?.uptime || '-',
    connection_status: item.connection_status || fallback?.connection_status || 'connected',
    config_status: item.config_status || fallback?.config_status || 'acknowledged',
    registered_at: item.registered_at || fallback?.registered_at || nowText(),
    last_config_sync_at: item.last_config_sync_at || fallback?.last_config_sync_at || '-',
    ...makeProbeAccessDefaults(item.id || fallback?.id || 'PROBE-local', capabilities),
    gateway_url: item.gateway_url || fallback?.gateway_url || makeProbeAccessDefaults(item.id || fallback?.id || 'PROBE-local', capabilities).gateway_url,
    bootstrap_token_hint: item.bootstrap_token_hint || fallback?.bootstrap_token_hint || makeProbeAccessDefaults(item.id || fallback?.id || 'PROBE-local', capabilities).bootstrap_token_hint,
    agent_config: item.agent_config || fallback?.agent_config || buildDefaultAgentConfig(capabilities)
  };
}

function localListProbes(): ApiList<ApiProbeNode> {
  const defaults = defaultProbes();
  const defaultById = new Map(defaults.map((item) => [item.id, item]));
  const storedRows = readLocalJson<ApiProbeNode[]>(LOCAL_PROBES_KEY, []);
  const storedIds = new Set(storedRows.map((item) => item.id));
  const rows = [
    ...storedRows.map((item) => normalizeProbeNode(item, defaultById.get(item.id))),
    ...defaults.filter((item) => !storedIds.has(item.id))
  ];
  writeLocalJson(LOCAL_PROBES_KEY, rows);
  return { items: rows };
}

function mergeLocalProbes(remoteItems: ApiProbeNode[]): ApiList<ApiProbeNode> {
  const localItems = readLocalJson<ApiProbeNode[]>(LOCAL_PROBES_KEY, []);
  const remoteIds = new Set(remoteItems.map((item) => item.id));
  return { items: [...localItems.filter((item) => !remoteIds.has(item.id)).map((item) => normalizeProbeNode(item)), ...remoteItems.map((item) => normalizeProbeNode(item))] };
}

function parseLocalDateTime(value?: string) {
  if (!value || value === '-') return null;
  const parsed = Date.parse(value.includes('T') ? value : value.replace(' ', 'T'));
  return Number.isFinite(parsed) ? parsed : null;
}

function secondsSince(value?: string) {
  const parsed = parseLocalDateTime(value);
  if (!parsed) return null;
  return Math.max(0, Math.floor((Date.now() - parsed) / 1000));
}

function parseUptimeSeconds(value?: string) {
  if (!value || value === '-') return null;
  const matched = value.match(/(\d+)\s*天/);
  return matched ? Number(matched[1]) * 24 * 60 * 60 : null;
}

function localGetProbeRuntime(id: string): ApiProbeRuntimePayload {
  const probe = findLocalProbeByIdOrName(id);
  if (!probe) throw new Error(`Local probe not found: ${id}`);
  return {
    probe,
    heartbeat_delay_seconds: secondsSince(probe.heartbeat_at),
    tasks: {
      active: probe.active_tasks ?? 0,
      queue_depth: probe.queue_depth ?? 0,
      executed: probe.executions ?? 0,
      failed: probe.failed ?? 0
    },
    resource_metrics: {
      cpu_usage: probe.cpu_usage ?? null,
      memory_usage_mb: probe.memory_usage_mb ?? null,
      memory_usage_pct: probe.memory_usage_pct ?? null,
      load_avg: probe.load_avg ?? null
    }
  };
}

function localListProbeHealth(params?: { hours?: number; interval_minutes?: number }): ApiProbeHealthResponse {
  return {
    items: localListProbes().items.map((probe) => ({
      ...probe,
      heartbeat_delay_seconds: secondsSince(probe.heartbeat_at),
      uptime_seconds: parseUptimeSeconds(probe.uptime)
    })),
    window: {
      hours: params?.hours ?? 6,
      interval_minutes: params?.interval_minutes ?? 5
    }
  };
}

function localListProbeMetricsHistory(id: string, params?: { hours?: number; interval_minutes?: number }): ApiProbeMetricsHistoryResponse {
  const probe = findLocalProbeByIdOrName(id);
  if (!probe) throw new Error(`Local probe not found: ${id}`);
  const hours = params?.hours ?? 6;
  const intervalMinutes = params?.interval_minutes ?? 60;
  const pointCount = Math.min(12, Math.max(4, Math.ceil((hours * 60) / intervalMinutes)));
  const now = Date.now();
  const baseCpu = probe.cpu_usage ?? 0;
  const baseMemory = probe.memory_usage_mb ?? 0;
  const baseQueue = probe.queue_depth ?? 0;
  const baseActive = probe.active_tasks ?? 0;
  const baseExecuted = probe.executions ?? 0;
  const points = Array.from({ length: pointCount }, (_, index) => {
    const reverseIndex = pointCount - index - 1;
    const offset = reverseIndex - Math.floor(pointCount / 2);
    return {
      timestamp: new Date(now - reverseIndex * intervalMinutes * 60 * 1000).toISOString(),
      cpu_usage: Number(Math.max(0, baseCpu + offset * 1.7).toFixed(1)),
      memory_usage_mb: Math.max(0, Math.round(baseMemory + offset * 12)),
      queue_depth: Math.max(0, baseQueue + (index % 3 === 0 ? 1 : 0)),
      active_workers: Math.max(0, baseActive + (index % 2)),
      tasks_executed: Math.max(0, baseExecuted - reverseIndex * 3),
      heartbeats_sent: Math.max(0, 360 - reverseIndex * 4)
    };
  });
  return {
    from: points[0]?.timestamp ?? nowIso(),
    to: points.at(-1)?.timestamp ?? nowIso(),
    points
  };
}

function localRegisterProbe(input: { name: string; region: string; capabilities: string[]; network_type?: string; ip_address?: string }): ApiProbeNode {
  const rows = localListProbes().items;
  const capabilities = normalizeProbeCapabilityList(input.capabilities);
  const id = `PROBE-local-${Date.now()}`;
  const row: ApiProbeNode = {
    ...makeProbeAccessDefaults(id, capabilities),
    id,
    name: input.name,
    region: input.region,
    network_type: input.network_type || '互联网',
    ip_address: input.ip_address || '',
    capabilities,
    status: 'registered',
    heartbeat_at: '-',
    version: 'v1',
    active_tasks: 0,
    success_rate: 100,
    avg_latency_ms: 0,
    queue_depth: 0,
    executions: 0,
    failed: 0,
    cpu_usage: null,
    memory_usage_mb: null,
    memory_usage_pct: null,
    load_avg: null,
    uptime: '待启动',
    connection_status: 'disconnected',
    config_status: 'pending',
    registered_at: nowText(),
    last_config_sync_at: '-'
  };
  writeLocalJson(LOCAL_PROBES_KEY, [row, ...rows]);
  localAudit('注册探针', row.id);
  return row;
}

function bumpProbeVersion(version?: string) {
  const current = Number(String(version || 'v0').replace(/^v/, ''));
  return `v${Number.isFinite(current) ? current + 1 : 1}`;
}

function probeVersionNumber(version?: string) {
  const value = Number(String(version || 'v1').replace(/^v/, ''));
  return Number.isFinite(value) && value > 0 ? value : 1;
}

function hashProbeConfig(config: ApiProbeConfigVersion['config']) {
  const source = JSON.stringify(config ?? {});
  let hash = 0x811c9dc5;
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, '0');
}

function readLocalProbeConfigVersions() {
  return readLocalJson<ApiProbeConfigVersion[]>(LOCAL_PROBE_CONFIG_VERSIONS_KEY, []);
}

function writeLocalProbeConfigVersions(rows: ApiProbeConfigVersion[]) {
  writeLocalJson(LOCAL_PROBE_CONFIG_VERSIONS_KEY, rows);
}

function makeProbeConfigVersion(row: ApiProbeNode, status: ApiProbeConfigVersion['status'] = 'acknowledged', rollbackFrom: number | null = null): ApiProbeConfigVersion {
  const version = probeVersionNumber(row.version);
  const config = row.agent_config || buildDefaultAgentConfig(row.capabilities);
  return {
    id: `${row.id}-config-v${version}`,
    probe_id: row.id,
    version,
    status,
    content_hash: hashProbeConfig(config),
    published_at: row.last_config_sync_at && row.last_config_sync_at !== '-' ? row.last_config_sync_at : nowText(),
    acknowledged_at: status === 'acknowledged' ? nowText() : null,
    rollback_from: rollbackFrom,
    created_by: getCurrentApiRole(),
    config
  };
}

function ensureProbeConfigVersions(row: ApiProbeNode) {
  const rows = readLocalProbeConfigVersions();
  if (rows.some((item) => item.probe_id === row.id)) return rows;
  const initial = makeProbeConfigVersion(row, row.config_status === 'pending' ? 'published' : 'acknowledged');
  const nextRows = [initial, ...rows];
  writeLocalProbeConfigVersions(nextRows);
  return nextRows;
}

function updateLocalProbe(id: string, updater: (row: ApiProbeNode) => ApiProbeNode) {
  const rows = localListProbes().items;
  const index = rows.findIndex((row) => row.id === id);
  if (index < 0) throw new Error(`Local probe not found: ${id}`);
  const nextRows = [...rows];
  nextRows[index] = normalizeProbeNode(updater(rows[index]));
  writeLocalJson(LOCAL_PROBES_KEY, nextRows);
  return nextRows[index];
}

function localRefreshProbeConfig(id: string) {
  const next = updateLocalProbe(id, (row) => ({
    ...row,
    version: bumpProbeVersion(row.version),
    config_status: 'acknowledged',
    last_config_sync_at: nowText(),
    agent_config: buildDefaultAgentConfig(row.capabilities)
  }));
  const versions = readLocalProbeConfigVersions().filter((item) => item.probe_id !== id || item.version !== probeVersionNumber(next.version));
  writeLocalProbeConfigVersions([makeProbeConfigVersion(next), ...versions]);
  localAudit('同步探针配置', id);
  return next;
}

function localRetireProbe(id: string) {
  const next = updateLocalProbe(id, (row) => ({
    ...row,
    status: 'retired',
    connection_status: 'disconnected',
    config_status: 'acknowledged',
    active_tasks: 0,
    queue_depth: 0,
    uptime: row.uptime || '-'
  }));
  localAudit('退役探针', id);
  return next;
}

function localListProbeConfigVersions(id: string): ApiList<ApiProbeConfigVersion> {
  const probe = localListProbes().items.find((row) => row.id === id);
  if (!probe) throw new Error(`Local probe not found: ${id}`);
  const rows = ensureProbeConfigVersions(probe);
  return { items: rows.filter((item) => item.probe_id === id).sort((a, b) => b.version - a.version) };
}

function localRollbackProbeConfig(id: string, version: number) {
  const versions = localListProbeConfigVersions(id).items;
  const target = versions.find((item) => item.version === version);
  if (!target) throw new Error(`Local probe config version not found: ${id} v${version}`);
  const previousVersion = probeVersionNumber(localListProbes().items.find((row) => row.id === id)?.version);
  const nextProbe = updateLocalProbe(id, (row) => ({
    ...row,
    version: `v${target.version}`,
    config_status: 'pending',
    last_config_sync_at: '-',
    agent_config: target.config || buildDefaultAgentConfig(row.capabilities)
  }));
  const rows = readLocalProbeConfigVersions().filter((item) => !(item.probe_id === id && item.version === target.version));
  writeLocalProbeConfigVersions([
    {
      ...target,
      id: `${id}-config-v${target.version}-rollback-${Date.now()}`,
      status: 'published',
      published_at: nowText(),
      acknowledged_at: null,
      rollback_from: previousVersion || null,
      created_by: getCurrentApiRole()
    },
    ...rows
  ]);
  localAudit('回滚探针配置', `${id}@v${version}`);
  return nextProbe;
}

function localListDetections(): ApiList<ApiDetectionTask> {
  return { items: readLocalJson<ApiDetectionTask[]>(LOCAL_DETECTIONS_KEY, []) };
}

function normalizeProbeTaskClaimResponse(response: unknown): ApiList<ApiDetectionTask> {
  if (!response) return { items: [] };
  const maybeList = response as ApiList<ApiDetectionTask>;
  if (Array.isArray(maybeList.items)) return { items: maybeList.items };
  return { items: [response as ApiDetectionTask] };
}

function findLocalProbeByIdOrName(idOrName: string) {
  return localListProbes().items.find((row) => row.id === idOrName || row.name === idOrName);
}

function isProbeDetectionTask(row: ApiDetectionTask, probe: ApiProbeNode) {
  return row.probe === probe.name || row.probe === probe.id || row.claimed_by_probe_id === probe.id || row.metadata?.selected_probe === probe.name;
}

function makeLocalPendingProbeTask(probe: ApiProbeNode): ApiDetectionTask {
  return {
    id: `DET-local-claim-${Date.now()}`,
    type: 'http',
    target: 'https://api.oneall.internal/health',
    probe: probe.name,
    status: 'pending',
    related_asset: 'api.oneall.internal',
    created_at: nowIso(),
    protocol: 'HTTPS',
    timeout_seconds: 10,
    message: '等待探针领取',
    metadata: { selected_probe: probe.name, source: 'local_probe_queue' }
  };
}

function localClaimProbeTasks(input: { probe_id: string; limit?: number }): ApiList<ApiDetectionTask> {
  const probe = findLocalProbeByIdOrName(input.probe_id);
  if (!probe) throw new Error(`Local probe not found: ${input.probe_id}`);
  const limit = Math.min(Math.max(input.limit ?? 1, 1), 10);
  let rows = localListDetections().items;
  const hasOpenTask = rows.some((row) => isProbeDetectionTask(row, probe) && ['pending', 'scheduled', 'running'].includes(row.status));
  if (!hasOpenTask) {
    rows = [makeLocalPendingProbeTask(probe), ...rows];
  }
  const claimIds = new Set(
    rows
      .filter((row) => isProbeDetectionTask(row, probe) && ['pending', 'scheduled'].includes(row.status))
      .slice(0, limit)
      .map((row) => row.id)
  );
  const claimedAt = nowIso();
  const nextRows = rows.map((row) => claimIds.has(row.id) ? {
    ...row,
    status: 'running',
    claimed_at: claimedAt,
    claimed_by_probe_id: probe.id,
    message: '探针已领取，等待回传'
  } : row);
  writeLocalJson(LOCAL_DETECTIONS_KEY, nextRows);
  if (claimIds.size) {
    updateLocalProbe(probe.id, (row) => ({
      ...row,
      active_tasks: (row.active_tasks ?? 0) + claimIds.size,
      queue_depth: Math.max(0, (row.queue_depth ?? 0) - claimIds.size),
      heartbeat_at: nowIso(),
      connection_status: 'connected',
      status: row.status === 'registered' ? 'online' : row.status
    }));
    localAudit('探针领取任务', `${probe.id} x${claimIds.size}`);
  }
  return { items: nextRows.filter((row) => claimIds.has(row.id)) };
}

function localSubmitProbeTaskResult(taskId: string, input: { probe_id: string; status: 'success' | 'failed'; response_time_ms?: number; status_code?: string; message?: string; metadata?: Record<string, unknown> }): ApiDetectionTask {
  const probe = findLocalProbeByIdOrName(input.probe_id);
  if (!probe) throw new Error(`Local probe not found: ${input.probe_id}`);
  const rows = localListDetections().items;
  const task = rows.find((row) => row.id === taskId);
  if (!task) throw new Error(`Local detection task not found: ${taskId}`);
  if (!isProbeDetectionTask(task, probe)) throw new Error(`Task ${taskId} is not assigned to probe ${probe.id}`);
  const responseTime = input.response_time_ms ?? (input.status === 'success' ? probe.avg_latency_ms ?? 80 : 5000);
  const completedAt = nowIso();
  const nextTask: ApiDetectionTask = {
    ...task,
    status: input.status,
    completed_at: completedAt,
    latency_ms: responseTime,
    message: input.message || (input.status === 'success' ? '探针回传成功' : '探针回传失败'),
    result_payload: {
      status_code: input.status_code ?? (input.status === 'success' ? '200' : '504'),
      probe_id: probe.id,
      finished_at: completedAt,
      ...(input.metadata ?? {})
    }
  };
  writeLocalJson(LOCAL_DETECTIONS_KEY, rows.map((row) => row.id === taskId ? nextTask : row));
  updateLocalProbe(probe.id, (row) => {
    const executions = (row.executions ?? 0) + 1;
    const failed = (row.failed ?? 0) + (input.status === 'failed' ? 1 : 0);
    const successRate = executions > 0 ? Number((((executions - failed) / executions) * 100).toFixed(1)) : row.success_rate;
    const avgLatency = Math.round((((row.avg_latency_ms ?? responseTime) * Math.max((row.executions ?? 1) - 1, 0)) + responseTime) / Math.max(row.executions ?? 1, 1));
    return {
      ...row,
      active_tasks: Math.max(0, (row.active_tasks ?? 0) - 1),
      executions,
      failed,
      success_rate: successRate,
      avg_latency_ms: avgLatency,
      heartbeat_at: nowIso(),
      connection_status: 'connected',
      status: input.status === 'failed' ? 'degraded' : row.status === 'registered' ? 'online' : row.status
    };
  });
  localAudit('探针回传结果', taskId);
  if (input.status === 'failed') {
    const alertRows = localListAlertEvents().items;
    const alert: ApiAlertEvent = { id: `ALERT-local-${Date.now()}`, severity: '严重', title: `${nextTask.related_asset} 检测失败`, asset: nextTask.related_asset, duration: '刚刚', owner: getCurrentApiRole(), notify: '已投递', workorder: '-', status: '待认领' };
    writeLocalJson(LOCAL_ALERTS_KEY, [alert, ...alertRows]);
    localNotify(alert.owner, `探针回传失败生成告警：${alert.title}`);
  }
  return nextTask;
}

function localValidateCmdbDomain(domain: string) {
  const host = extractTargetHost(domain);
  const rows = localListAssetRecords().items;
  const matched = rows.find((row) => {
    const candidate = String(row.domain ?? row.hostname ?? row.name ?? '').replace(/^https?:\/\//, '').replace(/\/.*$/, '');
    return candidate === host;
  });
  return {
    domain: host,
    matched: Boolean(matched),
    model_id: matched?.model_id ? String(matched.model_id) : matched ? 'cmdb-domain' : null,
    asset_id: matched?.id ? String(matched.id) : null,
    recommendation: matched ? '已在模型资产中找到匹配记录' : '未找到匹配资产，可先补充模型资产或同步任务'
  };
}

function localCreateDetection(input: { type: string; target: string; related_asset?: string; probe?: string; protocol?: string; port?: number; timeout_seconds?: number; metadata?: Record<string, unknown> }): ApiDetectionTask {
  const rows = localListDetections().items;
  const host = extractTargetHost(input.target);
  const detectionType = input.type || 'http';
  const isFailure = /fail|down|timeout|expired/i.test(input.target);
  const isCmdb = detectionType === 'cmdb' || input.protocol === 'CMDB';
  const isCertificate = detectionType === 'certificate' || input.protocol === 'CERTIFICATE';
  const cmdbResult = isCmdb ? localValidateCmdbDomain(input.target) : null;
  const status = isCmdb ? (cmdbResult?.matched ? 'success' : 'failed') : isFailure ? 'failed' : 'success';
  const task: ApiDetectionTask = {
    id: `DET-local-${Date.now()}`,
    type: detectionType,
    target: input.target,
    probe: input.probe || 'probe-sh-01',
    status,
    related_asset: input.related_asset || host || input.target,
    created_at: nowIso(),
    protocol: input.protocol ?? (isCertificate ? 'CERTIFICATE' : isCmdb ? 'CMDB' : 'HTTPS'),
    latency_ms: isCmdb ? 0 : status === 'failed' ? 5000 + Math.floor(Math.random() * 120) : 80 + Math.floor(Math.random() * 80),
    message: isCmdb ? cmdbResult?.recommendation : isCertificate ? (status === 'success' ? '证书链有效' : '证书检测失败或已过期') : (status === 'success' ? '探针返回成功' : '请求超时或连续失败'),
    port: input.port,
    timeout_seconds: input.timeout_seconds,
    certificate_days: isCertificate ? (status === 'success' ? 27 : -1) : undefined,
    cmdb_matched: cmdbResult?.matched,
    cmdb_record: cmdbResult?.matched ? cmdbResult : null,
    metadata: input.metadata
  };
  writeLocalJson(LOCAL_DETECTIONS_KEY, [task, ...rows]);
  localAudit('执行一次性检测', task.id);
  if (task.status === 'failed' && !isCmdb) {
    const alertRows = localListAlertEvents().items;
    const alert: ApiAlertEvent = { id: `ALERT-local-${Date.now()}`, severity: 'P1', title: `${task.target} 检测失败`, asset: task.related_asset, duration: '刚刚', owner: getCurrentApiRole(), notify: '已投递', workorder: '-', status: '待认领' };
    writeLocalJson(LOCAL_ALERTS_KEY, [alert, ...alertRows]);
    localNotify(alert.owner, `检测失败生成告警：${alert.title}`);
  }
  return task;
}

function localListNotifications(): ApiList<ApiNotification> {
  return { items: readLocalJson<ApiNotification[]>(LOCAL_NOTIFICATIONS_KEY, []) };
}

function normalizeAssetFields(fields?: ApiAssetModel['fields']) {
  const normalized = (fields?.length ? fields : [{ key: 'name', type: 'string', label: '名称' }])
    .map((field) => ({
      key: field.key.trim(),
      type: field.type || 'string',
      label: field.label?.trim() || field.key.trim(),
      required: Boolean(field.required),
      editable: field.editable === false ? false : true,
      unique: Boolean(field.unique),
      disabled: Boolean(field.disabled)
    }))
    .filter((field) => field.key);
  return normalized.length ? normalized : [{ key: 'name', type: 'string', label: '名称', required: false, editable: true, unique: false }];
}

function localListAssetModels(): ApiList<ApiAssetModel> {
  return { items: readLocalJson<ApiAssetModel[]>(LOCAL_ASSET_MODELS_KEY, []) };
}

function mergeLocalAssetModels(remoteModels: ApiAssetModel[]): ApiList<ApiAssetModel> {
  const localModels = readLocalJson<ApiAssetModel[]>(LOCAL_ASSET_MODELS_KEY, []);
  const remoteIds = new Set(remoteModels.map((model) => model.id));
  const remoteCodes = new Set(remoteModels.map((model) => model.code));
  return {
    items: [
      ...localModels.filter((model) => !remoteIds.has(model.id) && !remoteCodes.has(model.code)),
      ...remoteModels
    ]
  };
}

function localCreateAssetModel(input: { id?: string; name: string; code: string; fields?: ApiAssetModel['fields']; primary_key?: string }): ApiAssetModel {
  const rows = readLocalJson<ApiAssetModel[]>(LOCAL_ASSET_MODELS_KEY, []);
  const fields = normalizeAssetFields(input.fields);
  const createdAt = nowIso();
  const model: ApiAssetModel = {
    id: input.id?.trim() || `model-local-${Date.now()}`,
    name: input.name.trim(),
    code: input.code.trim(),
    fields,
    primary_key: input.primary_key && fields.some((field) => field.key === input.primary_key) ? input.primary_key : fields[0].key,
    status: 'active',
    created_by: getCurrentApiRole(),
    created_at: createdAt
  };
  writeLocalJson(LOCAL_ASSET_MODELS_KEY, [model, ...rows.filter((row) => row.id !== model.id && row.code !== model.code)]);
  const recordsByModel = readLocalJson<Record<string, ApiAssetRecord[]>>(LOCAL_ASSET_RECORDS_KEY, {});
  writeLocalJson(LOCAL_ASSET_RECORDS_KEY, { ...recordsByModel, [model.id]: recordsByModel[model.id] ?? [] });
  localAudit('创建资产模型', model.id);
  return model;
}

function localUpdateAssetModel(id: string, input: { name?: string; fields?: ApiAssetModel['fields']; primary_key?: string; status?: string }): ApiAssetModel {
  const rows = readLocalJson<ApiAssetModel[]>(LOCAL_ASSET_MODELS_KEY, []);
  const index = rows.findIndex((row) => row.id === id || row.code === id);
  if (index < 0) throw new Error(`Local asset model not found: ${id}`);
  const current = rows[index];
  const fields = input.fields ? normalizeAssetFields(input.fields) : current.fields;
  const updated: ApiAssetModel = {
    ...current,
    name: input.name?.trim() || current.name,
    fields,
    primary_key: input.primary_key && fields.some((field) => field.key === input.primary_key) ? input.primary_key : current.primary_key,
    status: input.status || current.status
  };
  const nextRows = [...rows];
  nextRows[index] = updated;
  writeLocalJson(LOCAL_ASSET_MODELS_KEY, nextRows);
  localAudit('更新资产模型', updated.id);
  return updated;
}

function localDeleteAssetModel(id: string) {
  const rows = readLocalJson<ApiAssetModel[]>(LOCAL_ASSET_MODELS_KEY, []);
  const model = rows.find((row) => row.id === id || row.code === id) ?? { id, code: id, name: id };
  const recordsByModel = readLocalJson<Record<string, ApiAssetRecord[]>>(LOCAL_ASSET_RECORDS_KEY, {});
  if ((recordsByModel[model.id] ?? []).length > 0) {
    throw new Error('模型已有实例数据，不能删除');
  }
  const syncReferenced = readLocalJson<ApiAssetSyncRun[]>(LOCAL_ASSET_SYNC_RUNS_KEY, []).some((run) => run.payload.model_id === model.id || run.payload.model_id === model.code);
  const referenceText = JSON.stringify([
    readLocalJson<ApiWorkorder[]>(LOCAL_WORKORDERS_KEY, []),
    readLocalJson<ApiAlertEvent[]>(LOCAL_ALERTS_KEY, []),
    readLocalJson<ApiMonitoringStrategy[]>(LOCAL_STRATEGIES_KEY, [])
  ]);
  const businessReferenced = [model.id, model.code, model.name].some((value) => value && referenceText.includes(value));
  if (syncReferenced || businessReferenced) {
    throw new Error('模型已被同步任务、工单、告警或策略引用，不能删除');
  }
  writeLocalJson(LOCAL_ASSET_MODELS_KEY, rows.filter((row) => row.id !== model.id && row.code !== model.code));
  const nextRecords = { ...recordsByModel };
  delete nextRecords[model.id];
  writeLocalJson(LOCAL_ASSET_RECORDS_KEY, nextRecords);
  const deletedKeys = new Set(readLocalJson<string[]>(LOCAL_ASSET_MODEL_DELETIONS_KEY, []));
  deletedKeys.add(model.id);
  deletedKeys.add(model.code);
  writeLocalJson(LOCAL_ASSET_MODEL_DELETIONS_KEY, Array.from(deletedKeys));
  localAudit('删除资产模型', model.id);
  return { id: model.id, deleted: true };
}

function localListAssetRecords(modelId?: string): ApiList<ApiAssetRecord> {
  const recordsByModel = readLocalJson<Record<string, ApiAssetRecord[]>>(LOCAL_ASSET_RECORDS_KEY, {});
  if (modelId) return { items: recordsByModel[modelId] ?? [] };
  return { items: Object.values(recordsByModel).flat() };
}

function hasLocalAssetRecords(modelId: string) {
  const recordsByModel = readLocalJson<Record<string, ApiAssetRecord[]>>(LOCAL_ASSET_RECORDS_KEY, {});
  return Object.prototype.hasOwnProperty.call(recordsByModel, modelId);
}

function writeLocalAssetRecords(modelId: string, records: ApiAssetRecord[]) {
  const recordsByModel = readLocalJson<Record<string, ApiAssetRecord[]>>(LOCAL_ASSET_RECORDS_KEY, {});
  writeLocalJson(LOCAL_ASSET_RECORDS_KEY, { ...recordsByModel, [modelId]: records });
}

function localCreateAssetRecord(model: { id: string; code: string }, values: Record<string, unknown>): ApiAssetRecord {
  const rows = localListAssetRecords(model.id).items;
  const now = nowIso();
  const row = {
    id: `asset-local-${model.id}-${Date.now()}`,
    model_id: model.id,
    model_code: model.code,
    source: 'Manual',
    created_by: getCurrentApiRole(),
    created_at: now,
    updated_at: now,
    ...values
  } as ApiAssetRecord;
  writeLocalAssetRecords(model.id, [row, ...rows]);
  localAudit('新增资产实例', row.id);
  return row;
}

function localUpdateAssetRecord(modelId: string, recordId: string, values: Record<string, unknown>): ApiAssetRecord {
  const rows = localListAssetRecords(modelId).items;
  const index = rows.findIndex((row) => row.id === recordId);
  if (index < 0) throw new Error(`Local asset record not found: ${recordId}`);
  const row = { ...rows[index], ...values, updated_at: nowIso() } as ApiAssetRecord;
  const nextRows = [...rows];
  nextRows[index] = row;
  writeLocalAssetRecords(modelId, nextRows);
  localAudit('编辑资产实例', recordId);
  return row;
}

function localDeleteAssetRecord(modelId: string, recordId: string) {
  const rows = localListAssetRecords(modelId).items;
  const record = rows.find((row) => row.id === recordId);
  if (!record) throw new Error(`Local asset record not found: ${recordId}`);
  const referenceValues = [record.id, record.name, record.domain, record.ip]
    .map((value) => String(value ?? '').trim())
    .filter(Boolean);
  const referencedByWorkorder = readLocalJson<ApiWorkorder[]>(LOCAL_WORKORDERS_KEY, []).some((item) =>
    referenceValues.some((value) => [item.related_object, item.relatedAlertId, item.title].some((target) => String(target ?? '').includes(value)))
  );
  const referencedByAlert = readLocalJson<ApiAlertEvent[]>(LOCAL_ALERTS_KEY, []).some((item) =>
    referenceValues.some((value) => [item.asset, item.title].some((target) => String(target ?? '').includes(value)))
  );
  const referencedByStrategy = JSON.stringify(readLocalJson<ApiMonitoringStrategy[]>(LOCAL_STRATEGIES_KEY, [])).includes(recordId)
    || referenceValues.some((value) => JSON.stringify(readLocalJson<ApiMonitoringStrategy[]>(LOCAL_STRATEGIES_KEY, [])).includes(value));
  if (referencedByWorkorder || referencedByAlert || referencedByStrategy) {
    throw new Error('资产实例已被工单、告警或策略引用，不能删除');
  }
  writeLocalAssetRecords(modelId, rows.filter((row) => row.id !== recordId));
  localAudit('删除资产实例', recordId);
  return { id: recordId, deleted: true };
}

function localListAssetSyncRuns(): ApiList<ApiAssetSyncRun> {
  return { items: readLocalJson<ApiAssetSyncRun[]>(LOCAL_ASSET_SYNC_RUNS_KEY, []) };
}

function writeLocalAssetSyncRun(run: ApiAssetSyncRun) {
  writeLocalJson(LOCAL_ASSET_SYNC_RUNS_KEY, [run, ...readLocalJson<ApiAssetSyncRun[]>(LOCAL_ASSET_SYNC_RUNS_KEY, [])].slice(0, 50));
}

function localRecordAssetSyncFailure(input: AssetSyncFailureInput): ApiAssetSyncRun {
  const run: ApiAssetSyncRun = {
    event_id: `sync-local-failed-${Date.now()}`,
    event_type: 'asset.sync.failed',
    producer: 'assets',
    payload: {
      model_id: input.modelId,
      source: input.source ?? 'script',
      script: input.script,
      script_id: input.scriptId,
      script_version: input.scriptVersion,
      count: 0,
      update_count: 0,
      fail_count: 1,
      operator: getCurrentApiRole(),
      error_type: input.errorType,
      error_message: input.errorMessage,
      error_detail: input.errorDetail,
      suggestion: input.suggestion,
      reason: input.errorMessage
    },
    created_at: nowIso()
  };
  writeLocalAssetSyncRun(run);
  localAudit('记录资产同步失败', input.modelId ?? input.script ?? 'asset-sync');
  return run;
}

function localListAssetSyncScripts(): ApiList<ApiAssetSyncScript> {
  const scripts = readLocalJson<ApiAssetSyncScript[]>(LOCAL_ASSET_SYNC_SCRIPTS_KEY, []);
  return { items: scripts.length ? scripts : readLocalJson<ApiAssetSyncScript[]>('oneall.assetSyncTasks', []) };
}

function localHashText(text: string) {
  let hash = 0;
  for (let index = 0; index < text.length; index += 1) {
    hash = ((hash << 5) - hash + text.charCodeAt(index)) | 0;
  }
  return Math.abs(hash).toString(16);
}

function localSaveAssetSyncScript(input: Omit<ApiAssetSyncScript, 'id' | 'current_version' | 'script_versions' | 'updated_by' | 'updated_at' | 'created_at'> & { id?: string }): ApiAssetSyncScript {
  const scripts = localListAssetSyncScripts().items;
  const current = input.id ? scripts.find((script) => script.id === input.id) : undefined;
  const now = nowIso();
  const scriptHash = localHashText(`${input.script_name}\n${input.script_content}`);
  const mappingHash = localHashText(JSON.stringify(input.field_mapping ?? {}));
  const currentVersions = current?.script_versions ?? [];
  const latestVersion = currentVersions[0];
  const changed = !latestVersion || latestVersion.content_hash !== scriptHash || latestVersion.mapping_hash !== mappingHash || latestVersion.script_name !== input.script_name.trim();
  const nextVersionNumber = changed ? currentVersions.length + 1 : currentVersions.length || 1;
  const nextVersion: ApiAssetSyncScriptVersion = {
    id: `sync-script-version-${input.model_id}-${Date.now()}`,
    version: `v${nextVersionNumber}`,
    script_name: input.script_name.trim(),
    content_hash: scriptHash,
    mapping_hash: mappingHash,
    updated_by: getCurrentApiRole(),
    updated_at: now
  };
  const scriptVersions = changed ? [nextVersion, ...currentVersions].slice(0, 20) : currentVersions;
  const script: ApiAssetSyncScript = {
    id: current?.id ?? input.id ?? `sync-script-${input.model_id}-${Date.now()}`,
    name: input.name.trim() || `${input.script_name || 'asset-sync'} 同步脚本`,
    model_id: input.model_id,
    script_name: input.script_name.trim(),
    script_content: input.script_content,
    field_mapping: input.field_mapping,
    current_version: scriptVersions[0]?.version ?? 'v1',
    script_versions: scriptVersions,
    enabled: input.enabled,
    updated_by: getCurrentApiRole(),
    updated_at: now,
    created_at: current?.created_at ?? now
  };
  writeLocalJson(LOCAL_ASSET_SYNC_SCRIPTS_KEY, [script, ...scripts.filter((item) => item.id !== script.id)]);
  localAudit('保存资产同步脚本', script.id);
  return script;
}

function localListAuditLogs(): ApiList<ApiAuditLog> {
  return { items: readLocalJson<ApiAuditLog[]>(LOCAL_AUDIT_LOGS_KEY, []) };
}

function findLocalAssetModel(modelId: string) {
  return readLocalJson<ApiAssetModel[]>(LOCAL_ASSET_MODELS_KEY, []).find((model) => model.id === modelId || model.code === modelId);
}

function defaultSourceFieldKey(field: { key: string }, source: string) {
  if (source === 'blueking_cmdb') return `bk_${field.key}`;
  if (source === 'zabbix') return `zbx_${field.key}`;
  if (source === 'manual' || source === 'script') return field.key;
  return `${source}_${field.key}`;
}

function sampleValueForSourceField(sourceKey: string, field: { key: string; type: string; label?: string }, index: number, source: string) {
  const serial = String(index + 1).padStart(2, '0');
  if (sourceKey.includes('domain') || field.key.includes('domain')) return `${source === 'zabbix' ? 'host' : 'svc'}-${serial}.oneall.internal`;
  if (sourceKey.includes('ip') || field.key === 'ip' || field.type === 'ip') return `10.30.${index + 1}.${20 + index}`;
  if (sourceKey.includes('owner') || field.key.includes('owner')) return ['张三', '李四', '王五'][index % 3];
  if (sourceKey.includes('environment') || field.key.includes('environment')) return index % 2 === 0 ? 'prod' : 'staging';
  if (field.type === 'number') return index + 1;
  if (field.type === 'boolean') return index % 2 === 0;
  if (field.type === 'status') return index % 2 === 0 ? '运行' : '维护';
  return `${field.label || field.key}-${serial}`;
}

function localPreviewAssetSync(modelId: string, input: AssetSyncInput = {}): ApiAssetSyncPreview {
  const model = findLocalAssetModel(modelId) ?? input.model;
  if (!model) throw new Error(`Local asset model not found: ${modelId}`);
  const source = input.source || 'script';
  const enabledFields = model.fields.filter((field) => !field.disabled);
  const primaryKey = model.primary_key || enabledFields[0]?.key;
  const existingRows = localListAssetRecords(model.id).items;
  const issues = enabledFields
    .filter((field) => (field.required || field.unique || model.primary_key === field.key) && !input.mapping?.[field.key])
    .map((field) => `${field.label || field.key} 未配置来源字段`);
  const samples = Array.from({ length: 3 }, (_, index) => {
    const record: Record<string, unknown> = {};
    for (const field of enabledFields) {
      const sourceKey = input.mapping?.[field.key] || defaultSourceFieldKey(field, source);
      record[field.key] = sampleValueForSourceField(sourceKey, field, index, source);
    }
    record.name = String(record[model.primary_key || enabledFields[0]?.key] ?? `${model.name}-${index + 1}`);
    record.owner = String(record.owner ?? record.system_owner ?? getCurrentApiRole());
    record.environment = String(record.environment ?? 'prod');
    record.source = source;
    return record;
  });
  const updates = primaryKey
    ? samples.filter((sample) => existingRows.some((row) => String(row[primaryKey] ?? '') === String(sample[primaryKey] ?? ''))).length
    : 0;
  return {
    model_id: model.id,
    source,
    creates: samples.length - updates,
    updates,
    deletes: 0,
    issues,
    samples
  };
}

function localRunAssetSync(modelId: string, input: AssetSyncInput = {}): ApiAssetSyncResult {
  const model = findLocalAssetModel(modelId) ?? input.model;
  if (!model) throw new Error(`Local asset model not found: ${modelId}`);
  const preview = localPreviewAssetSync(model.id, input);
  const recordsByModel = readLocalJson<Record<string, ApiAssetRecord[]>>(LOCAL_ASSET_RECORDS_KEY, {});
  const enabledFields = model.fields.filter((field) => !field.disabled);
  const primaryKey = model.primary_key || enabledFields[0]?.key;
  const existingRows = recordsByModel[model.id] ?? [];
  let createCount = 0;
  let updateCount = 0;
  const touchedIds = new Set<string>();
  const syncedRows = preview.samples.map((sample, index) => {
    const matched = primaryKey
      ? existingRows.find((row) => String(row[primaryKey] ?? '') === String(sample[primaryKey] ?? ''))
      : undefined;
    if (matched) {
      updateCount += 1;
      touchedIds.add(matched.id);
      return {
        ...matched,
        ...sample,
        source: preview.source,
        updated_at: nowIso()
      } as ApiAssetRecord;
    }
    createCount += 1;
    return {
      id: `asset-local-${model.id}-${Date.now()}-${index}`,
      model_id: model.id,
      model_code: model.code,
      source: preview.source,
      created_by: '同步脚本',
      created_at: nowIso(),
      updated_at: nowIso(),
      ...sample
    } as ApiAssetRecord;
  });
  const untouchedRows = existingRows.filter((row) => !touchedIds.has(row.id));
  writeLocalJson(LOCAL_ASSET_RECORDS_KEY, { ...recordsByModel, [model.id]: [...syncedRows, ...untouchedRows] });
  const run: ApiAssetSyncRun = {
    event_id: `sync-local-${Date.now()}`,
    event_type: 'asset.sync.completed',
    producer: 'assets',
    payload: {
      model_id: model.id,
      source: preview.source,
      script: input.script,
      script_id: input.scriptId,
      script_version: input.scriptVersion,
      count: createCount,
      update_count: updateCount,
      fail_count: 0,
      operator: getCurrentApiRole()
    },
    created_at: nowIso()
  };
  writeLocalAssetSyncRun(run);
  localAudit('执行资产同步', model.id);
  return {
    model_id: model.id,
    source: preview.source,
    count: syncedRows.length,
    records: syncedRows
  };
}
