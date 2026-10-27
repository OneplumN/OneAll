export const routeRegistry = [
  { key: 'monitoring-overview', path: '/monitoring/overview', module: '监控与告警', label: '监控总览', level: 2, nav: true },
  { key: 'alerts', path: '/monitoring/alerts', module: '监控与告警', label: '告警事件', level: 2, nav: true },
  { key: 'alert-detail', path: '/monitoring/alerts/:id', module: '监控与告警', label: '告警详情', level: 3, parent: 'alerts' },
  { key: 'policies', path: '/monitoring/policies', module: '监控与告警', label: '监控策略', level: 2, nav: true },
  { key: 'policy-detail', path: '/monitoring/policies/:id', module: '监控与告警', label: '策略详情', level: 3, parent: 'policies' },
  { key: 'policy-rule-config', path: '/monitoring/policies/:id/rule', module: '监控与告警', label: '规则配置', level: 3, parent: 'policies' },
  { key: 'probes', path: '/monitoring/probes', module: '监控与告警', label: '探针节点', level: 2, nav: true },
  { key: 'probe-detail', path: '/monitoring/probes/:id', module: '监控与告警', label: '探针详情', level: 3, parent: 'probes' },
  { key: 'execution-logs', path: '/monitoring/execution-logs', module: '监控与告警', label: '执行日志', level: 2, nav: true },
  { key: 'execution-log-detail', path: '/monitoring/execution-logs/:id', module: '监控与告警', label: '日志详情', level: 3, parent: 'execution-logs' },

  { key: 'assets', path: '/assets/models', module: '资产中心', label: '模型资产', level: 2, nav: true },
  { key: 'asset-model-management', path: '/assets/model-management', module: '资产中心', label: '模型管理', level: 2, nav: true },
  { key: 'asset-new', path: '/assets/models/new', module: '资产中心', label: '新建模型', level: 3, parent: 'assets' },
  { key: 'asset-detail', path: '/assets/models/:modelId', module: '资产中心', label: '模型详情', level: 3, parent: 'assets' },
  { key: 'asset-records', path: '/assets/models/:modelId/records', module: '资产中心', label: '数据记录', level: 3, parent: 'asset-detail' },
  { key: 'asset-fields', path: '/assets/models/:modelId/fields', module: '资产中心', label: '字段配置', level: 3, parent: 'asset-detail' },
  { key: 'asset-sync-config', path: '/assets/models/:modelId/sync-config', module: '资产中心', label: '同步配置', level: 3, parent: 'asset-detail' },
  { key: 'asset-sync-history', path: '/assets/models/:modelId/sync-history', module: '资产中心', label: '同步历史', level: 3, parent: 'asset-detail' },
  { key: 'asset-permissions-audit', path: '/assets/models/:modelId/permissions-audit', module: '资产中心', label: '权限与审计', level: 3, parent: 'asset-detail' },
  { key: 'asset-sync', path: '/assets/sync-tasks', module: '资产中心', label: '同步任务', level: 2, nav: true },
  { key: 'asset-sync-preview', path: '/assets/sync-tasks/:id/preview', module: '资产中心', label: '同步预览', level: 3, parent: 'asset-sync' },
  { key: 'asset-sync-history-list', path: '/assets/sync-history', module: '资产中心', label: '同步历史', level: 3, parent: 'asset-sync' },
  { key: 'asset-mapping-templates', path: '/assets/mapping-templates', module: '资产中心', label: '字段映射模板', level: 3, parent: 'asset-detail' },
  { key: 'asset-import-export-records', path: '/assets/import-export-records', module: '资产中心', label: '导入导出记录', level: 3, nav: false, parent: 'asset-sync' },

  { key: 'detection', path: '/detection/domain', module: '一次性检验', label: '域名拨测', level: 2, nav: true },
  { key: 'certificate-detection', path: '/detection/certificate', module: '一次性检验', label: '证书检测', level: 2, nav: true },
  { key: 'cmdb-domain-check', path: '/detection/cmdb-domain', module: '一次性检验', label: 'CMDB 域名校验', level: 2, nav: true },
  { key: 'detection-records', path: '/detection/records', module: '一次性检验', label: '检测记录', level: 2, nav: true },

  { key: 'workorder-new', path: '/workorders/new', module: '工单管理', label: '申请工单', level: 2, nav: true },
  { key: 'workorders', path: '/workorders/my', module: '工单管理', label: '我的申请', level: 2, nav: true },
  { key: 'approvals', path: '/workorders/approvals', module: '工单管理', label: '我的审批', level: 2, nav: true },
  { key: 'workorder-execution', path: '/workorders/execution', module: '工单管理', label: '执行记录', level: 3, nav: false, parent: 'workorders' },
  { key: 'workorder-detail', path: '/workorders/:id', module: '工单管理', label: '工单详情', level: 3, parent: 'workorders' },

  { key: 'settings-platform', path: '/settings/platform', module: '系统设置', label: '平台参数', level: 2, nav: true },
  { key: 'settings-permissions', path: '/settings/users-roles', module: '系统设置', label: '用户与角色', level: 2, nav: true },
  { key: 'settings-permission-matrix', path: '/settings/permission-matrix', module: '系统设置', label: '权限矩阵', level: 2, nav: true },
  { key: 'settings-credentials', path: '/settings/credentials', module: '系统设置', label: '凭据管理', level: 2, nav: true },
  { key: 'settings-integrations', path: '/settings/data-sources', module: '系统设置', label: '数据源管理', level: 2, nav: true },
  { key: 'settings-notification-channels', path: '/settings/notification-channels', module: '系统设置', label: '通知通道', level: 2, nav: true },
  { key: 'settings-notification-templates', path: '/settings/notification-templates', module: '系统设置', label: '通知模板', level: 2, nav: true },
  { key: 'settings-webhooks', path: '/settings/webhooks', module: '系统设置', label: '出站 Webhook', level: 2, nav: true },
  { key: 'settings-audit-logs', path: '/settings/audit-logs', module: '系统设置', label: '审计日志', level: 2, nav: true },
  { key: 'settings-retention', path: '/settings/retention', module: '系统设置', label: '数据保留策略', level: 2, nav: true },

  { key: 'ip-regex', path: '/tools/ip-regex', module: '工具', label: 'IP 正则助手', level: 2, nav: true }
] as const;

export type PageKey = (typeof routeRegistry)[number]['key'];
export type PrimaryModule = '监控与告警' | '资产中心' | '一次性检验' | '工单管理' | '系统设置' | '工具';

export const primaryModuleOrder: PrimaryModule[] = ['监控与告警', '资产中心', '一次性检验', '工单管理', '系统设置', '工具'];

export const navigationGroups = primaryModuleOrder.map((title) => ({
  title,
  items: routeRegistry
    .filter((route) => route.module === title && 'nav' in route && route.nav)
    .map((route) => ({ key: route.key, label: route.label }))
}));

export function isPageKey(value: string): value is PageKey {
  return routeRegistry.some((route) => route.key === value);
}

export function getRouteByKey(key: PageKey) {
  return routeRegistry.find((route) => route.key === key);
}

export function getNavParentKey(key: PageKey): PageKey {
  const route = getRouteByKey(key);
  return ((route && 'parent' in route ? route.parent : undefined) || key) as PageKey;
}
