export type DataSourceType = 'blueking_cmdb' | 'zabbix' | 'ldap' | 'webhook' | 'excel' | 'api';
export type CredentialType = 'token' | 'account' | 'password' | 'app_secret' | 'webhook_secret';
export type NotificationChannelType = 'site' | 'webhook' | 'wechat_work' | 'email';
export type SettingsEventType =
  | 'asset.sync.started'
  | 'asset.sync.completed'
  | 'asset.sync.failed'
  | 'monitoring.strategy.enabled'
  | 'probe.result.received'
  | 'alert.event.created'
  | 'workorder.completed';

export type DataSourceDefinition = {
  type: DataSourceType;
  name: string;
  allowedCredentialTypes: CredentialType[];
  usage: string;
};

export const dataSourceDefinitions: DataSourceDefinition[] = [
  { type: 'blueking_cmdb', name: '蓝鲸 CMDB', allowedCredentialTypes: ['token', 'app_secret'], usage: '资产模型同步' },
  { type: 'zabbix', name: 'Zabbix', allowedCredentialTypes: ['account', 'token'], usage: '用户模型同步和监控上下文' },
  { type: 'ldap', name: 'LDAP', allowedCredentialTypes: ['account', 'password'], usage: '用户同步' },
  { type: 'webhook', name: 'Webhook', allowedCredentialTypes: ['webhook_secret'], usage: '事件投递' },
  { type: 'excel', name: 'Excel 导入', allowedCredentialTypes: [], usage: '人工导入' },
  { type: 'api', name: '通用 API', allowedCredentialTypes: ['token', 'app_secret'], usage: '外部系统同步' }
];

export type CredentialRecord = {
  id: string;
  name: string;
  type: CredentialType;
  owner: string;
  secret?: string;
  masked_secret?: string;
};

export function canReferenceCredential(dataSourceType: DataSourceType, credentialType: CredentialType) {
  const definition = dataSourceDefinitions.find((item) => item.type === dataSourceType);
  return Boolean(definition?.allowedCredentialTypes.includes(credentialType));
}

export function maskCredential(record: CredentialRecord) {
  const masked = record.masked_secret || '******';
  const { secret: _secret, ...safe } = record;
  return { ...safe, masked_secret: masked };
}

export type NotificationChannel = {
  type: NotificationChannelType;
  name: string;
  target: 'person' | 'system';
  supportedEvents: SettingsEventType[];
};

const allSettingsEvents: SettingsEventType[] = [
  'asset.sync.started',
  'asset.sync.completed',
  'asset.sync.failed',
  'monitoring.strategy.enabled',
  'probe.result.received',
  'alert.event.created',
  'workorder.completed'
];

export const notificationChannels: NotificationChannel[] = [
  { type: 'site', name: '站内信', target: 'person', supportedEvents: allSettingsEvents },
  { type: 'wechat_work', name: '企业微信', target: 'person', supportedEvents: ['asset.sync.failed', 'alert.event.created', 'workorder.completed'] },
  { type: 'email', name: '邮件', target: 'person', supportedEvents: ['asset.sync.completed', 'asset.sync.failed', 'alert.event.created'] },
  { type: 'webhook', name: '出站 Webhook', target: 'system', supportedEvents: ['monitoring.strategy.enabled', 'probe.result.received', 'alert.event.created', 'workorder.completed'] }
];

export function supportsNotificationEvent(channelType: NotificationChannelType, eventType: SettingsEventType) {
  return Boolean(notificationChannels.find((channel) => channel.type === channelType)?.supportedEvents.includes(eventType));
}

export type NotificationTemplate = {
  key: string;
  eventType: SettingsEventType;
  title: string;
  variables: string[];
};

export const notificationTemplates: NotificationTemplate[] = [
  { key: 'asset-sync-failed', eventType: 'asset.sync.failed', title: '资产同步失败', variables: ['source_name', 'failed_count', 'trace_id'] },
  { key: 'alert-created', eventType: 'alert.event.created', title: '告警事件创建', variables: ['severity', 'asset_name', 'strategy_name'] },
  { key: 'workorder-completed', eventType: 'workorder.completed', title: '工单已完成', variables: ['workorder_id', 'result', 'operator'] }
];

export function validateTemplateVariables(template: NotificationTemplate, payload: Record<string, unknown>) {
  const missing = template.variables.filter((variable) => !(variable in payload));
  return { valid: missing.length === 0, missing };
}
