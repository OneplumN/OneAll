export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export type ApiDomain =
  | 'auth'
  | 'notifications'
  | 'detection'
  | 'workorders'
  | 'assets'
  | 'monitoring'
  | 'alerts'
  | 'probes'
  | 'settings'
  | 'tools';

export type ApiEndpoint = {
  key: string;
  domain: ApiDomain;
  method: HttpMethod;
  path: `/api/v1/${string}`;
  description: string;
};

export const apiV1Endpoints: ApiEndpoint[] = [
  { key: 'auth.login', domain: 'auth', method: 'POST', path: '/api/v1/auth/login', description: '用户名密码登录' },
  { key: 'auth.profile', domain: 'auth', method: 'GET', path: '/api/v1/auth/profile', description: '当前用户、角色、权限' },
  { key: 'notifications.list', domain: 'notifications', method: 'GET', path: '/api/v1/notifications', description: '站内通知列表' },
  { key: 'notifications.stream', domain: 'notifications', method: 'GET', path: '/api/v1/notifications/stream', description: 'SSE 通知流' },

  { key: 'detection.oneOff.create', domain: 'detection', method: 'POST', path: '/api/v1/detection/one-off', description: '发起一次性检测' },
  { key: 'detection.tasks.list', domain: 'detection', method: 'GET', path: '/api/v1/detection/tasks', description: '检测任务列表' },
  { key: 'detection.task.detail', domain: 'detection', method: 'GET', path: '/api/v1/detection/tasks/{id}', description: '检测任务详情' },
  { key: 'detection.cmdb.validate', domain: 'detection', method: 'GET', path: '/api/v1/detection/cmdb/validate', description: 'CMDB 域名校验' },

  { key: 'workorders.create', domain: 'workorders', method: 'POST', path: '/api/v1/workorders/requests', description: '提交工单' },
  { key: 'workorders.list', domain: 'workorders', method: 'GET', path: '/api/v1/workorders/requests', description: '工单列表' },
  { key: 'workorders.detail', domain: 'workorders', method: 'GET', path: '/api/v1/workorders/requests/{id}', description: '工单详情' },
  { key: 'workorders.approve', domain: 'workorders', method: 'POST', path: '/api/v1/workorders/requests/{id}/approve', description: '审批通过' },
  { key: 'workorders.reject', domain: 'workorders', method: 'POST', path: '/api/v1/workorders/requests/{id}/reject', description: '审批驳回' },
  { key: 'workorders.batch', domain: 'workorders', method: 'POST', path: '/api/v1/workorders/requests/batch', description: '工单批量操作' },

  { key: 'assets.models.list', domain: 'assets', method: 'GET', path: '/api/v1/assets/models', description: '资产模型列表' },
  { key: 'assets.models.create', domain: 'assets', method: 'POST', path: '/api/v1/assets/models', description: '创建资产模型' },
  { key: 'assets.models.update', domain: 'assets', method: 'PUT', path: '/api/v1/assets/models/{model_id}', description: '更新模型和字段' },
  { key: 'assets.records.query', domain: 'assets', method: 'GET', path: '/api/v1/assets/records/query', description: '资产记录查询' },
  { key: 'assets.records.batch', domain: 'assets', method: 'POST', path: '/api/v1/assets/records/batch', description: '资产批量操作' },
  { key: 'assets.sync.preview', domain: 'assets', method: 'POST', path: '/api/v1/assets/models/{model_id}/sync/preview', description: '同步预览' },
  { key: 'assets.sync.run', domain: 'assets', method: 'POST', path: '/api/v1/assets/models/{model_id}/sync', description: '执行同步' },
  { key: 'assets.sync.history', domain: 'assets', method: 'GET', path: '/api/v1/assets/sync/runs', description: '同步历史' },

  { key: 'monitoring.overview', domain: 'monitoring', method: 'GET', path: '/api/v1/monitoring/overview', description: '监控总览' },
  { key: 'monitoring.strategies.list', domain: 'monitoring', method: 'GET', path: '/api/v1/monitoring/strategies', description: '监控策略列表' },
  { key: 'monitoring.strategies.create', domain: 'monitoring', method: 'POST', path: '/api/v1/monitoring/strategies', description: '创建策略' },
  { key: 'monitoring.strategies.batch', domain: 'monitoring', method: 'POST', path: '/api/v1/monitoring/strategies/batch', description: '策略批量操作' },
  { key: 'alerts.events.list', domain: 'alerts', method: 'GET', path: '/api/v1/alerts/events', description: '告警事件列表' },
  { key: 'alerts.events.detail', domain: 'alerts', method: 'GET', path: '/api/v1/alerts/events/{id}', description: '告警详情' },
  { key: 'alerts.events.batch', domain: 'alerts', method: 'POST', path: '/api/v1/alerts/events/batch', description: '告警批量操作' },

  { key: 'probes.register', domain: 'probes', method: 'POST', path: '/api/v1/probes/register', description: '探针注册' },
  { key: 'probes.nodes.list', domain: 'probes', method: 'GET', path: '/api/v1/probes/nodes', description: '探针节点列表' },
  { key: 'probes.nodes.health', domain: 'probes', method: 'GET', path: '/api/v1/probes/nodes/health', description: '探针健康摘要' },
  { key: 'probes.nodes.runtime', domain: 'probes', method: 'GET', path: '/api/v1/probes/nodes/{id}/runtime', description: '节点运行态' },
  { key: 'probes.nodes.heartbeat', domain: 'probes', method: 'POST', path: '/api/v1/probes/nodes/{id}/heartbeat', description: '节点心跳' },
  { key: 'probes.nodes.metricsHistory', domain: 'probes', method: 'GET', path: '/api/v1/probes/nodes/{id}/metrics/history', description: '节点指标历史' },
  { key: 'probes.nodes.retire', domain: 'probes', method: 'POST', path: '/api/v1/probes/nodes/{id}/retire', description: '退役探针节点' },
  { key: 'probes.config.versions', domain: 'probes', method: 'GET', path: '/api/v1/probes/nodes/{id}/config/versions', description: '配置版本' },
  { key: 'probes.config.refresh', domain: 'probes', method: 'POST', path: '/api/v1/probes/nodes/{id}/config/refresh', description: '下发最新配置' },
  { key: 'probes.config.rollback', domain: 'probes', method: 'POST', path: '/api/v1/probes/nodes/{id}/config/rollback', description: '回滚配置版本' },
  { key: 'probes.tasks.claim', domain: 'probes', method: 'POST', path: '/api/v1/probes/tasks/claim', description: '任务领取' },
  { key: 'probes.tasks.result', domain: 'probes', method: 'POST', path: '/api/v1/probes/tasks/{task_id}/result', description: '任务结果回传' },
  { key: 'probes.schedules.result', domain: 'probes', method: 'POST', path: '/api/v1/probes/schedules/{schedule_id}/result', description: '调度结果回传' },

  { key: 'settings.permissions.catalog', domain: 'settings', method: 'GET', path: '/api/v1/settings/permissions/catalog', description: '权限目录' },
  { key: 'settings.users.list', domain: 'settings', method: 'GET', path: '/api/v1/settings/users', description: '用户列表' },
  { key: 'settings.dataSources.list', domain: 'settings', method: 'GET', path: '/api/v1/settings/data-sources', description: '数据源列表' },
  { key: 'settings.credentials.list', domain: 'settings', method: 'GET', path: '/api/v1/settings/credentials', description: '凭据列表' },
  { key: 'settings.notificationChannels.list', domain: 'settings', method: 'GET', path: '/api/v1/settings/notification-channels', description: '通知通道列表' },
  { key: 'settings.notificationTemplates.list', domain: 'settings', method: 'GET', path: '/api/v1/settings/notification-templates', description: '通知模板列表' },
  { key: 'settings.webhooks.list', domain: 'settings', method: 'GET', path: '/api/v1/settings/webhooks', description: '出站 Webhook 列表' },
  { key: 'settings.webhooks.test', domain: 'settings', method: 'POST', path: '/api/v1/settings/webhooks/{id}/test', description: '测试 Webhook' },
  { key: 'settings.auditLogs.list', domain: 'settings', method: 'GET', path: '/api/v1/settings/audit-logs', description: '审计日志列表' },

  { key: 'tools.ipRegex.compile', domain: 'tools', method: 'POST', path: '/api/v1/tools/ip-regex/compile', description: 'IP 列表生成正则' },
  { key: 'tools.ipRegex.expand', domain: 'tools', method: 'POST', path: '/api/v1/tools/ip-regex/expand', description: '正则展开 IP' }
];

export function getEndpoint(key: string) {
  return apiV1Endpoints.find((endpoint) => endpoint.key === key);
}

export function normalizeLegacyApiPath(path: string) {
  if (path.startsWith('/api/v1/')) return path;
  if (!path.startsWith('/api/')) return path;
  return `/api/v1/${path.slice('/api/'.length).replace(/^alerts\/checks/, 'monitoring/strategies').replace(/^monitoring\/requests/, 'workorders/requests')}`.replace(/\/+$/, '');
}

export type ProbeStatus = 'registered' | 'online' | 'degraded' | 'offline' | 'retired';

export const probeTransitions: Record<ProbeStatus, ProbeStatus[]> = {
  registered: ['online'],
  online: ['degraded', 'offline', 'retired'],
  degraded: ['online', 'offline'],
  offline: ['online', 'retired'],
  retired: []
};

export const probeLifecyclePolicy = {
  heartbeatIntervalSeconds: 30,
  degradedAfterMissedHeartbeats: 2,
  offlineAfterSeconds: 300,
  claimTimeoutGraceSeconds: 30
} as const;

export function canTransitionProbe(from: ProbeStatus, to: ProbeStatus) {
  return probeTransitions[from].includes(to);
}

export function classifyProbeStatus(secondsSinceHeartbeat: number, configStale = false): ProbeStatus {
  if (secondsSinceHeartbeat >= probeLifecyclePolicy.offlineAfterSeconds) return 'offline';
  if (secondsSinceHeartbeat >= probeLifecyclePolicy.heartbeatIntervalSeconds * probeLifecyclePolicy.degradedAfterMissedHeartbeats || configStale) return 'degraded';
  return 'online';
}

export const domainEventTypes = [
  'asset.sync.started',
  'asset.sync.completed',
  'asset.sync.failed',
  'monitoring.strategy.enabled',
  'probe.result.received',
  'alert.event.created',
  'workorder.completed'
] as const;

export type DomainEventType = (typeof domainEventTypes)[number];

export type DomainEventEnvelope = {
  event_id: string;
  trace_id: string;
  event_type: DomainEventType;
  producer: ApiDomain;
  payload: Record<string, unknown>;
  created_at: string;
};

export function validateDomainEvent(event: Partial<DomainEventEnvelope>) {
  const errors: string[] = [];

  if (!event.event_id) errors.push('event_id 必填');
  if (!event.trace_id) errors.push('trace_id 必填');
  if (!event.event_type || !domainEventTypes.includes(event.event_type as DomainEventType)) errors.push('event_type 不支持');
  if (!event.producer) errors.push('producer 必填');
  if (!event.payload || typeof event.payload !== 'object') errors.push('payload 必须是对象');
  if (!event.created_at || Number.isNaN(Date.parse(event.created_at))) errors.push('created_at 必须是 ISO 时间');

  return { valid: errors.length === 0, errors };
}

export const migrationPhases = [
  { phase: 1, name: '代码结构和页面重构', writeMode: 'legacy', requiredGate: '产品边界、API 契约和页面体验稳定' },
  { phase: 2, name: '新旧字段映射和兼容读取', writeMode: 'legacy', requiredGate: '新 API 可输出目标字段' },
  { phase: 3, name: '后台迁移任务', writeMode: 'legacy', requiredGate: '迁移任务可断点续跑' },
  { phase: 4, name: '双读校验', writeMode: 'legacy', requiredGate: '新旧数据读取一致' },
  { phase: 5, name: '切换写入', writeMode: 'target', requiredGate: '备份、回滚和校验方案完成' },
  { phase: 6, name: '清理旧结构', writeMode: 'target', requiredGate: '迁移验收完成' }
] as const;
