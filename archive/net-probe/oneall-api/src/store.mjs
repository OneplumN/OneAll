import { applyDataScope, assertDataScope, previewAlertRule, transitionWorkorder, validateAlertRuleDsl, validateAssetFields, validateAssetRecord } from './domain.mjs';

const now = () => new Date().toISOString();
const nextId = (prefix, seq) => `${prefix}-${String(seq).padStart(4, '0')}`;

function defaultProbeAgentConfig(capabilities = []) {
  const caps = Array.isArray(capabilities) && capabilities.length > 0 ? capabilities : ['HTTP'];
  return {
    heartbeat_interval_seconds: 30,
    task_claim_limit: 5,
    capabilities: caps,
    result_endpoint: '/api/v1/probes/tasks/{task_id}/result',
    schedule_result_endpoint: '/api/v1/probes/schedules/{schedule_id}/result'
  };
}

function sanitizeProbe(probe) {
  const { token, ...safeProbe } = probe;
  return safeProbe;
}

function probeTokenHint(token = '') {
  if (!token) return '';
  return token.length <= 10 ? token : `${token.slice(0, 10)}…`;
}

function probeVersionNumber(version = 'v1') {
  const parsed = Number(String(version).trim().replace(/^v/, ''));
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
}

function numeric(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function roundMetric(value) {
  const clamped = Math.max(0, Math.min(100, value));
  return Math.round(clamped * 10) / 10;
}

function heartbeatDelaySeconds(value) {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) return 0;
  return Math.max(0, Math.floor((Date.now() - parsed) / 1000));
}

function nextSeqFromIds(items, prefix, fallback) {
  const max = items.reduce((acc, item) => {
    const match = String(item.id || item.event_id || '').match(new RegExp(`^${prefix}-(\\d+)$`));
    return match ? Math.max(acc, Number(match[1])) : acc;
  }, fallback - 1);
  return max + 1;
}

function normalizeSequences(state) {
  state.seq.assetModel = nextSeqFromIds(state.assetModels, 'MDL', state.seq.assetModel);
  state.seq.assetRecord = nextSeqFromIds(state.assetRecords, 'AST', state.seq.assetRecord);
  state.seq.workorder = nextSeqFromIds(state.workorders, 'WO', state.seq.workorder);
  state.seq.strategy = nextSeqFromIds(state.strategies, 'STR', state.seq.strategy);
  state.seq.alert = nextSeqFromIds(state.alerts, 'ALT', state.seq.alert);
  state.seq.probe = nextSeqFromIds(state.probes, 'PRB', state.seq.probe);
  state.seq.detection = nextSeqFromIds(state.detectionTasks, 'DET', state.seq.detection);
  state.seq.audit = nextSeqFromIds(state.auditLogs, 'AUD', state.seq.audit);
  state.seq.event = nextSeqFromIds(state.events, 'EVT', state.seq.event);
  state.seq.notification = nextSeqFromIds(state.notifications, 'NTF', state.seq.notification);
}

export function createStore(options = {}) {
  const persistedState = options.persistence?.load();
  const state = persistedState || {
    seq: {
      assetModel: 1,
      assetRecord: 1,
      workorder: 16,
      strategy: 4,
      alert: 5,
      probe: 4,
      detection: 10,
      audit: 1,
      event: 1,
      notification: 1
    },
    users: [
      { id: 'user-1', name: '平台管理员', role: 'PlatformAdmin' },
      { id: 'user-2', name: '值班工程师', role: 'OpsEngineer' },
      { id: 'user-3', name: '审批人', role: 'Approver' }
    ],
    assetModels: [],
    assetRecords: [],
    strategies: [
      {
        id: 'STR-0001',
        name: 'HTTP 可用性',
        scope: '用户创建模型 / prod',
        enabled: true,
        version: 'v1',
        rule: {
          scope: { asset_model: 'user_created_model', asset_filter: { environment: 'prod' } },
          signal: { metric: 'http_status', source: 'probe_result' },
          condition: { operator: 'not_in', value: [200, 301, 302], duration: '3m', consecutive: 3 },
          severity: 'critical',
          recovery: { operator: 'in', value: [200, 301, 302], consecutive: 2 },
          actions: { notify_channels: ['site', 'webhook'], create_workorder: true }
        },
        created_at: now()
      }
    ],
    alerts: [
      { id: 'ALT-0001', severity: 'P0', title: 'api.oneall.internal HTTP 检测连续超时', asset: 'api.oneall.internal', duration: '18m', owner: '张三', business_line: '支付业务', environment: 'prod', notify: '已投递', workorder: 'WO-0014', status: '处理中', created_at: now() },
      { id: 'ALT-0002', severity: 'P1', title: 'www.oneall.internal 证书 7 天后过期', asset: 'www.oneall.internal', duration: '2h', owner: '李四', business_line: '增长业务', environment: 'prod', notify: '待重试', workorder: '-', status: '待认领', created_at: now() }
    ],
    workorders: [
      { id: 'WO-0014', type: '拨测监控申请', title: '新增 api.oneall.internal HTTP 监控', applicant: '张三', assignee: '李四', status: 'submitted', sla: '3h 20m', business_line: '支付业务', environment: 'prod', related_object: 'ALT-0001', created_at: now(), updated_at: now() },
      { id: 'WO-0015', type: '告警处理', title: 'pay DNS 解析异常处理', applicant: '系统', assignee: '王五', status: 'executing', sla: '42m', business_line: '支付业务', environment: 'prod', related_object: 'ALT-0003', created_at: now(), updated_at: now() }
    ],
    probes: [
      {
        id: 'PRB-0001',
        name: 'probe-sh-01',
        region: '上海',
        network_type: '公网出口',
        ip_address: '10.10.1.21',
        capabilities: ['HTTP', 'TCP', 'DNS'],
        status: 'online',
        heartbeat_at: now(),
        version: 'v18',
        active_tasks: 0,
        success_rate: 99.3,
        avg_latency_ms: 41,
        queue_depth: 0,
        executions: 1286,
        failed: 9,
        cpu_usage: 32,
        memory_usage_mb: 612,
        memory_usage_pct: 41,
        load_avg: 0.72,
        uptime: '18 天',
        connection_status: 'connected',
        config_status: 'acknowledged',
        gateway_url: 'https://gateway.oneall.internal/probes/PRB-0001',
        bootstrap_token_hint: 'probe_token…',
        registered_at: now(),
        last_config_sync_at: now(),
        agent_config: defaultProbeAgentConfig(['HTTP', 'TCP', 'DNS']),
        token: 'probe_token_sh_01'
      }
    ],
    detectionTasks: [],
    auditLogs: [],
    events: [],
    notifications: []
  };
  normalizeSequences(state);

  const persist = () => {
    options.persistence?.save(state);
  };

  const audit = (actor, action, object, result = '成功', payload = {}) => {
    const record = { id: nextId('AUD', state.seq.audit++), actor, action, object, result, payload, created_at: now() };
    state.auditLogs.unshift(record);
    return record;
  };

  const notify = (target, title, payload = {}) => {
    const record = {
      id: nextId('NTF', state.seq.notification++),
      target,
      title,
      payload,
      status: 'unread',
      created_at: now()
    };
    state.notifications.unshift(record);
    return record;
  };

  const event = (producer, event_type, payload) => {
    const record = {
      event_id: nextId('EVT', state.seq.event++),
      trace_id: `trace-${Date.now()}`,
      event_type,
      producer,
      payload,
      created_at: now()
    };
    state.events.unshift(record);
    return record;
  };

  const recordDomainChange = (actor, action, object, eventProducer, eventType, payload = {}, notificationTitle) => {
    audit(actor, action, object, '成功', payload);
    event(eventProducer, eventType, payload);
    if (notificationTitle) notify(actor, notificationTitle, payload);
    persist();
  };

  const probeTaskStats = (probe) => {
    const tasks = state.detectionTasks.filter((task) => task.probe === probe.name || task.probe === probe.id);
    const pending = tasks.filter((task) => task.status === 'pending').length;
    const running = tasks.filter((task) => task.status === 'running').length;
    const finished = tasks.filter((task) => ['success', 'failed'].includes(task.status));
    const failed = finished.filter((task) => task.status === 'failed').length;
    const latencies = finished
      .map((task) => numeric(task.result?.latency_ms ?? task.result?.duration_ms))
      .filter((value) => value !== undefined);
    const avgLatency = latencies.length > 0
      ? Math.round(latencies.reduce((acc, value) => acc + value, 0) / latencies.length)
      : (probe.avg_latency_ms || 89);
    return { pending, running, executed: finished.length, failed, avgLatency };
  };

  const enrichProbe = (probe) => {
    const stats = probeTaskStats(probe);
    const next = {
      ...probe,
      name: probe.name || probe.id,
      region: probe.region || 'unknown',
      network_type: probe.network_type || '公网出口',
      capabilities: Array.isArray(probe.capabilities) && probe.capabilities.length > 0 ? probe.capabilities : ['HTTP'],
      status: probe.status || 'online',
      heartbeat_at: probe.heartbeat_at || now(),
      version: probe.version || 'v1',
      registered_at: probe.registered_at || probe.heartbeat_at || now(),
      last_config_sync_at: probe.last_config_sync_at || probe.heartbeat_at || now(),
      active_tasks: probe.active_tasks ?? stats.running,
      queue_depth: probe.queue_depth ?? stats.pending,
      executions: probe.executions ?? stats.executed,
      failed: probe.failed ?? stats.failed,
      avg_latency_ms: probe.avg_latency_ms || stats.avgLatency,
      cpu_usage: probe.cpu_usage || 12,
      memory_usage_mb: probe.memory_usage_mb || 256,
      memory_usage_pct: probe.memory_usage_pct || 24,
      load_avg: probe.load_avg || 0.2,
      uptime: probe.uptime || '刚刚',
      connection_status: probe.connection_status || (probe.status === 'retired' ? 'disconnected' : 'connected'),
      config_status: probe.config_status || 'acknowledged',
      gateway_url: probe.gateway_url || `https://gateway.oneall.internal/probes/${probe.id}`,
      bootstrap_token_hint: probe.bootstrap_token_hint || probeTokenHint(probe.token),
      agent_config: probe.agent_config || defaultProbeAgentConfig(probe.capabilities)
    };
    if (!next.success_rate) {
      next.success_rate = next.executions > 0 ? roundMetric(((next.executions - next.failed) / next.executions) * 100) : 100;
    }
    return next;
  };

  return {
    state,
    profile(role = 'OpsAdmin') {
      return { id: 'current-user', name: 'OpsAdmin', role, permissions: role };
    },
    overview(role = 'OpsAdmin') {
      const scopedAlerts = this.listAlerts(role);
      const scopedWorkorders = this.listWorkorders(role);
      return {
        unresolved_alerts: scopedAlerts.filter((item) => item.status !== '已恢复').length,
        p0: scopedAlerts.filter((item) => item.severity === 'P0').length,
        asset_models: state.assetModels.length,
        workorders_waiting: scopedWorkorders.filter((item) => ['submitted', 'approved', 'executing'].includes(item.status)).length,
        probes_online: state.probes.filter((item) => item.status === 'online').length
      };
    },
    listAssetModels() {
      return state.assetModels;
    },
    getAssetModel(id) {
      const model = state.assetModels.find((item) => item.id === id || item.code === id);
      if (!model) {
        const error = new Error('资产模型不存在');
        error.status = 404;
        throw error;
      }
      return model;
    },
    createAssetModel(input, actor = 'OpsAdmin') {
      if (!input?.name || !input?.code) {
        const error = new Error('资产模型 name 和 code 必填');
        error.status = 400;
        throw error;
      }
      if (state.assetModels.some((item) => item.code === input.code)) {
        const error = new Error('资产模型 code 已存在');
        error.status = 409;
        throw error;
      }
      const fieldValidation = validateAssetFields(input.fields || []);
      if (!fieldValidation.valid) {
        const error = new Error(fieldValidation.errors.join('；'));
        error.status = 400;
        throw error;
      }
      const model = {
        id: nextId('MDL', state.seq.assetModel++),
        name: input.name,
        code: input.code,
        fields: Array.isArray(input.fields) ? input.fields : [],
        status: 'active',
        created_by: actor,
        created_at: now(),
        updated_at: now()
      };
      state.assetModels.unshift(model);
      recordDomainChange(actor, '创建资产模型', model.id, 'assets', 'asset.sync.started', { model_id: model.id, reason: 'model_created' }, `资产模型已创建：${model.name}`);
      return model;
    },
    updateAssetModel(id, input, actor = 'OpsAdmin') {
      const index = state.assetModels.findIndex((item) => item.id === id || item.code === id);
      if (index < 0) {
        const error = new Error('资产模型不存在');
        error.status = 404;
        throw error;
      }
      const current = state.assetModels[index];
      const fieldValidation = validateAssetFields(Array.isArray(input?.fields) ? input.fields : current.fields);
      if (!fieldValidation.valid) {
        const error = new Error(fieldValidation.errors.join('；'));
        error.status = 400;
        throw error;
      }
      const next = {
        ...current,
        name: input?.name ?? current.name,
        description: input?.description ?? current.description,
        fields: Array.isArray(input?.fields) ? input.fields : current.fields,
        status: input?.status ?? current.status,
        updated_at: now()
      };
      state.assetModels[index] = next;
      recordDomainChange(actor, '更新资产模型', next.id, 'assets', 'asset.sync.started', { model_id: next.id, reason: 'model_updated' }, `资产模型已更新：${next.name}`);
      return next;
    },
    batchAssetRecords(input, actor = 'OpsAdmin') {
      const model = this.getAssetModel(input?.model_id || input?.model_code);
      const records = Array.isArray(input?.records) ? input.records : [];
      if (!records.length) {
        const error = new Error('records 必须至少包含一条记录');
        error.status = 400;
        throw error;
      }
      const updated = records.map((record) => {
        const validation = validateAssetRecord(model, record);
        if (!validation.valid) {
          const error = new Error(validation.errors.join('；'));
          error.status = 400;
          throw error;
        }
        const id = record.id || nextId('AST', state.seq.assetRecord++);
        const existingIndex = state.assetRecords.findIndex((item) => item.id === id);
        const item = {
          ...(existingIndex >= 0 ? state.assetRecords[existingIndex] : {}),
          ...record,
          id,
          model_id: model.id,
          model_code: model.code,
          updated_at: now()
        };
        if (existingIndex >= 0) state.assetRecords[existingIndex] = item;
        else state.assetRecords.unshift(item);
        return item;
      });
      recordDomainChange(actor, '批量写入资产记录', model.id, 'assets', 'asset.sync.completed', { model_id: model.id, count: updated.length }, `资产记录已更新：${model.name}`);
      return { items: updated, count: updated.length };
    },
    previewAssetSync(modelId, input = {}) {
      const model = this.getAssetModel(modelId);
      const source = input.source || 'manual';
      const sample = {
        name: `${model.code}-sample`,
        owner: input.owner || 'OpsAdmin',
        environment: input.environment || 'prod'
      };
      return {
        model_id: model.id,
        source,
        total: 1,
        creates: state.assetRecords.some((item) => item.model_id === model.id) ? 0 : 1,
        updates: state.assetRecords.some((item) => item.model_id === model.id) ? 1 : 0,
        sample
      };
    },
    runAssetSync(modelId, input = {}, actor = 'OpsAdmin') {
      const model = this.getAssetModel(modelId);
      const preview = this.previewAssetSync(model.id, input);
      const result = this.batchAssetRecords({ model_id: model.id, records: [preview.sample] }, actor);
      event('assets', 'asset.sync.completed', { model_id: model.id, source: preview.source, count: result.count });
      notify(actor, `资产同步完成：${model.name}`, { model_id: model.id, count: result.count });
      persist();
      return { ...preview, run_id: state.events[0]?.event_id, records: result.items };
    },
    listAssetRecords(role = 'OpsAdmin') {
      return applyDataScope(role, 'assets', state.assetRecords);
    },
    listWorkorders(role = 'OpsAdmin') {
      return applyDataScope(role, 'workorders', state.workorders);
    },
    getWorkorder(id, role = 'OpsAdmin') {
      const item = state.workorders.find((row) => row.id === id);
      if (!item) {
        const error = new Error('工单不存在');
        error.status = 404;
        throw error;
      }
      assertDataScope(role, 'workorders', item);
      return item;
    },
    createWorkorder(input, actor = 'OpsEngineer') {
      if (!input?.title || !input?.type) {
        const error = new Error('工单 title 和 type 必填');
        error.status = 400;
        throw error;
      }
      const workorder = {
        id: nextId('WO', state.seq.workorder++),
        type: input.type,
        title: input.title,
        applicant: input.applicant || actor,
        assignee: input.assignee || '待分配',
        status: input.submit === false ? 'draft' : 'submitted',
        sla: input.sla || '4h',
        business_line: input.business_line || '支付业务',
        environment: input.environment || 'prod',
        related_object: input.related_object || '-',
        created_at: now(),
        updated_at: now()
      };
      state.workorders.unshift(workorder);
      recordDomainChange(actor, '创建工单', workorder.id, 'workorders', 'workorder.completed', { workorder_id: workorder.id, status: workorder.status }, `工单已创建：${workorder.id}`);
      return workorder;
    },
    transitionWorkorder(id, nextStatus, actor = 'OpsAdmin') {
      const index = state.workorders.findIndex((item) => item.id === id);
      if (index < 0) {
        const error = new Error('工单不存在');
        error.status = 404;
        throw error;
      }
      const updated = transitionWorkorder(state.workorders[index], nextStatus);
      state.workorders[index] = updated;
      recordDomainChange(actor, `工单流转到 ${nextStatus}`, id, 'workorders', 'workorder.completed', { workorder_id: id, status: nextStatus }, `工单状态已更新：${id}`);
      return updated;
    },
    batchWorkorders(input, actor = 'OpsAdmin') {
      const ids = Array.isArray(input?.ids) ? input.ids : [];
      const action = input?.action;
      const nextStatus = { approve: 'approved', reject: 'rejected', execute: 'executing', complete: 'completed', fail: 'failed' }[action];
      if (!nextStatus) {
        const error = new Error('不支持的工单批量动作');
        error.status = 400;
        throw error;
      }
      return { items: ids.map((id) => this.transitionWorkorder(id, nextStatus, actor)) };
    },
    listStrategies() {
      return state.strategies;
    },
    createStrategy(input, actor = 'OpsAdmin') {
      const validation = validateAlertRuleDsl(input?.rule);
      if (!validation.valid) {
        const error = new Error(validation.errors.join('；'));
        error.status = 400;
        throw error;
      }
      const strategy = {
        id: nextId('STR', state.seq.strategy++),
        name: input.name,
        scope: input.scope || input.rule.scope.asset_model,
        enabled: input.enabled !== false,
        version: 'v1',
        rule: input.rule,
        created_at: now()
      };
      state.strategies.unshift(strategy);
      recordDomainChange(actor, '创建监控策略', strategy.id, 'monitoring', 'monitoring.strategy.enabled', { strategy_id: strategy.id }, `监控策略已创建：${strategy.name}`);
      return strategy;
    },
    batchStrategies(input, actor = 'OpsAdmin') {
      const ids = Array.isArray(input?.ids) ? input.ids : [];
      const action = input?.action;
      if (!['enable', 'disable'].includes(action)) {
        const error = new Error('不支持的策略批量动作');
        error.status = 400;
        throw error;
      }
      const updated = state.strategies.filter((item) => ids.includes(item.id)).map((item) => {
        item.enabled = action === 'enable';
        item.updated_at = now();
        audit(actor, `批量${action === 'enable' ? '启用' : '停用'}策略`, item.id);
        return item;
      });
      event('monitoring', 'monitoring.strategy.enabled', { strategy_ids: ids, action });
      persist();
      return { items: updated };
    },
    previewStrategy(id, sample) {
      const strategy = state.strategies.find((item) => item.id === id);
      if (!strategy) {
        const error = new Error('策略不存在');
        error.status = 404;
        throw error;
      }
      return previewAlertRule(strategy.rule, sample);
    },
    listAlerts(role = 'OpsAdmin') {
      return applyDataScope(role, 'alerts', state.alerts);
    },
    getAlert(id, role = 'OpsAdmin') {
      const item = state.alerts.find((row) => row.id === id);
      if (!item) {
        const error = new Error('告警不存在');
        error.status = 404;
        throw error;
      }
      assertDataScope(role, 'alerts', item);
      return item;
    },
    closeAlerts(ids, actor = 'OpsAdmin') {
      const idSet = new Set(ids);
      const updated = [];
      state.alerts = state.alerts.map((item) => {
        if (!idSet.has(item.id)) return item;
        const next = { ...item, status: '已恢复', updated_at: now() };
        updated.push(next);
        recordDomainChange(actor, '关闭告警', item.id, 'alerts', 'alert.event.created', { alert_id: item.id, status: '已恢复' }, `告警已关闭：${item.id}`);
        return next;
      });
      persist();
      return updated;
    },
    registerProbe(input, actor = 'probe-bootstrap') {
      const token = `probe_token_${Date.now()}`;
      const probe = {
        id: nextId('PRB', state.seq.probe++),
        name: input?.name || `probe-${state.seq.probe}`,
        region: input?.region || 'unknown',
        network_type: input?.network_type || 'unknown',
        ip_address: input?.ip_address || '',
        capabilities: Array.isArray(input?.capabilities) ? input.capabilities : ['HTTP'],
        status: 'online',
        heartbeat_at: now(),
        version: input?.version || 'v1',
        connection_status: 'connected',
        config_status: 'acknowledged',
        registered_at: now(),
        last_config_sync_at: now(),
        gateway_url: '',
        bootstrap_token_hint: probeTokenHint(token),
        agent_config: defaultProbeAgentConfig(input?.capabilities),
        token
      };
      state.probes.unshift(probe);
      audit(actor, '注册探针', probe.id);
      notify('OpsAdmin', `探针已注册：${probe.name}`, { probe_id: probe.id });
      persist();
      return { ...sanitizeProbe(enrichProbe(probe)), token };
    },
    listProbes() {
      return state.probes.map((probe) => sanitizeProbe(enrichProbe(probe)));
    },
    listProbeHealth(hours = 6, intervalMinutes = 10) {
      return {
        items: state.probes.map((probe) => {
          const item = sanitizeProbe(enrichProbe(probe));
          return {
            probe: item,
            probe_id: item.id,
            name: item.name,
            status: item.status,
            connection_status: item.connection_status,
            config_status: item.config_status,
            heartbeat_at: item.heartbeat_at,
            heartbeat_delay_seconds: heartbeatDelaySeconds(item.heartbeat_at),
            success_rate: item.success_rate,
            avg_latency_ms: item.avg_latency_ms,
            active_tasks: item.active_tasks,
            queue_depth: item.queue_depth,
            version: item.version
          };
        }),
        window: { hours, interval_minutes: intervalMinutes }
      };
    },
    getProbeRuntime(id) {
      const probe = state.probes.find((item) => item.id === id || item.name === id);
      if (!probe) {
        const error = new Error('探针不存在');
        error.status = 404;
        throw error;
      }
      const item = sanitizeProbe(enrichProbe(probe));
      const stats = probeTaskStats(item);
      return {
        probe: item,
        probe_id: item.id,
        name: item.name,
        status: item.status,
        connection_status: item.connection_status,
        heartbeat_at: item.heartbeat_at,
        heartbeat_delay_seconds: heartbeatDelaySeconds(item.heartbeat_at),
        pending_tasks: stats.pending,
        running_tasks: stats.running,
        capabilities: item.capabilities,
        tasks: {
          pending: stats.pending,
          running: stats.running,
          active: item.active_tasks,
          queue_depth: item.queue_depth,
          executed: stats.executed,
          failed: stats.failed
        },
        resource_metrics: {
          cpu_usage: item.cpu_usage,
          memory_usage_mb: item.memory_usage_mb,
          memory_usage_pct: item.memory_usage_pct,
          load_avg: item.load_avg,
          avg_latency_ms: stats.avgLatency
        }
      };
    },
    heartbeatProbe(id, input = {}, actor = 'probe') {
      const probe = state.probes.find((item) => item.id === id || item.name === id);
      if (!probe) {
        const error = new Error('探针不存在');
        error.status = 404;
        throw error;
      }
      if (Array.isArray(input.capabilities) && input.capabilities.length) probe.capabilities = input.capabilities;
      if (input.ip_address) probe.ip_address = input.ip_address;
      if (input.version) probe.version = input.version;
      probe.status = 'online';
      probe.connection_status = 'connected';
      probe.heartbeat_at = now();
      audit(actor, '探针心跳', probe.id);
      persist();
      return sanitizeProbe(enrichProbe(probe));
    },
    listProbeMetricsHistory(id, hours = 6, intervalMinutes = 60) {
      const probe = state.probes.find((item) => item.id === id || item.name === id);
      if (!probe) {
        const error = new Error('探针不存在');
        error.status = 404;
        throw error;
      }
      const item = enrichProbe(probe);
      const safeHours = Number(hours) > 0 ? Number(hours) : 6;
      const safeInterval = Number(intervalMinutes) > 0 ? Number(intervalMinutes) : 60;
      const count = Math.min(48, Math.max(4, Math.floor((safeHours * 60) / safeInterval)));
      const end = Date.now();
      const points = Array.from({ length: count }, (_, index) => {
        const offset = count - index - 1;
        const variance = ((index + 1) % 6) * 1.7;
        return {
          timestamp: new Date(end - offset * safeInterval * 60 * 1000).toISOString(),
          cpu_usage: roundMetric(item.cpu_usage + variance),
          memory_usage_mb: item.memory_usage_mb + index * 2,
          memory_usage_pct: roundMetric(item.memory_usage_pct + variance / 2),
          queue_depth: item.queue_depth,
          active_workers: item.active_tasks,
          tasks_executed: item.executions + index + 1,
          heartbeats_sent: index + 1
        };
      });
      return {
        probe_id: item.id,
        name: item.name,
        from: points[0]?.timestamp,
        to: new Date(end).toISOString(),
        points,
        window: { hours: safeHours, interval_minutes: safeInterval }
      };
    },
    listProbeConfigVersions(id) {
      const probe = state.probes.find((item) => item.id === id || item.name === id);
      if (!probe) {
        const error = new Error('探针不存在');
        error.status = 404;
        throw error;
      }
      const item = enrichProbe(probe);
      const version = probeVersionNumber(item.version);
      const current = {
        id: `${item.id}-v${version}`,
        probe_id: item.id,
        version,
        version_label: `v${version}`,
        status: item.config_status,
        created_at: item.last_config_sync_at,
        published_at: item.last_config_sync_at,
        acknowledged_at: item.last_config_sync_at,
        created_by: 'OpsAdmin',
        content_hash: `cfg-${item.id.toLowerCase()}-v${version}`,
        checksum: `cfg-${item.id.toLowerCase()}-v${version}`,
        config: item.agent_config
      };
      if (version <= 1) return [current];
      return [
        current,
        {
          id: `${item.id}-v${version - 1}`,
          probe_id: item.id,
          version: version - 1,
          version_label: `v${version - 1}`,
          status: 'superseded',
          created_at: item.registered_at,
          published_at: item.registered_at,
          created_by: 'OpsAdmin',
          content_hash: `cfg-${item.id.toLowerCase()}-v${version - 1}`,
          checksum: `cfg-${item.id.toLowerCase()}-v${version - 1}`,
          config: item.agent_config
        }
      ];
    },
    refreshProbeConfig(id, actor = 'OpsAdmin') {
      const probe = state.probes.find((item) => item.id === id || item.name === id);
      if (!probe) {
        const error = new Error('探针不存在');
        error.status = 404;
        throw error;
      }
      probe.version = `v${probeVersionNumber(probe.version) + 1}`;
      probe.config_status = 'acknowledged';
      probe.last_config_sync_at = now();
      probe.agent_config = defaultProbeAgentConfig(probe.capabilities);
      recordDomainChange(actor, '刷新探针配置', probe.id, 'probes', 'probe.config.refreshed', { probe_id: probe.id, version: probe.version }, `探针配置已刷新：${probe.name}`);
      return sanitizeProbe(enrichProbe(probe));
    },
    rollbackProbeConfig(id, input = {}, actor = 'OpsAdmin') {
      const probe = state.probes.find((item) => item.id === id || item.name === id);
      if (!probe) {
        const error = new Error('探针不存在');
        error.status = 404;
        throw error;
      }
      const version = Number(input?.version) > 0 ? Number(input.version) : 1;
      probe.version = `v${version}`;
      probe.config_status = 'acknowledged';
      probe.last_config_sync_at = now();
      probe.agent_config = defaultProbeAgentConfig(probe.capabilities);
      recordDomainChange(actor, '回滚探针配置', `${probe.id}@v${version}`, 'probes', 'probe.config.rolled_back', { probe_id: probe.id, version }, `探针配置已回滚：${probe.name}`);
      return sanitizeProbe(enrichProbe(probe));
    },
    retireProbe(id, actor = 'OpsAdmin') {
      const probe = state.probes.find((item) => item.id === id || item.name === id);
      if (!probe) {
        const error = new Error('探针不存在');
        error.status = 404;
        throw error;
      }
      probe.status = 'retired';
      probe.connection_status = 'disconnected';
      probe.active_tasks = 0;
      probe.queue_depth = 0;
      recordDomainChange(actor, '退役探针', probe.id, 'probes', 'probe.retired', { probe_id: probe.id }, `探针已退役：${probe.name}`);
      return sanitizeProbe(enrichProbe(probe));
    },
    claimProbeTasks(input = {}) {
      const probeID = input.probe_id || '';
      const probe = state.probes.find((item) => item.id === probeID || item.name === probeID);
      const limit = Math.min(10, Math.max(1, Number(input.limit) || 5));
      const claimed = [];
      for (const task of state.detectionTasks) {
        if (task.status !== 'pending') continue;
        if (probe && task.probe && task.probe !== probe.id && task.probe !== probe.name) continue;
        task.status = 'running';
        task.claimed_at = now();
        task.claimed_by_probe_id = probe?.id || probeID;
        task.message = '探针已领取，等待回传';
        task.updated_at = now();
        claimed.push(task);
        if (claimed.length >= limit) break;
      }
      if (probe && claimed.length) {
        probe.status = 'online';
        probe.connection_status = 'connected';
        probe.heartbeat_at = now();
        probe.active_tasks = (probe.active_tasks || 0) + claimed.length;
      }
      persist();
      return claimed;
    },
    submitProbeResult(taskId, input, actor = 'probe') {
      const task = state.detectionTasks.find((item) => item.id === taskId);
      if (!task) {
        const error = new Error('任务不存在');
        error.status = 404;
        throw error;
      }
      const success = input.status ? input.status === 'success' : Boolean(input.success);
      task.status = success ? 'success' : 'failed';
      task.result = input;
      task.completed_at = now();
      task.claimed_by_probe_id = input.probe_id || task.claimed_by_probe_id;
      task.latency_ms = Number(input.latency_ms || input.response_time_ms || 0);
      task.message = input.message || '';
      task.updated_at = now();
      recordDomainChange(actor, '回传探针结果', taskId, 'probes', 'probe.result.received', { task_id: taskId, success }, `探针结果已回传：${taskId}`);
      if (!success) {
        const alert = {
          id: nextId('ALT', state.seq.alert++),
          severity: 'P1',
          title: `${task.target} 检测失败`,
          asset: task.related_asset === '-' ? task.target : task.related_asset,
          duration: '刚刚',
          owner: '平台组',
          business_line: task.business_line || '支付业务',
          environment: task.environment || 'prod',
          notify: '已投递',
          workorder: '-',
          status: '待认领',
          detection_task: task.id,
          sourceTaskId: task.id,
          created_at: now()
        };
        state.alerts.unshift(alert);
        event('alerts', 'alert.event.created', { alert_id: alert.id, task_id: task.id });
        notify('OpsAdmin', `新告警：${alert.title}`, { alert_id: alert.id });

        const autoWorkorder = state.strategies.some((strategy) => strategy.enabled && strategy.rule?.actions?.create_workorder);
        if (autoWorkorder) {
          const workorder = {
            id: nextId('WO', state.seq.workorder++),
            type: '告警处理',
            title: `处理 ${alert.title}`,
            applicant: '系统',
            assignee: '待分配',
            status: 'submitted',
            sla: '4h',
            business_line: alert.business_line,
            environment: alert.environment,
            related_object: alert.id,
            relatedAlertId: alert.id,
            created_at: now(),
            updated_at: now()
          };
          state.workorders.unshift(workorder);
          alert.workorder = workorder.id;
          audit('系统', '告警自动创建工单', workorder.id, '成功', { alert_id: alert.id });
          notify('OpsAdmin', `告警已自动创建工单：${workorder.id}`, { alert_id: alert.id, workorder_id: workorder.id });
        }
        persist();
      }
      return task;
    },
    createDetection(input, actor = 'OpsEngineer') {
      const task = {
        id: nextId('DET', state.seq.detection++),
        type: input?.type || 'http',
        target: input?.target,
        probe: input?.probe || 'probe-sh-01',
        status: 'pending',
        related_asset: input?.related_asset || '-',
        business_line: input?.business_line || '支付业务',
        environment: input?.environment || 'prod',
        created_at: now(),
        updated_at: now()
      };
      state.detectionTasks.unshift(task);
      audit(actor, '创建一次性检测', task.id);
      notify(actor, `检测任务已创建：${task.id}`, { task_id: task.id });
      persist();
      return task;
    },
    listDetectionTasks(role = 'OpsAdmin') {
      return applyDataScope(role, 'assets', state.detectionTasks);
    },
    getDetectionTask(id, role = 'OpsAdmin') {
      const task = state.detectionTasks.find((item) => item.id === id);
      if (!task) {
        const error = new Error('检测任务不存在');
        error.status = 404;
        throw error;
      }
      assertDataScope(role, 'assets', task);
      return task;
    },
    validateCmdbDomain(domain) {
      const record = state.assetRecords.find((item) => item.name === domain || item.domain === domain || item.target === domain);
      return {
        domain,
        matched: Boolean(record),
        model_id: record?.model_id || null,
        asset_id: record?.id || null,
        missing_fields: record ? [] : ['owner', 'environment'],
        recommendation: record ? '可关联资产并进入监控策略' : '未命中资产记录，建议先创建模型并同步数据'
      };
    },
    listAuditLogs() {
      return state.auditLogs;
    },
    listNotifications() {
      return state.notifications;
    }
  };
}
