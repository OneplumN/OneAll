export type Role = 'PlatformAdmin' | 'OpsAdmin' | 'OpsEngineer' | 'Approver' | 'Viewer';

export type PermissionAction =
  | 'read'
  | 'create'
  | 'update'
  | 'delete'
  | 'execute'
  | 'approve'
  | 'close'
  | 'manage'
  | 'sync'
  | 'reference';

export type PermissionModule =
  | 'monitoringOverview'
  | 'alertEvents'
  | 'monitoringPolicies'
  | 'probeNodes'
  | 'assetCenter'
  | 'oneOffDetection'
  | 'workorders'
  | 'usersAndRoles'
  | 'credentials'
  | 'dataSources'
  | 'notificationsWebhooks'
  | 'auditLogs';

export const permissionMatrix: Record<PermissionModule, Record<Role, PermissionAction[]>> = {
  monitoringOverview: {
    PlatformAdmin: ['read'],
    OpsAdmin: ['read'],
    OpsEngineer: ['read'],
    Approver: ['read'],
    Viewer: ['read']
  },
  alertEvents: {
    PlatformAdmin: ['read', 'close'],
    OpsAdmin: ['read', 'close'],
    OpsEngineer: ['read', 'execute'],
    Approver: ['read'],
    Viewer: ['read']
  },
  monitoringPolicies: {
    PlatformAdmin: ['read', 'create', 'update'],
    OpsAdmin: ['read', 'create', 'update', 'execute'],
    OpsEngineer: ['read', 'create', 'update'],
    Approver: ['read'],
    Viewer: ['read']
  },
  probeNodes: {
    PlatformAdmin: ['read', 'manage'],
    OpsAdmin: ['read', 'manage'],
    OpsEngineer: ['read'],
    Approver: [],
    Viewer: ['read']
  },
  assetCenter: {
    PlatformAdmin: ['read', 'create', 'update'],
    OpsAdmin: ['read', 'create', 'update', 'sync'],
    OpsEngineer: ['read', 'create', 'update'],
    Approver: ['read'],
    Viewer: ['read']
  },
  oneOffDetection: {
    PlatformAdmin: ['read', 'execute'],
    OpsAdmin: ['read', 'execute'],
    OpsEngineer: ['read', 'execute'],
    Approver: ['read'],
    Viewer: ['read']
  },
  workorders: {
    PlatformAdmin: ['read', 'manage'],
    OpsAdmin: ['read', 'manage'],
    OpsEngineer: ['read', 'create', 'execute'],
    Approver: ['approve'],
    Viewer: ['read']
  },
  usersAndRoles: {
    PlatformAdmin: ['read', 'create', 'update', 'delete'],
    OpsAdmin: [],
    OpsEngineer: [],
    Approver: [],
    Viewer: []
  },
  credentials: {
    PlatformAdmin: ['read', 'create', 'update', 'delete', 'manage'],
    OpsAdmin: ['read', 'reference'],
    OpsEngineer: ['reference'],
    Approver: [],
    Viewer: []
  },
  dataSources: {
    PlatformAdmin: ['read', 'create', 'update', 'delete'],
    OpsAdmin: ['read', 'create', 'update'],
    OpsEngineer: ['read'],
    Approver: [],
    Viewer: []
  },
  notificationsWebhooks: {
    PlatformAdmin: ['read', 'create', 'update', 'delete'],
    OpsAdmin: ['read', 'create', 'update'],
    OpsEngineer: ['read'],
    Approver: [],
    Viewer: []
  },
  auditLogs: {
    PlatformAdmin: ['read'],
    OpsAdmin: ['read'],
    OpsEngineer: [],
    Approver: [],
    Viewer: []
  }
};

export function hasPermission(role: Role, module: PermissionModule, action: PermissionAction) {
  return permissionMatrix[module][role].includes(action);
}

export type WorkorderStatus =
  | 'draft'
  | 'submitted'
  | 'rejected'
  | 'approved'
  | 'executing'
  | 'completed'
  | 'failed'
  | 'canceled'
  | 'withdrawn';

export const workorderTransitions: Record<WorkorderStatus, WorkorderStatus[]> = {
  draft: ['submitted', 'withdrawn'],
  submitted: ['approved', 'rejected', 'withdrawn'],
  rejected: ['draft'],
  approved: ['executing', 'canceled'],
  executing: ['completed', 'failed'],
  completed: [],
  failed: ['executing'],
  canceled: [],
  withdrawn: ['submitted']
};

export const workorderStatusMeta: Record<WorkorderStatus, { tab: string; actions: string[] }> = {
  draft: { tab: '我的申请', actions: ['编辑', '提交', '删除'] },
  submitted: { tab: '我的审批', actions: ['审批', '驳回', '撤回'] },
  rejected: { tab: '我的申请', actions: ['重新编辑', '归档'] },
  approved: { tab: '工单详情', actions: ['执行', '取消'] },
  executing: { tab: '工单详情', actions: ['更新进度', '标记失败', '完成'] },
  completed: { tab: '工单详情', actions: ['查看', '关联告警关闭记录'] },
  failed: { tab: '工单详情', actions: ['重试', '转人工处理'] },
  canceled: { tab: '工单详情', actions: ['查看'] },
  withdrawn: { tab: '我的申请', actions: ['查看', '重新提交'] }
};

export function canTransitionWorkorder(from: WorkorderStatus, to: WorkorderStatus) {
  return workorderTransitions[from].includes(to);
}

export function getWorkorderTabs() {
  return ['全部', ...Array.from(new Set(Object.values(workorderStatusMeta).map((item) => item.tab)))];
}

export type AlertOperator = 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'not_in' | 'contains' | 'regex';
export type AlertSeverity = 'info' | 'warning' | 'critical';

export type AlertCondition = {
  operator: AlertOperator;
  value: unknown;
  duration?: string;
  consecutive?: number;
};

export type AlertRuleDsl = {
  scope: {
    asset_model: string;
    asset_filter?: Record<string, unknown>;
  };
  signal: {
    metric: string;
    source: string;
  };
  condition: AlertCondition;
  severity: AlertSeverity;
  recovery?: AlertCondition;
  actions: {
    notify_channels: string[];
    create_workorder: boolean;
  };
};

export const alertOperators: AlertOperator[] = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'not_in', 'contains', 'regex'];
export const alertSeverities: AlertSeverity[] = ['info', 'warning', 'critical'];

export function validateAlertRuleDsl(rule: Partial<AlertRuleDsl>) {
  const errors: string[] = [];

  if (!rule.scope?.asset_model) errors.push('scope.asset_model 必填');
  if (!rule.signal?.metric) errors.push('signal.metric 必填');
  if (!rule.signal?.source) errors.push('signal.source 必填');
  validateCondition(rule.condition, 'condition', errors);
  if (rule.recovery) validateCondition(rule.recovery, 'recovery', errors);
  if (!rule.severity || !alertSeverities.includes(rule.severity)) errors.push('severity 必须是 info、warning、critical');
  if (!Array.isArray(rule.actions?.notify_channels)) errors.push('actions.notify_channels 必须是数组');
  if (typeof rule.actions?.create_workorder !== 'boolean') errors.push('actions.create_workorder 必须是布尔值');

  return { valid: errors.length === 0, errors };
}

function validateCondition(condition: Partial<AlertCondition> | undefined, path: string, errors: string[]) {
  if (!condition) {
    errors.push(`${path} 必填`);
    return;
  }
  if (!condition.operator || !alertOperators.includes(condition.operator)) {
    errors.push(`${path}.operator 不支持`);
  }
  if (!('value' in condition)) {
    errors.push(`${path}.value 必填`);
  }
  if (condition.duration && !/^\d+[smhd]$/.test(condition.duration)) {
    errors.push(`${path}.duration 格式应为 3m、1h 等`);
  }
  if (condition.consecutive !== undefined && (!Number.isInteger(condition.consecutive) || condition.consecutive < 1)) {
    errors.push(`${path}.consecutive 必须是正整数`);
  }
}

export function evaluateAlertCondition(actual: unknown, condition: AlertCondition) {
  switch (condition.operator) {
    case 'eq':
      return actual === condition.value;
    case 'ne':
      return actual !== condition.value;
    case 'gt':
      return Number(actual) > Number(condition.value);
    case 'gte':
      return Number(actual) >= Number(condition.value);
    case 'lt':
      return Number(actual) < Number(condition.value);
    case 'lte':
      return Number(actual) <= Number(condition.value);
    case 'in':
      return Array.isArray(condition.value) && condition.value.includes(actual);
    case 'not_in':
      return Array.isArray(condition.value) && !condition.value.includes(actual);
    case 'contains':
      return String(actual).includes(String(condition.value));
    case 'regex':
      return new RegExp(String(condition.value)).test(String(actual));
    default:
      return false;
  }
}

export function previewAlertRule(rule: AlertRuleDsl, sample: Record<string, unknown>) {
  const validation = validateAlertRuleDsl(rule);
  if (!validation.valid) {
    return { triggered: false, recovered: false, errors: validation.errors };
  }

  const actual = sample[rule.signal.metric];
  const triggered = evaluateAlertCondition(actual, rule.condition);
  const recovered = rule.recovery ? evaluateAlertCondition(actual, rule.recovery) : false;
  return { triggered, recovered, errors: [] };
}
