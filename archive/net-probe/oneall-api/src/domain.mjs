export const roles = ['PlatformAdmin', 'OpsAdmin', 'OpsEngineer', 'Approver', 'Viewer'];

export const permissionMatrix = {
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

export const dataScopeMatrix = {
  PlatformAdmin: { assets: 'all', alerts: 'all', workorders: 'all', auditLogs: 'all' },
  OpsAdmin: { assets: 'all', alerts: 'all', workorders: 'all', auditLogs: 'all' },
  OpsEngineer: { assets: 'owned_or_prod', alerts: 'owned_or_team', workorders: 'owned_or_assigned', auditLogs: 'none' },
  Approver: { assets: 'prod', alerts: 'readable', workorders: 'approval_queue', auditLogs: 'none' },
  Viewer: { assets: 'prod', alerts: 'readable', workorders: 'readable', auditLogs: 'none' }
};

export const workorderTransitions = {
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

export const workorderStatusMeta = {
  draft: { tab: '我的申请', actions: ['编辑', '提交', '删除'] },
  submitted: { tab: '待我审批', actions: ['审批', '驳回', '撤回'] },
  rejected: { tab: '我的申请', actions: ['重新编辑', '归档'] },
  approved: { tab: '待我执行', actions: ['执行', '取消'] },
  executing: { tab: '待我执行', actions: ['更新进度', '标记失败', '完成'] },
  completed: { tab: '工单详情', actions: ['查看', '关联告警关闭记录'] },
  failed: { tab: '工单详情', actions: ['重试', '转人工处理'] },
  canceled: { tab: '工单详情', actions: ['查看'] },
  withdrawn: { tab: '我的申请', actions: ['查看', '重新提交'] }
};

export const alertOperators = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'not_in', 'contains', 'regex'];
export const alertSeverities = ['info', 'warning', 'critical'];
export const assetFieldTypes = ['string', 'number', 'boolean', 'datetime', 'enum', 'ip', 'url', 'user'];

export function hasPermission(role, module, action) {
  return Boolean(permissionMatrix[module]?.[role]?.includes(action));
}

export function assertPermission(role, module, action) {
  if (!hasPermission(role, module, action)) {
    const error = new Error(`角色 ${role} 缺少 ${module}.${action} 权限`);
    error.status = 403;
    throw error;
  }
}

export function applyDataScope(role, domain, items) {
  const scope = dataScopeMatrix[role]?.[domain] || 'none';
  if (scope === 'all') return items;
  if (scope === 'none') return [];
  return items.filter((item) => matchesDataScope(scope, item));
}

export function assertDataScope(role, domain, item) {
  if (!applyDataScope(role, domain, [item]).length) {
    const error = new Error(`角色 ${role} 无权访问该${domain}数据`);
    error.status = 403;
    throw error;
  }
}

function matchesDataScope(scope, item) {
  if (scope === 'prod') return item.environment === 'prod' || item.env === 'prod' || item.environment === undefined;
  if (scope === 'owned_or_prod') return item.owner === 'OpsEngineer' || item.created_by === 'OpsEngineer' || item.environment === 'prod' || item.env === 'prod';
  if (scope === 'owned_or_team') return ['OpsEngineer', '平台组', '张三', '李四', '王五'].includes(item.owner) || item.team === '平台组' || item.business_line === '支付业务';
  if (scope === 'owned_or_assigned') return item.applicant === 'OpsEngineer' || item.assignee === 'OpsEngineer' || item.assignee === '待分配' || item.business_line === '支付业务';
  if (scope === 'approval_queue') return ['submitted', 'approved'].includes(item.status);
  if (scope === 'readable') return item.visibility !== 'private';
  return false;
}

export function canTransitionWorkorder(from, to) {
  return Boolean(workorderTransitions[from]?.includes(to));
}

export function transitionWorkorder(workorder, nextStatus) {
  if (!canTransitionWorkorder(workorder.status, nextStatus)) {
    const error = new Error(`工单状态不能从 ${workorder.status} 流转到 ${nextStatus}`);
    error.status = 409;
    throw error;
  }
  return { ...workorder, status: nextStatus, updated_at: new Date().toISOString() };
}

export function validateAlertRuleDsl(rule) {
  const errors = [];
  if (!rule?.scope?.asset_model) errors.push('scope.asset_model 必填');
  if (!rule?.signal?.metric) errors.push('signal.metric 必填');
  if (!rule?.signal?.source) errors.push('signal.source 必填');
  validateCondition(rule?.condition, 'condition', errors);
  if (rule?.recovery) validateCondition(rule.recovery, 'recovery', errors);
  if (!alertSeverities.includes(rule?.severity)) errors.push('severity 必须是 info、warning、critical');
  if (!Array.isArray(rule?.actions?.notify_channels)) errors.push('actions.notify_channels 必须是数组');
  if (typeof rule?.actions?.create_workorder !== 'boolean') errors.push('actions.create_workorder 必须是布尔值');
  return { valid: errors.length === 0, errors };
}

export function validateAssetFields(fields = []) {
  const errors = [];
  if (!Array.isArray(fields)) {
    return { valid: false, errors: ['fields 必须是数组'] };
  }
  const keys = new Set();
  fields.forEach((field, index) => {
    const path = `fields[${index}]`;
    if (!field?.key || !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(field.key)) errors.push(`${path}.key 必须是字母开头的标识符`);
    if (field?.key && keys.has(field.key)) errors.push(`${path}.key 重复`);
    if (field?.key) keys.add(field.key);
    if (!assetFieldTypes.includes(field?.type)) errors.push(`${path}.type 不支持`);
    if (field?.type === 'enum' && (!Array.isArray(field.options) || !field.options.length)) errors.push(`${path}.options 必须包含枚举值`);
  });
  return { valid: errors.length === 0, errors };
}

export function validateAssetRecord(model, record) {
  const errors = [];
  for (const field of model.fields || []) {
    const value = record?.[field.key];
    if (field.required && (value === undefined || value === null || value === '')) errors.push(`${field.key} 必填`);
    if (value === undefined || value === null || value === '') continue;
    if (field.type === 'number' && Number.isNaN(Number(value))) errors.push(`${field.key} 必须是数字`);
    if (field.type === 'boolean' && typeof value !== 'boolean') errors.push(`${field.key} 必须是布尔值`);
    if (field.type === 'datetime' && Number.isNaN(Date.parse(String(value)))) errors.push(`${field.key} 必须是可解析时间`);
    if (field.type === 'enum' && !field.options?.includes(value)) errors.push(`${field.key} 不在枚举范围内`);
    if (field.type === 'ip' && !isIpv4(String(value))) errors.push(`${field.key} 必须是 IPv4`);
    if (field.type === 'url' && !/^https?:\/\//.test(String(value))) errors.push(`${field.key} 必须是 URL`);
  }
  return { valid: errors.length === 0, errors };
}

function validateCondition(condition, path, errors) {
  if (!condition) {
    errors.push(`${path} 必填`);
    return;
  }
  if (!alertOperators.includes(condition.operator)) errors.push(`${path}.operator 不支持`);
  if (!Object.prototype.hasOwnProperty.call(condition, 'value')) errors.push(`${path}.value 必填`);
  if (condition.duration && !/^\d+[smhd]$/.test(condition.duration)) errors.push(`${path}.duration 格式应为 3m、1h 等`);
  if (condition.consecutive !== undefined && (!Number.isInteger(condition.consecutive) || condition.consecutive < 1)) {
    errors.push(`${path}.consecutive 必须是正整数`);
  }
}

export function evaluateAlertCondition(actual, condition) {
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

export function previewAlertRule(rule, sample) {
  const validation = validateAlertRuleDsl(rule);
  if (!validation.valid) return { triggered: false, recovered: false, errors: validation.errors };
  const actual = sample[rule.signal.metric];
  return {
    triggered: evaluateAlertCondition(actual, rule.condition),
    recovered: rule.recovery ? evaluateAlertCondition(actual, rule.recovery) : false,
    errors: []
  };
}

export function compileIpRegexFromText(input) {
  const lines = input.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const valid = [];
  const invalidIps = [];
  for (const line of lines) {
    if (isIpv4(line)) valid.push(line);
    else invalidIps.push(line);
  }
  const unique = [...new Set(valid)];
  const regex = unique.length ? `^(${unique.map((ip) => ip.replaceAll('.', '\\.')).join('|')})$` : '';
  return { regex, matchedCount: unique.length, invalidIps };
}

export function expandIpRegex(regex, limit = 500) {
  const match = String(regex || '').match(/^\^\((.+)\)\$$/);
  if (!match) {
    const error = new Error('仅支持展开本工具生成的精确 IP 正则');
    error.status = 400;
    throw error;
  }
  const ips = match[1].split('|').map((item) => item.replaceAll('\\.', '.')).filter(isIpv4);
  return { items: ips.slice(0, limit), total: ips.length, truncated: ips.length > limit };
}

function isIpv4(value) {
  const parts = value.split('.');
  return parts.length === 4 && parts.every((part) => /^\d+$/.test(part) && Number(part) >= 0 && Number(part) <= 255 && String(Number(part)) === part);
}
