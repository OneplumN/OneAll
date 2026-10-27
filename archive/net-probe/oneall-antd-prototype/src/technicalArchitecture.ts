export type BackendFramework = 'go-gin';
export type DatabaseEngine = 'postgresql';
export type AuthMode = 'jwt-ldap-rbac';
export type EventDeliveryMode = 'outbox-redis-stream';
export type ProbeProtocol = 'https-json';

export const technicalArchitectureDecision = {
  backend: {
    framework: 'go-gin' as BackendFramework,
    reason: '新 API 边界以轻量服务为目标，先稳定 /api/v1 契约，再迁移实现',
    migration: '不第一阶段强行重建所有数据表，旧实现可作为兼容入口'
  },
  database: {
    primary: 'postgresql' as DatabaseEngine,
    jsonFields: '资产记录 fields、字段映射 transform_rule、事件 payload 使用 JSONB',
    migration: '按迁移阶段执行，支持双读校验和回滚'
  },
  auth: {
    mode: 'jwt-ldap-rbac' as AuthMode,
    token: '业务 API 使用 JWT，避免依赖 Cookie；企业用户通过 LDAP 同步',
    authorization: '页面权限和 API 权限使用同一套角色动作矩阵'
  },
  eventDelivery: {
    mode: 'outbox-redis-stream' as EventDeliveryMode,
    sourceOfTruth: '业务库 outbox/event_log 是事实来源',
    transport: 'Redis Streams 用于轻量异步投递和重试，不作为最终事实表'
  },
  redis: {
    allowed: ['事件投递缓冲', '短期锁', '限流计数', '探针任务领取窗口'],
    forbidden: ['业务事实数据唯一存储', '长期审计日志', '资产记录主存储']
  },
  timescale: {
    optional: true,
    useWhen: ['探针指标历史', '检测耗时趋势', '高频执行结果聚合'],
    notFor: ['资产模型字段', '权限矩阵', '工单状态机']
  },
  probe: {
    protocol: 'https-json' as ProbeProtocol,
    auth: '探针注册后获得节点 token，后续心跳、领取任务、回传结果均携带 token',
    endpoints: [
      'POST /api/v1/probes/register',
      'GET /api/v1/probes/nodes',
      'GET /api/v1/probes/nodes/health',
      'GET /api/v1/probes/nodes/{id}/runtime',
      'GET /api/v1/probes/nodes/{id}/metrics/history',
      'POST /api/v1/probes/nodes/{id}/config/refresh',
      'GET /api/v1/probes/nodes/{id}/config/versions',
      'POST /api/v1/probes/nodes/{id}/config/rollback',
      'POST /api/v1/probes/nodes/{id}/retire',
      'POST /api/v1/probes/tasks/claim',
      'POST /api/v1/probes/tasks/{task_id}/result'
    ]
  }
} as const;

export function canUseRedisFor(purpose: string) {
  return (technicalArchitectureDecision.redis.allowed as readonly string[]).includes(purpose);
}

export function mustPersistInDatabase(purpose: string) {
  return (technicalArchitectureDecision.redis.forbidden as readonly string[]).includes(purpose);
}

export function shouldUseTimescaleFor(purpose: string) {
  return (technicalArchitectureDecision.timescale.useWhen as readonly string[]).includes(purpose);
}

export function validateProbeRequestHeaders(headers: Record<string, string | undefined>) {
  const errors: string[] = [];
  if (!headers['x-oneall-probe-id']) errors.push('x-oneall-probe-id 必填');
  if (!headers.authorization?.startsWith('Bearer ')) errors.push('authorization 必须使用 Bearer token');
  if (!headers['x-oneall-trace-id']) errors.push('x-oneall-trace-id 必填');
  return { valid: errors.length === 0, errors };
}
