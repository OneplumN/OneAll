import '@ant-design/v5-patch-for-react-19';
import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  App as AntApp,
  Avatar,
  Badge,
  Button,
  ConfigProvider,
  Descriptions,
  Drawer,
  Empty,
  Input,
  InputNumber,
  Layout,
  Modal,
  Pagination,
  Popconfirm,
  Progress,
  Select,
  Space,
  Statistic,
  Steps,
  Switch,
  Table,
  Tabs,
  Tag,
  Timeline,
  Tooltip,
  Typography,
  Upload
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import zhCN from 'antd/locale/zh_CN';
import {
  AlertOutlined,
  AuditOutlined,
  BellOutlined,
  BoxPlotOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloudSyncOutlined,
  ControlOutlined,
  CopyOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  DeploymentUnitOutlined,
  DownloadOutlined,
  DownOutlined,
  FieldTimeOutlined,
  FileDoneOutlined,
  FilterOutlined,
  LeftOutlined,
  LockOutlined,
  MailOutlined,
  MessageOutlined,
  NodeIndexOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  RightOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  UploadOutlined,
  UserOutlined
} from '@ant-design/icons';
import 'antd/dist/reset.css';
import './styles.css';
import { acknowledgeAlertEvent, apiRoles, approveWorkorder, claimProbeTasks, closeAlertEvent, completeWorkorder, createAssetModel, createAssetRecord, createDetectionTask, createMonitoringStrategy, createWorkorderRequest, deleteAssetModel, deleteAssetRecord, deleteMonitoringStrategy, deleteWorkorderRequest, executeWorkorder, getCurrentApiRole, getPermissionCatalog, getProbeRuntime, listAlertEvents, listAssetModels, listAssetRecords, listAssetSyncRuns, listAssetSyncScripts, listAuditLogs, listDeletedAssetModelKeys, listDetectionTasks, listMonitoringStrategies, listNotifications, listProbeConfigVersions, listProbeHealth, listProbeMetricsHistory, listProbeNodes, listWorkorderRequests, previewAssetSync, recordAssetSyncFailure, refreshProbeConfig, registerProbeNode, rejectWorkorder, retireProbeNode, rollbackProbeConfig, runAssetSync, saveAssetSyncScript, submitProbeTaskResult, toggleMonitoringStrategy, updateAssetModel, updateAssetRecord, updateWorkorderRequest, validateCmdbDomain, withdrawWorkorder, type ApiAlertEvent, type ApiAssetModel, type ApiAssetSyncPreview, type ApiAssetSyncRun, type ApiAssetSyncScript, type ApiDetectionTask, type ApiMonitoringStrategy, type ApiPermissionCatalog, type ApiProbeConfigVersion, type ApiProbeMetricsHistoryPoint, type ApiProbeNode, type ApiProbeRuntimePayload, type ApiRole, type WorkorderApprovalRecord, type WorkorderRequestData } from './apiClient';
import { compileIpRegexFromText, expandIpRegex, parseIpLines, testIpAgainstRegex } from './ipRegexTool';
import { buildDetectionRequest, normalizeProbeCapabilities, presentDetectionStatus, validateDetectionInput, validateProbeRegistration } from './detectionContracts';
import {
  hasPermission,
  permissionMatrix as localPermissionMatrix,
  previewAlertRule,
  validateAlertRuleDsl,
  canTransitionWorkorder,
  type AlertRuleDsl,
  type PermissionModule,
  type Role,
  type WorkorderStatus
} from './domainContracts';
import { getNavParentKey, getRouteByKey, isPageKey, navigationGroups, type PageKey } from './navigationContract';
import {
  canReferenceCredential,
  dataSourceDefinitions,
  maskCredential,
  notificationChannels,
  notificationTemplates,
  supportsNotificationEvent
} from './settingsContracts';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

function LabeledInput(props: { label: string } & React.ComponentProps<typeof Input>) {
  const { label, ...inputProps } = props;
  return (
    <Space.Compact className="compact-input">
      <span className="compact-input-label">{label}</span>
      <Input {...inputProps} />
    </Space.Compact>
  );
}

type AlertRow = {
  key: string;
  severity: string;
  title: string;
  asset: string;
  duration: string;
  owner: string;
  notify: string;
  workorder: string;
  status: string;
};

type AssetRow = {
  key: string;
  name: string;
  type: string;
  ip: string;
  owner: string;
  dept: string;
  env: string;
  status: string;
  source: string;
  sync: string;
};

type WorkorderRow = {
  key: string;
  id: string;
  type: string;
  title: string;
  applicant: string;
  assignee: string;
  status: WorkorderStatus;
  sla: string;
  related_object?: string;
  relatedAlertId?: string;
  request_data?: WorkorderRequestData;
  strategy_id?: string;
  approval_records?: WorkorderApprovalRecord[];
};

type AssetModelRow = {
  key: string;
  id: string;
  name: string;
  code: string;
  fields: Array<{ key: string; type: string; label?: string; required?: boolean; editable?: boolean; unique?: boolean; disabled?: boolean }>;
  primary_key?: string;
  status: string;
  created_by: string;
  created_at: string;
};

type BusinessAssetModel = {
  id: string;
  name: string;
  code: string;
  category: string;
  source: string;
  fields: Array<{ key: string; type: string; label: string; required?: boolean; editable?: boolean; unique?: boolean; disabled?: boolean }>;
  rows: Array<Record<string, unknown> & { key: string }>;
};

type AssetFieldDraft = { key: string; label: string; type: string; required?: boolean; editable?: boolean; unique?: boolean; disabled?: boolean };
type AssetModelEditorState = {
  mode: 'create' | 'edit';
  id?: string;
  name: string;
  code: string;
  category: string;
  source: string;
  primaryKey: string;
  fields: AssetFieldDraft[];
};

type AuditLogRow = {
  key: string;
  id: string;
  actor: string;
  action: string;
  object: string;
  result: string;
  created_at: string;
};

const alerts: AlertRow[] = [
  { key: 'a1', severity: 'P0', title: 'api.oneall.internal HTTP 检测连续超时', asset: 'api.oneall.internal', duration: '18m', owner: '张三', notify: '已投递', workorder: 'WO-014', status: '处理中' },
  { key: 'a2', severity: 'P1', title: 'www.oneall.internal 证书 7 天后过期', asset: 'www.oneall.internal', duration: '2h', owner: '李四', notify: '待重试', workorder: '-', status: '待认领' },
  { key: 'a3', severity: 'P2', title: 'probe-gz-01 心跳延迟升高', asset: 'probe-gz-01', duration: '41m', owner: '平台组', notify: '已投递', workorder: '-', status: '观察中' },
  { key: 'a4', severity: 'P1', title: 'pay.oneall.internal DNS 解析异常', asset: 'pay.oneall.internal', duration: '9m', owner: '王五', notify: '已投递', workorder: 'WO-015', status: '处理中' }
];

const assets: AssetRow[] = [
  { key: '1', name: 'api.oneall.internal', type: '域名', ip: '10.0.1.100', owner: '张三', dept: '支付业务', env: 'prod', status: '运行', source: '蓝鲸 CMDB', sync: '09:00' },
  { key: '2', name: 'www.oneall.internal', type: '域名', ip: '10.0.1.101', owner: '李四', dept: '增长业务', env: 'prod', status: '运行', source: '蓝鲸 CMDB', sync: '09:00' },
  { key: '3', name: 'pay-oneall-app', type: '应用', ip: '10.0.2.50', owner: '王五', dept: '支付业务', env: 'prod', status: '维护', source: 'Zabbix', sync: '08:45' },
  { key: '4', name: 'legacy.oneall.internal', type: '域名', ip: '10.0.9.8', owner: '赵六', dept: '平台组', env: 'staging', status: '下线', source: '蓝鲸 CMDB', sync: '昨天' }
];

const workorders: WorkorderRow[] = [
  { key: 'w1', id: 'WO-20260526-014', type: '拨测监控申请', title: '新增 api.oneall.internal HTTP 监控', applicant: '张三', assignee: '李四', status: 'submitted' as WorkorderStatus, sla: '3h 20m' },
  { key: 'w2', id: 'WO-20260526-015', type: '拨测监控申请', title: 'HTTP 拨测 pay.oneall.internal', applicant: '王五', assignee: '赵六', status: 'approved' as WorkorderStatus, sla: '42m' },
  { key: 'w3', id: 'WO-20260525-088', type: '拨测监控申请', title: '证书拨测 www.oneall.internal', applicant: '李四', assignee: '赵六', status: 'completed' as WorkorderStatus, sla: '-' }
];

const workorderStatusLabel: Record<WorkorderStatus, string> = {
  draft: '草稿',
  submitted: '待审批',
  rejected: '已驳回',
  approved: '待执行',
  executing: '执行中',
  completed: '已完成',
  failed: '执行失败',
  canceled: '已取消',
  withdrawn: '已撤回'
};

const monitoringRequestDefaults = {
  target: 'https://api.oneall.internal/health',
  systemName: '支付业务',
  networkType: '互联网',
  owner: '张三',
  alertContacts: '00001',
  protocol: 'HTTP',
  frequency: '1 分钟',
  probes: '上海探针',
  alertThreshold: '连续 3 次失败'
};

function buildMonitoringRequest(row: WorkorderRow) {
  if (row.request_data) {
    const data = row.request_data;
    const triggerText = data.triggerMode === 'window'
      ? `最近 ${data.windowCount ?? data.failureCount} 次失败 ${data.failureCount} 次`
      : `连续 ${data.failureCount} 次失败`;
    return {
      target: data.target,
      systemName: data.systemName,
      networkType: data.networkType,
      owner: data.owner,
      alertContacts: data.alertContacts,
      protocol: data.protocol,
      frequency: `${data.frequencyValue} ${data.frequencyUnit}`,
      probes: data.probes.join('、'),
      expectedStatusCodes: data.expectedStatusCodes,
      timeoutSeconds: `${data.timeoutSeconds} 秒`,
      alertThreshold: `${data.alertSeverity} / ${triggerText} / 超时 ${data.timeoutSeconds} 秒 / 恢复 ${data.recoverySuccessCount} 次成功`
    };
  }
  const target = row.related_object || (row.title.match(/(https?:\/\/\S+|[a-z0-9.-]+\.[a-z]{2,})/i)?.[0] ?? monitoringRequestDefaults.target);
  const protocol = row.title.includes('SSL') || row.title.includes('证书') ? 'CERTIFICATE' : 'HTTP';
  return {
    target,
    systemName: row.title.includes('pay') ? '支付业务' : monitoringRequestDefaults.systemName,
    networkType: '互联网',
    owner: row.applicant === '系统' ? row.assignee : row.applicant,
    alertContacts: row.id.endsWith('2') ? '00002' : monitoringRequestDefaults.alertContacts,
    protocol,
    frequency: protocol === 'CERTIFICATE' ? '1 天' : monitoringRequestDefaults.frequency,
    probes: '上海探针',
    expectedStatusCodes: '200,204',
    timeoutSeconds: '5 秒',
    alertThreshold: row.title.includes('DNS') ? '严重 / 连续 2 次失败 / 超时 5 秒 / 恢复 2 次成功' : '严重 / 连续 3 次失败 / 超时 5 秒 / 恢复 2 次成功'
  };
}

function getWorkorderStepCurrent(status: WorkorderStatus) {
  if (status === 'draft') return 0;
  if (['submitted', 'rejected', 'withdrawn'].includes(status)) return 1;
  if (['approved', 'executing', 'failed'].includes(status)) return 2;
  return 3;
}

function getWorkorderStepStatus(status: WorkorderStatus): 'wait' | 'process' | 'finish' | 'error' {
  if (['rejected', 'failed', 'canceled', 'withdrawn'].includes(status)) return 'error';
  if (status === 'completed') return 'finish';
  return 'process';
}

const businessAssetModels: BusinessAssetModel[] = [
  {
    id: 'cmdb-domain',
    name: 'CMDB 域名',
    code: 'cmdb-domain',
    category: '服务资源',
    source: 'CMDB',
    fields: [
      { key: 'domain', label: '域名', type: 'string' },
      { key: 'system_name', label: '所属系统', type: 'string' },
      { key: 'network_type', label: '互联网类型', type: 'enum' },
      { key: 'owner', label: '负责人', type: 'string' },
      { key: 'alert_contacts', label: '告警联系人（工号）', type: 'string' }
    ],
    rows: []
  },
  {
    id: 'zabbix-host',
    name: 'Zabbix 主机',
    code: 'zabbix-host',
    category: '基础资源',
    source: 'Zabbix',
    fields: [
      { key: 'ip', label: 'IP 地址', type: 'string' },
      { key: 'host_name', label: '主机名称', type: 'string' },
      { key: 'visible_name', label: '可见名称', type: 'string' },
      { key: 'host_group', label: '主机群组', type: 'string' },
      { key: 'proxy', label: 'Proxy', type: 'string' },
      { key: 'interface_type', label: '接口类型', type: 'string' },
      { key: 'interface_available', label: '接口可用性', type: 'status' }
    ],
    rows: []
  },
  {
    id: 'ipmp-project',
    name: 'IPMP 项目',
    code: 'ipmp-project',
    category: '业务对象',
    source: 'IPMP',
    fields: [
      { key: 'app_code', label: '应用编号', type: 'string' },
      { key: 'app_name_cn', label: '应用中文名称', type: 'string' },
      { key: 'app_name_en', label: '应用英文简称', type: 'string' },
      { key: 'app_status', label: '应用状态', type: 'status' },
      { key: 'owner', label: '系统负责人', type: 'string' },
      { key: 'security_level', label: '等保级别', type: 'string' },
      { key: 'system_origin', label: '系统归属', type: 'string' }
    ],
    rows: []
  },
  {
    id: 'workorder-host',
    name: '工单纳管主机信息',
    code: 'workorder-host',
    category: '基础资源',
    source: 'Manual',
    fields: [
      { key: 'ip', label: 'IP 地址', type: 'string' },
      { key: 'online_status', label: '在线状态', type: 'status' },
      { key: 'idc', label: '所在机房', type: 'string' },
      { key: 'proxy', label: '接入 ITSI Proxy', type: 'string' },
      { key: 'port', label: '端口', type: 'number' },
      { key: 'alert_contacts', label: '告警联系人', type: 'string' },
      { key: 'hostname', label: 'Hostname', type: 'string' },
      { key: 'app_system', label: '应用系统', type: 'string' },
      { key: 'owner', label: '系统负责人', type: 'string' }
    ],
    rows: []
  }
];

const httpAvailabilityRule: AlertRuleDsl = {
  scope: {
    asset_model: 'pay_domain_service',
    asset_filter: { environment: 'prod' }
  },
  signal: {
    metric: 'http_status',
    source: 'probe_result'
  },
  condition: {
    operator: 'not_in',
    value: [200, 301, 302],
    duration: '3m',
    consecutive: 3
  },
  severity: 'critical',
  recovery: {
    operator: 'in',
    value: [200, 301, 302],
    consecutive: 2
  },
  actions: {
    notify_channels: ['site', 'webhook'],
    create_workorder: false
  }
};

const moduleIcons = {
  '监控与告警': <AlertOutlined />,
  '资产中心': <BoxPlotOutlined />,
  '一次性检验': <PlayCircleOutlined />,
  '工单管理': <FileDoneOutlined />,
  '系统设置': <SettingOutlined />,
  '工具': <ControlOutlined />
};

const nextNavGroups = navigationGroups.map((group) => ({
  ...group,
  icon: moduleIcons[group.title]
}));

const permissionModuleLabels: Record<PermissionModule, string> = {
  monitoringOverview: '监控总览',
  alertEvents: '告警事件',
  monitoringPolicies: '监控策略',
  probeNodes: '探针节点',
  assetCenter: '资产中心',
  oneOffDetection: '一次性检验',
  workorders: '工单管理',
  usersAndRoles: '用户与角色',
  credentials: '凭据管理',
  dataSources: '数据源管理',
  notificationsWebhooks: '通知与 Webhook',
  auditLogs: '审计日志'
};

const roleDescriptions: Record<Role, string> = {
  PlatformAdmin: '系统设置、用户、凭据、审计',
  OpsAdmin: '资产、监控、探针、工单闭环',
  OpsEngineer: '日常检测、处置、资产维护',
  Approver: '审批工单和查看关联对象',
  Viewer: '只读查看授权数据范围'
};

function buildPermissionRows(matrix: ApiPermissionCatalog['permissionMatrix'] | typeof localPermissionMatrix) {
  return (Object.keys(permissionModuleLabels) as PermissionModule[]).map((module) => {
    const row: { key: string; module: string } & Partial<Record<Role, string>> = {
      key: module,
      module: permissionModuleLabels[module]
    };
    apiRoles.forEach((role) => {
      row[role] = matrix[module]?.[role]?.length ? matrix[module][role].join(' / ') : 'none';
    });
    return row;
  });
}

function getPageFromHash(): PageKey {
  const key = window.location.hash.replace('#', '');
  if (key.startsWith('alerts/')) return 'alert-detail';
  if (key.startsWith('policies/')) return 'policy-detail';
  if (key.startsWith('probes/')) return 'probe-detail';
  if (key.startsWith('execution-logs/')) return 'execution-log-detail';
  if (key.startsWith('workorders/')) return 'workorder-detail';
  return isPageKey(key) ? key : 'alerts';
}

function getHashEntityId(prefix: string) {
  const key = window.location.hash.replace('#', '');
  return key.startsWith(`${prefix}/`) ? decodeURIComponent(key.slice(prefix.length + 1)) : '';
}

function rememberDetailReturn(type: 'alert' | 'policy' | 'probe' | 'execution-log' | 'workorder', target: PageKey) {
  window.sessionStorage.setItem(`oneall.detailReturn.${type}`, target);
}

function goDetailBack(type: 'alert' | 'policy' | 'probe' | 'execution-log' | 'workorder', fallback: PageKey) {
  const target = window.sessionStorage.getItem(`oneall.detailReturn.${type}`) || fallback;
  window.location.hash = target;
}

function statusTag(value: string) {
  const color =
    ['运行', '在线', '已完成', '已投递', '已映射', '已同步', '已连接', '已确认', 'prod'].includes(value) ? 'green' :
    ['P0', '致命', '失败', '执行失败', '已驳回', '下线', '离线', '已退役', '已回滚', '待重试', '缺失', '未连接'].includes(value) ? 'red' :
    ['P1', '严重', '维护', '异常', '待审批', '待执行', '执行中', '处理中', '观察中', '待同步', '待确认', 'staging'].includes(value) ? 'orange' :
    ['P2', '预警', '待认领', '草稿', '已注册'].includes(value) ? 'blue' :
    'default';
  return <Tag color={color}>{value}</Tag>;
}

function probeStatusLabel(status?: string) {
  if (status === 'online') return '在线';
  if (status === 'degraded') return '异常';
  if (status === 'offline') return '离线';
  if (status === 'registered') return '已注册';
  if (status === 'retired') return '已退役';
  return status || '未知';
}

function probeConnectionLabel(status?: string) {
  if (status === 'connected') return '已连接';
  if (status === 'disconnected') return '未连接';
  return status || '-';
}

function probeConfigLabel(status?: string) {
  if (status === 'acknowledged') return '已同步';
  if (status === 'pending') return '待同步';
  return status || '-';
}

function probeConfigVersionLabel(status?: string) {
  if (status === 'acknowledged') return '已确认';
  if (status === 'published') return '待确认';
  if (status === 'rolled_back') return '已回滚';
  return status || '-';
}

function probeVersionNumberForView(version?: string) {
  const value = Number(String(version || 'v0').replace(/^v/, ''));
  return Number.isFinite(value) ? value : 0;
}

function formatProbeMetric(value?: number | null, unit = '') {
  if (value == null || Number.isNaN(Number(value))) return '-';
  return `${Number(value).toFixed(unit === '%' ? 0 : 1).replace(/\.0$/, '')}${unit}`;
}

function formatProbeMemory(value?: number | null) {
  if (value == null || Number.isNaN(Number(value))) return '-';
  const numeric = Number(value);
  return numeric >= 1024 ? `${(numeric / 1024).toFixed(1)}GB` : `${numeric.toFixed(0)}MB`;
}

function getAlertEventName(alert: Pick<ApiAlertEvent, 'title' | 'asset'>) {
  return alert.title.replace(alert.asset, '').trim() || alert.title;
}

function getStableAlertUuid(id: string) {
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id)) return id;
  const seeds = [0x811c9dc5, 0x01000193, 0x9e3779b9, 0x85ebca6b];
  const hex = seeds.map((seed) => {
    let hash = seed;
    for (let index = 0; index < id.length; index += 1) {
      hash ^= id.charCodeAt(index) + index;
      hash = Math.imul(hash, 0x01000193);
    }
    return (hash >>> 0).toString(16).padStart(8, '0');
  }).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-4${hex.slice(13, 16)}-${(8 + (parseInt(hex.slice(16, 17), 16) % 4)).toString(16)}${hex.slice(17, 20)}-${hex.slice(20, 32)}`;
}

function getAlertRecipients(alert: Pick<ApiAlertEvent, 'owner'>) {
  return `${alert.owner}、值班组`;
}

function getAlertNotifyChannels(alert: Pick<ApiAlertEvent, 'notify'>) {
  if (alert.notify === '待重试') {
    return [
      { key: 'wecom', label: '企微', ok: true, icon: <MessageOutlined /> },
      { key: 'mail', label: '邮箱', ok: false, icon: <MailOutlined /> }
    ];
  }
  return [
    { key: 'wecom', label: '企微', ok: true, icon: <MessageOutlined /> },
    { key: 'mail', label: '邮箱', ok: alert.notify === '已投递', icon: <MailOutlined /> }
  ];
}

function NotifyChannelStatus(props: { alert: Pick<ApiAlertEvent, 'notify'> }) {
  return (
    <Space size={8} className="notify-channel-list">
      {getAlertNotifyChannels(props.alert).map((channel) => (
        <Tooltip key={channel.key} title={`${channel.label}${channel.ok ? '通知成功' : '通知失败'}`}>
          <span className={`notify-channel ${channel.ok ? 'is-success' : 'is-failed'}`}>
            {channel.icon}
            <span>{channel.label}</span>
            {channel.ok ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
          </span>
        </Tooltip>
      ))}
    </Space>
  );
}

function PageHeader(props: { module: string; title: string; desc: string; action?: React.ReactNode }) {
  if (!props.action) return null;
  return <div className="page-action-bar">{props.action}</div>;
}

function tablePagination(pageSize = 8) {
  return {
    pageSize,
    hideOnSinglePage: false,
    showSizeChanger: true,
    showTotal: (total: number) => `共 ${total} 条`
  };
}

function useTableContainerWidth(selector: string, minWidth: number) {
  const [width, setWidth] = useState(minWidth);
  useEffect(() => {
    const update = () => {
      const element = document.querySelector(selector);
      setWidth(Math.max(minWidth, Math.floor(element?.clientWidth ?? minWidth)));
    };
    update();
    const element = document.querySelector(selector);
    const observer = typeof ResizeObserver !== 'undefined' && element ? new ResizeObserver(update) : null;
    observer?.observe(element as Element);
    window.addEventListener('resize', update);
    return () => {
      observer?.disconnect();
      window.removeEventListener('resize', update);
    };
  }, [minWidth, selector]);
  return width;
}

function distributeTableWidths(containerWidth: number, columns: Array<{ min: number; weight?: number }>) {
  const baseWidth = columns.reduce((total, column) => total + column.min, 0);
  const extraWidth = Math.max(0, containerWidth - baseWidth);
  const totalWeight = columns.reduce((total, column) => total + (column.weight ?? 0), 0);
  const widths = columns.map((column) => column.min + Math.floor(totalWeight ? (extraWidth * (column.weight ?? 0)) / totalWeight : 0));
  const usedWidth = widths.reduce((total, width) => total + width, 0);
  if (widths.length && usedWidth < containerWidth) widths[0] += containerWidth - usedWidth;
  return widths;
}

function FilterBar(props: { children?: React.ReactNode; primary?: React.ReactNode }) {
  return (
    <div className="filter-card">
      <Input prefix={<SearchOutlined />} placeholder="搜索名称、负责人、ID、关键字" />
      <Select value="prod" options={[{ label: '生产环境', value: 'prod' }, { label: '预发环境', value: 'staging' }, { label: '测试环境', value: 'test' }]} />
      <Select value="all" options={[{ label: '全部业务线', value: 'all' }, { label: '支付业务', value: 'pay' }, { label: '平台组', value: 'platform' }]} />
      {props.children}
      <Button icon={<FilterOutlined />}>高级筛选</Button>
      {props.primary}
    </div>
  );
}

function SectionBlock(props: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={['section-block', props.className].filter(Boolean).join(' ')}>
      <div className="section-block-title">{props.title}</div>
      <div className="section-block-body">{props.children}</div>
    </section>
  );
}

function Kpi(props: { title: string; value: string | number; hint: string; tone: string; icon: React.ReactNode }) {
  return (
    <div className={`kpi kpi-${props.tone}`}>
      <div className="kpi-head"><span className="kpi-icon">{props.icon}</span><Text type="secondary">{props.title}</Text></div>
      <Statistic value={props.value} />
      <Text type="secondary">{props.hint}</Text>
    </div>
  );
}

function CompactSummary(props: { items: Array<{ label: string; value: string | number; tone?: string }> }) {
  return (
    <div className="compact-summary">
      {props.items.map((item) => (
        <span key={item.label} className={item.tone ? `summary-item summary-${item.tone}` : 'summary-item'}>
          {item.label}<b>{item.value}</b>
        </span>
      ))}
    </div>
  );
}

function AlertsPage(_props: { onOpenDetail: () => void }) {
  type AlertEventRow = ApiAlertEvent & { key: string };
  const [rows, setRows] = useState<AlertEventRow[]>([]);
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState('active');
  const [closeTarget, setCloseTarget] = useState<AlertEventRow | null>(null);
  const [closeReason, setCloseReason] = useState('人工确认恢复');
  const tableWidth = useTableContainerWidth('.alert-list-body', 1280);
  const alertColumnWidths = distributeTableWidths(tableWidth, [
    { min: 76 },
    { min: 240, weight: 2.2 },
    { min: 180, weight: 1.2 },
    { min: 138, weight: 1 },
    { min: 110 },
    { min: 90 },
    { min: 90 },
    { min: 130 },
    { min: 92 },
    { min: 180 }
  ]);
  const alertTableWidth = alertColumnWidths.reduce((total, width) => total + width, 0);
  const reloadAlerts = () => {
    listAlertEvents()
      .then((data) => setRows(data.items.map((item) => ({ ...item, key: item.id }))))
      .catch(() => setRows(alerts.map((item) => ({ ...item, id: item.key, key: item.key }))));
  };
  useEffect(() => {
    reloadAlerts();
  }, []);
  const activeRows = rows.filter((row) => row.status !== '已恢复');
  const filteredRows = rows.filter((row) => {
    const text = [row.id, row.title, row.asset, row.owner, row.status, row.severity, row.strategy, row.workorder].join(' ').toLowerCase();
    const matchedKeyword = !keyword.trim() || text.includes(keyword.trim().toLowerCase());
    const matchedStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && row.status !== '已恢复') ||
      (statusFilter === 'unclaimed' && row.status === '待认领') ||
      (statusFilter === 'processing' && row.status === '处理中') ||
      (statusFilter === 'recovered' && row.status === '已恢复');
    return matchedKeyword && matchedStatus;
  });
  const acknowledge = (row: AlertEventRow) => acknowledgeAlertEvent(row.id).then(reloadAlerts);
  const confirmClose = () => {
    if (!closeTarget) return;
    closeAlertEvent(closeTarget.id, closeReason.trim() || '人工确认恢复').then(() => {
      setCloseTarget(null);
      setCloseReason('人工确认恢复');
      reloadAlerts();
    });
  };
  const columns: ColumnsType<AlertEventRow> = [
    { title: '级别', dataIndex: 'severity', width: alertColumnWidths[0], render: statusTag },
    { title: '告警标题', dataIndex: 'title', width: alertColumnWidths[1], ellipsis: true },
    { title: '影响资产', dataIndex: 'asset', width: alertColumnWidths[2], ellipsis: true },
    { title: '策略', dataIndex: 'strategy', width: alertColumnWidths[3], ellipsis: true, render: (value) => value ?? '-' },
    { title: '探针', dataIndex: 'probe', width: alertColumnWidths[4], render: (value) => value ?? '-' },
    { title: '持续', dataIndex: 'duration', width: alertColumnWidths[5] },
    { title: '负责人', dataIndex: 'owner', width: alertColumnWidths[6] },
    { title: '工单', dataIndex: 'workorder', width: alertColumnWidths[7], render: (value) => value && value !== '-' ? <Button type="link">{value}</Button> : <Text type="secondary">未创建</Text> },
    { title: '状态', dataIndex: 'status', width: alertColumnWidths[8], render: statusTag },
    {
      title: '操作',
      width: alertColumnWidths[9],
      fixed: 'right',
      render: (_, row) => (
        <Space>
          <Button type="link" onClick={() => {
            rememberDetailReturn('alert', 'alerts');
            window.location.hash = `alerts/${encodeURIComponent(row.id)}`;
          }}>详情</Button>
          {row.status === '待认领' && <Button type="link" onClick={() => acknowledge(row)}>认领</Button>}
          {row.status !== '已恢复' && <Button type="link" danger onClick={() => setCloseTarget(row)}>关闭</Button>}
        </Space>
      )
    }
  ];

  return (
    <section className="page alerts-page">
      <section className="alert-list-shell">
        <div className="alert-list-toolbar">
          <Space>
            <Input prefix={<SearchOutlined />} placeholder="搜索告警、资产、负责人、工单" value={keyword} onChange={(event) => setKeyword(event.target.value)} allowClear />
            <Select value={statusFilter} onChange={setStatusFilter} options={[
              { label: '未恢复', value: 'active' },
              { label: '待认领', value: 'unclaimed' },
              { label: '处理中', value: 'processing' },
              { label: '已恢复', value: 'recovered' },
              { label: '全部状态', value: 'all' }
            ]} />
          </Space>
          <Space>
            <Text type="secondary">未恢复 {activeRows.length} 条</Text>
            <Button icon={<ReloadOutlined />} onClick={reloadAlerts}>刷新</Button>
          </Space>
        </div>
        <div className="alert-list-body">
          <Table className="enterprise-fixed-table" size="middle" tableLayout="fixed" dataSource={filteredRows} columns={columns} pagination={tablePagination(20)} scroll={{ x: alertTableWidth }} />
        </div>
      </section>
      <Modal
        title="关闭告警"
        open={Boolean(closeTarget)}
        okText="确认关闭"
        okButtonProps={{ danger: true }}
        onOk={confirmClose}
        onCancel={() => setCloseTarget(null)}
      >
        <Space direction="vertical" className="full-width">
          <Text type="secondary">关闭会把事件状态置为已恢复，并写入处置记录。</Text>
          <Input.TextArea rows={4} value={closeReason} onChange={(event) => setCloseReason(event.target.value)} maxLength={120} showCount />
        </Space>
      </Modal>
    </section>
  );
}

function MonitoringOverviewPage(props: { onOpenAlert: () => void }) {
  return (
    <section className="page">
      <PageHeader
        module="监控与告警"
        title="监控总览"
        desc="作为登录默认页，呈现未恢复风险、探针健康、策略下发和待处理队列。"
      />
      <div className="metric-grid compact">
        <Kpi title="未恢复告警" value={27} hint="P0 3 条，P1 8 条" tone="red" icon={<ThunderboltOutlined />} />
        <Kpi title="策略健康" value="42/45" hint="3 条待下发" tone="green" icon={<SafetyCertificateOutlined />} />
        <Kpi title="探针在线率" value="94%" hint="18 / 19 节点在线" tone="blue" icon={<NodeIndexOutlined />} />
        <Kpi title="今日工单" value={16} hint="5 条待审批" tone="orange" icon={<FileDoneOutlined />} />
      </div>
      <div className="workbench-grid">
        <SectionBlock title="值班队列">
          <div className="queue-list">
            {['P0 未处理 3', '待认领 9', '通知失败 2', '探针异常 1'].map((item) => <button key={item}>{item}</button>)}
          </div>
        </SectionBlock>
        <SectionBlock title="最近高优先级告警" className="span-2">
          <Table
            pagination={false}
            size="middle"
            dataSource={alerts.slice(0, 3)}
            columns={[
              { title: '级别', dataIndex: 'severity', width: 80, render: statusTag },
              { title: '标题', dataIndex: 'title' },
              { title: '资产', dataIndex: 'asset', width: 170 },
              { title: '状态', dataIndex: 'status', width: 100, render: statusTag },
              { title: '操作', width: 90, render: () => <Button type="link" onClick={props.onOpenAlert}>详情</Button> }
            ]}
          />
        </SectionBlock>
      </div>
      <div className="workbench-grid">
        <SectionBlock title="策略下发状态" className="span-2">
          <Table
            pagination={false}
            dataSource={[
              { key: '1', name: 'HTTP 可用性', scope: '支付域名服务模型 / prod', version: 'v18', status: '已下发' },
              { key: '2', name: '证书有效期', scope: '支付域名服务模型 / prod', version: 'v11', status: '待下发' },
              { key: '3', name: 'DNS 解析', scope: '支付域名服务模型 / prod', version: 'v7', status: '已下发' }
            ]}
            columns={[
              { title: '策略', dataIndex: 'name' },
              { title: '范围', dataIndex: 'scope' },
              { title: '版本', dataIndex: 'version' },
              { title: '状态', dataIndex: 'status', render: statusTag }
            ]}
          />
        </SectionBlock>
        <SectionBlock title="探针健康">
          <Space direction="vertical" className="full-width">
            <div><Text>华东一区</Text><Progress percent={96} strokeColor="#15803d" /></div>
            <div><Text>华北一区</Text><Progress percent={92} strokeColor="#1d4ed8" /></div>
            <div><Text>华南一区</Text><Progress percent={78} strokeColor="#b45309" /></div>
          </Space>
        </SectionBlock>
      </div>
    </section>
  );
}

function PoliciesPage() {
  type StrategyRow = ApiMonitoringStrategy & { key: string };
  const [rows, setRows] = useState<StrategyRow[]>([]);
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const tableWidth = useTableContainerWidth('.policy-list-body', 1260);
  const policyColumnWidths = distributeTableWidths(tableWidth, [
    { min: 190, weight: 1.8 },
    { min: 260, weight: 2.2 },
    { min: 90 },
    { min: 100 },
    { min: 88 },
    { min: 76 },
    { min: 110 },
    { min: 160, weight: 1 },
    { min: 160 },
    { min: 210 }
  ]);
  const policyTableWidth = policyColumnWidths.reduce((total, width) => total + width, 0);
  const reloadStrategies = () => {
    listMonitoringStrategies()
      .then((data) => setRows((data.items ?? []).map((item) => ({ ...item, key: item.id }))))
      .catch(() => setRows([]));
  };
  useEffect(() => {
    reloadStrategies();
  }, []);
  const sourceLabel = (row: ApiMonitoringStrategy) => row.source_workorder_id ? `工单 ${row.source_workorder_id}` : '手动创建';
  const protocolLabel = (row: ApiMonitoringStrategy) => row.protocol ?? (row.rule?.signal?.metric === 'certificate_expire_days' ? 'CERTIFICATE' : 'HTTP');
  const filteredRows = rows.filter((row) => {
    const text = [row.id, row.name, row.scope, row.protocol, row.severity, row.source_workorder_id].join(' ').toLowerCase();
    const matchedKeyword = !keyword.trim() || text.includes(keyword.trim().toLowerCase());
    const matchedStatus = statusFilter === 'all' || (statusFilter === 'enabled' ? row.enabled : !row.enabled);
    return matchedKeyword && matchedStatus;
  });
  const copyStrategy = (row: StrategyRow) => {
    createMonitoringStrategy({
      name: `${row.name} 副本`,
      scope: row.scope,
      enabled: false,
      rule: row.rule
    }).then(reloadStrategies);
  };

  return (
    <section className="page policy-page">
      <section className="policy-list-shell">
        <div className="policy-list-toolbar">
          <Space>
            <Input prefix={<SearchOutlined />} placeholder="搜索策略、范围、来源工单" value={keyword} onChange={(event) => setKeyword(event.target.value)} allowClear />
            <Select value={statusFilter} onChange={setStatusFilter} options={[{ label: '全部状态', value: 'all' }, { label: '已启用', value: 'enabled' }, { label: '已停用', value: 'disabled' }]} />
          </Space>
          <Button type="primary" icon={<SafetyCertificateOutlined />} onClick={() => createMonitoringStrategy({ name: `HTTP 可用性 ${Date.now()}`, scope: '支付业务' }).then(reloadStrategies)}>新建策略</Button>
        </div>
        <div className="policy-list-body">
          <Table
            size="middle"
            dataSource={filteredRows}
            pagination={tablePagination(20)}
            columns={[
              { title: '策略名称', dataIndex: 'name', width: policyColumnWidths[0], ellipsis: true },
              { title: '作用对象', dataIndex: 'scope', width: policyColumnWidths[1], ellipsis: true },
              { title: '协议', dataIndex: 'protocol', width: policyColumnWidths[2], render: (_, row) => protocolLabel(row) },
              { title: '告警等级', dataIndex: 'severity', width: policyColumnWidths[3], render: (value) => statusTag(value ?? '严重') },
              {
                title: '启用',
                dataIndex: 'enabled',
                width: policyColumnWidths[4],
                render: (enabled: boolean, row) => (
                  <Switch
                    size="small"
                    checked={enabled}
                    checkedChildren="启用"
                    unCheckedChildren="停用"
                    onChange={(checked) => toggleMonitoringStrategy(row.id, checked).then(reloadStrategies)}
                  />
                )
              },
              { title: '版本', dataIndex: 'version', width: policyColumnWidths[5] },
              { title: '最近触发', dataIndex: 'recent_trigger', width: policyColumnWidths[6], render: (value) => value ?? '-' },
              { title: '来源', width: policyColumnWidths[7], ellipsis: true, render: (_, row) => sourceLabel(row) },
              { title: '更新时间', dataIndex: 'updated_at', width: policyColumnWidths[8], render: (value) => value ?? '-' },
              {
                title: '操作',
                width: policyColumnWidths[9],
                fixed: 'right',
                render: (_, row) => (
                  <Space>
                    <Button type="link" onClick={() => {
                      rememberDetailReturn('policy', 'policies');
                      window.location.hash = `policies/${encodeURIComponent(row.id)}`;
                    }}>详情</Button>
                    <Button type="link" onClick={() => {
                      rememberDetailReturn('policy', 'policies');
                      window.location.hash = `policies/${encodeURIComponent(row.id)}`;
                    }}>编辑</Button>
                    <Button type="link" onClick={() => copyStrategy(row)}>复制</Button>
                    <Popconfirm title="删除策略" description="删除后该策略不会继续下发。" okText="删除" cancelText="取消" onConfirm={() => deleteMonitoringStrategy(row.id).then(reloadStrategies)}>
                      <Button type="link" danger>删除</Button>
                    </Popconfirm>
                  </Space>
                )
              }
            ]}
            tableLayout="fixed"
            className="enterprise-fixed-table"
            scroll={{ x: policyTableWidth }}
          />
        </div>
      </section>
    </section>
  );
}

function ProbesPage() {
  type ProbeRow = ApiProbeNode & { key: string };
  const [rows, setRows] = useState<ProbeRow[]>([]);
  const [healthSummary, setHealthSummary] = useState({ online: 0, degraded: 0, offline: 0 });
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [registerOpen, setRegisterOpen] = useState(false);
  const [registeredProbe, setRegisteredProbe] = useState<ApiProbeNode | null>(null);
  const [probeMessage, setProbeMessage] = useState('');
  const [probeForm, setProbeForm] = useState({
    name: 'probe-new-01',
    region: '华东一区',
    networkType: '互联网',
    ipAddress: '10.40.1.8',
    capabilities: ['HTTP', 'CERTIFICATE']
  });
  const reload = () => {
    Promise.all([listProbeNodes(), listProbeHealth()])
      .then(([data, health]) => {
        setRows((data.items ?? []).map((item) => ({ ...item, key: item.id })));
        const healthItems = health.items ?? [];
        setHealthSummary({
          online: healthItems.filter((item) => item.status === 'online').length,
          degraded: healthItems.filter((item) => item.status === 'degraded').length,
          offline: healthItems.filter((item) => item.status === 'offline').length
        });
      })
      .catch(() => {
        setRows([]);
        setHealthSummary({ online: 0, degraded: 0, offline: 0 });
      });
  };
  useEffect(() => {
    reload();
  }, []);
  const probeTableWidth = useTableContainerWidth('.probe-list-body', 1040);
  const probeColumnWidths = distributeTableWidths(probeTableWidth, [
    { min: 170, weight: 1.4 },
    { min: 130, weight: 0.8 },
    { min: 130, weight: 0.8 },
    { min: 170, weight: 1.1 },
    { min: 120, weight: 0.7 },
    { min: 100, weight: 0.4 },
    { min: 100, weight: 0 },
    { min: 120, weight: 0 }
  ]);
  const filteredRows = rows.filter((row) => {
    const text = [row.id, row.name, row.region, row.network_type, row.ip_address, row.capabilities.join(' ')].join(' ').toLowerCase();
    const keywordHit = !keyword.trim() || text.includes(keyword.trim().toLowerCase());
    const statusHit = statusFilter === 'all' || row.status === statusFilter;
    return keywordHit && statusHit;
  });
  const openProbeDetail = (row: ProbeRow) => {
    rememberDetailReturn('probe', 'probes');
    window.location.hash = `probes/${encodeURIComponent(row.id)}`;
  };
  const openRegisterDrawer = () => {
    setProbeMessage('');
    setRegisteredProbe(null);
    setRegisterOpen(true);
  };
  const closeRegisterDrawer = () => {
    setRegisterOpen(false);
    setRegisteredProbe(null);
  };
  const retireProbe = (row: ProbeRow) => {
    retireProbeNode(row.id).then(reload);
  };
  const saveProbe = () => {
    const errors = validateProbeRegistration({
      name: probeForm.name,
      region: probeForm.region,
      networkType: probeForm.networkType,
      ipAddress: probeForm.ipAddress,
      capabilities: probeForm.capabilities
    });
    if (errors.length) {
      setProbeMessage(errors[0]);
      return;
    }
    registerProbeNode({
      name: probeForm.name.trim(),
      region: probeForm.region.trim(),
      network_type: probeForm.networkType,
      ip_address: probeForm.ipAddress.trim(),
      capabilities: normalizeProbeCapabilities(probeForm.capabilities)
    }).then((created) => {
      setRegisteredProbe(created);
      setProbeMessage('');
      reload();
    });
  };
  const registeredProbeBootstrap = registeredProbe ? [
    `ONEALL_PROBE_ID=${registeredProbe.id}`,
    `ONEALL_GATEWAY=${registeredProbe.gateway_url ?? '-'}`,
    `ONEALL_TOKEN=<PROBE_TOKEN>`,
    `ONEALL_CAPABILITIES=${registeredProbe.capabilities.join(',')}`,
    `ONEALL_HEARTBEAT=${registeredProbe.agent_config?.heartbeat_interval_seconds ?? 30}s`
  ].join('\n') : '';

  return (
    <section className="page">
      <section className="legacy-list-panel platform-table-panel probe-table-panel">
        <div className="legacy-list-toolbar">
          <div className="legacy-list-toolbar-left">
            <Input prefix={<SearchOutlined />} allowClear value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索名称 / IP / ID / 能力" />
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              options={[
                { label: '全部状态', value: 'all' },
                { label: '已注册', value: 'registered' },
                { label: '在线', value: 'online' },
                { label: '异常', value: 'degraded' },
                { label: '离线', value: 'offline' },
                { label: '已退役', value: 'retired' }
              ]}
            />
          </div>
          <div className="legacy-list-toolbar-right">
            <span className="probe-health-inline">在线 {healthSummary.online} / 异常 {healthSummary.degraded} / 离线 {healthSummary.offline}</span>
            <Button icon={<ReloadOutlined />} onClick={reload}>刷新</Button>
            <Button type="primary" icon={<NodeIndexOutlined />} onClick={openRegisterDrawer}>注册探针</Button>
          </div>
        </div>
        <div className="legacy-list-body platform-table-body probe-list-body">
          <Table
            className="enterprise-fixed-table"
            size="middle"
            tableLayout="fixed"
            dataSource={filteredRows}
            columns={[
              {
                title: '探针',
                width: probeColumnWidths[0],
                ellipsis: true,
                render: (_, row) => <Button type="link" onClick={() => openProbeDetail(row)}>{row.name}</Button>
              },
              { title: '区域 / 网络', width: probeColumnWidths[1], ellipsis: true, render: (_, row) => `${row.region} / ${row.network_type ?? '-'}` },
              { title: 'IP 地址', dataIndex: 'ip_address', width: probeColumnWidths[2], ellipsis: true, render: (value) => value || '未上报' },
              { title: '能力', width: probeColumnWidths[3], ellipsis: true, render: (_, row) => row.capabilities.join(' / ') },
              { title: '运行', width: probeColumnWidths[4], render: (_, row) => `${row.active_tasks ?? 0} 任务 / 队列 ${row.queue_depth ?? 0}` },
              { title: '成功率', dataIndex: 'success_rate', width: probeColumnWidths[5], render: (value) => value === null || value === undefined ? '-' : `${value}%` },
              { title: '状态', dataIndex: 'status', width: probeColumnWidths[6], render: (value) => statusTag(probeStatusLabel(value)) },
              {
                title: '操作',
                width: probeColumnWidths[7],
                render: (_, row) => (
                  <Space size={8}>
                    <Button type="link" onClick={() => openProbeDetail(row)}>详情</Button>
                    {row.status !== 'retired' && (
                      <Popconfirm title="确认退役该探针？" onConfirm={() => retireProbe(row)}>
                        <Button type="link" danger>退役</Button>
                      </Popconfirm>
                    )}
                  </Space>
                )
              }
            ]}
            pagination={tablePagination(20)}
          />
        </div>
      </section>
      <Drawer
        title="注册探针"
        width={520}
        open={registerOpen}
        onClose={closeRegisterDrawer}
        footer={registeredProbe ? <Button type="primary" onClick={closeRegisterDrawer}>完成</Button> : <Space><Button onClick={closeRegisterDrawer}>取消</Button><Button type="primary" onClick={saveProbe}>保存</Button></Space>}
      >
        <Space direction="vertical" className="full-width" size={12}>
          {probeMessage && <Text type="danger">{probeMessage}</Text>}
          {!registeredProbe && (
            <>
              <LabeledInput label="探针名称" value={probeForm.name} onChange={(event) => setProbeForm((current) => ({ ...current, name: event.target.value }))} />
              <LabeledInput label="区域" value={probeForm.region} onChange={(event) => setProbeForm((current) => ({ ...current, region: event.target.value }))} />
              <LabeledInput label="IP 地址" value={probeForm.ipAddress} onChange={(event) => setProbeForm((current) => ({ ...current, ipAddress: event.target.value }))} />
              <Space.Compact className="full-width">
                <span className="compact-input-label">网络类型</span>
                <Select className="full-width" value={probeForm.networkType} options={['互联网', '专线', '内网'].map((value) => ({ label: value, value }))} onChange={(value) => setProbeForm((current) => ({ ...current, networkType: value }))} />
              </Space.Compact>
              <Space.Compact className="full-width">
                <span className="compact-input-label">能力</span>
                <Select
                  mode="multiple"
                  className="full-width"
                  value={probeForm.capabilities}
                  options={['HTTP', 'TCP', 'DNS', 'CERTIFICATE'].map((value) => ({ label: value, value }))}
                  onChange={(value) => setProbeForm((current) => ({ ...current, capabilities: value }))}
                />
              </Space.Compact>
            </>
          )}
          {registeredProbe && (
            <section className="probe-access-panel">
              <h3>接入信息</h3>
              <div className="probe-access-grid">
                <div><span>节点 ID</span><strong>{registeredProbe.id}</strong></div>
                <div><span>接入地址</span><strong>{registeredProbe.gateway_url}</strong></div>
                <div><span>Token</span><strong>{registeredProbe.bootstrap_token_hint}</strong></div>
                <div><span>配置版本</span><strong>{registeredProbe.version}</strong></div>
              </div>
              <pre className="probe-bootstrap-code">{registeredProbeBootstrap}</pre>
            </section>
          )}
        </Space>
      </Drawer>
    </section>
  );
}

function AssetsPage() {
  const [models, setModels] = useState<AssetModelRow[]>([]);
  const [activeModelId, setActiveModelId] = useState(() => window.localStorage.getItem('oneall.asset.activeModelId') || businessAssetModels[0].id);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchField, setSearchField] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [recordDrawer, setRecordDrawer] = useState<{ mode: 'view' | 'create' | 'edit'; record?: Record<string, unknown> & { key: string } } | null>(null);
  const [recordDraft, setRecordDraft] = useState<Record<string, string>>({});
  const [records, setRecords] = useState<Array<Record<string, unknown> & { key: string }>>([]);
  const [assetMessage, setAssetMessage] = useState('');
  const assetTableWidth = useTableContainerWidth('.asset-model-table-wrap', 720);
  const reloadModels = () => {
    listAssetModels()
      .then((data) => {
        const nextModels = data.items.map((item) => ({ ...item, key: item.id }));
        setModels(nextModels);
      })
      .catch(() => setModels([]));
  };
  useEffect(() => {
    reloadModels();
  }, []);
  const deletedModelKeys = new Set(listDeletedAssetModelKeys());
  const allModels = [
    ...businessAssetModels.filter((model) => !deletedModelKeys.has(model.id) && !deletedModelKeys.has(model.code)).map((model) => {
      const override = models.find((item) => item.id === model.id || item.code === model.code);
      return {
        id: override?.id ?? model.id,
        name: override?.name ?? model.name,
        code: model.code,
        fields: override?.fields.map((field) => ({ key: field.key, label: field.label ?? field.key, type: field.type, required: field.required, editable: field.editable, unique: field.unique, disabled: field.disabled })) ?? model.fields,
        primaryKey: override?.primary_key ?? model.fields[0]?.key ?? '',
        platformDefault: true
      };
    }),
    ...models.filter((model) => !businessAssetModels.some((defaultModel) => defaultModel.id === model.id || defaultModel.code === model.code)).map((model) => ({
      id: model.id,
      name: model.name,
      code: model.code,
      fields: model.fields.map((field) => ({ key: field.key, label: field.label ?? field.key, type: field.type, required: field.required, editable: field.editable, unique: field.unique, disabled: field.disabled })),
      primaryKey: model.primary_key ?? model.fields[0]?.key ?? '',
      platformDefault: false
    }))
  ];
  const activeModel = allModels.find((item) => item.id === activeModelId) ?? allModels[0];
  const activeFields = activeModel?.fields ?? [];
  const activeEnabledFields = activeFields.filter((field) => !field.disabled);
  const activeTitle = activeModel?.name ?? '模型';
  useEffect(() => {
    if (!activeModel) {
      setRecords([]);
      return;
    }
    listAssetRecords(activeModel.id)
      .then((data) => setRecords(data.items.map((item) => ({ ...item, key: item.id }))))
      .catch(() => setRecords([]));
  }, [activeModel?.id]);
  useEffect(() => {
    window.localStorage.setItem('oneall.asset.activeModelId', activeModelId);
    setSearchKeyword('');
    setSearchField('all');
    setPage(1);
    setRecordDrawer(null);
  }, [activeModelId]);
  const displayedFields = activeEnabledFields;
  const visibleRecords = useMemo(() => {
    const keyword = searchKeyword.trim().toLowerCase();
    if (!keyword) return records;
    const fields = searchField === 'all' ? activeEnabledFields : activeEnabledFields.filter((field) => field.key === searchField);
    return records.filter((record) => fields.some((field) => String(record[field.key] ?? '').toLowerCase().includes(keyword)));
  }, [activeEnabledFields, records, searchField, searchKeyword]);
  const currentPage = Math.min(page, Math.max(1, Math.ceil(visibleRecords.length / pageSize)));
  const pagedRecords = visibleRecords.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const fieldWeight = (key: string, type: string, index: number) => {
    if (index === 0) return 1.4;
    if (['domain', 'url'].includes(type) || ['domain', 'hostname', 'visible_name', 'app_name_cn'].includes(key)) return 1.25;
    if (['owner', 'port'].includes(key) || ['number', 'boolean', 'status'].includes(type)) return 0.75;
    return 1;
  };
  const fieldMinWidth = (key: string, type: string, index: number) => {
    if (index === 0) return 190;
    if (['domain', 'url'].includes(type) || key === 'domain') return 180;
    if (['owner', 'port'].includes(key) || ['number', 'boolean', 'status'].includes(type)) return 96;
    return 128;
  };
  const actionColumnWidth = 140;
  const assetScrollbarCompensation = 15;
  const fieldWidths = useMemo(() => {
    const availableWidth = Math.max(560, assetTableWidth - actionColumnWidth - assetScrollbarCompensation);
    return distributeTableWidths(availableWidth, displayedFields.map((field, index) => ({
      min: fieldMinWidth(field.key, field.type, index),
      weight: fieldWeight(field.key, field.type, index)
    })));
  }, [assetTableWidth, displayedFields]);
  const assetRenderedTableWidth = fieldWidths.reduce((total, width) => total + width, actionColumnWidth);
  const openRecordDrawer = (mode: 'view' | 'create' | 'edit', record?: Record<string, unknown> & { key: string }) => {
    setRecordDrawer({ mode, record });
    const editableFields = mode === 'view' ? activeFields : activeEnabledFields;
    setRecordDraft(Object.fromEntries(editableFields.map((field) => [field.key, String(record?.[field.key] ?? '')])));
  };
  const reloadRecords = () => {
    if (!activeModel) {
      setRecords([]);
      return;
    }
    listAssetRecords(activeModel.id)
      .then((data) => setRecords(data.items.map((item) => ({ ...item, key: item.id }))))
      .catch(() => setRecords([]));
  };
  const saveRecord = () => {
    if (!activeModel) return;
    setAssetMessage('');
    const values = Object.fromEntries(activeEnabledFields.map((field) => [field.key, recordDraft[field.key] ?? '']));
    const missingRequired = activeEnabledFields.find((field) => field.required && !String(values[field.key] ?? '').trim());
    if (missingRequired) {
      setAssetMessage(`${missingRequired.label ?? missingRequired.key} 必填`);
      return;
    }
    const request = recordDrawer?.mode === 'edit' && recordDrawer.record
      ? updateAssetRecord(activeModel.id, recordDrawer.record.key, values)
      : createAssetRecord({ id: activeModel.id, code: activeModel.code }, values);
    request.then(() => {
      reloadRecords();
      setRecordDrawer(null);
    });
  };
  const tableColumns = [
    ...displayedFields.map((field, index) => ({
      title: <span className="asset-table-head-title">{field.label ?? field.key}</span>,
      dataIndex: field.key,
      ellipsis: true,
      width: fieldWidths[index],
      fixed: index === 0 ? 'left' as const : undefined,
      sorter: (a: Record<string, unknown>, b: Record<string, unknown>) => String(a[field.key] ?? '').localeCompare(String(b[field.key] ?? ''), 'zh-CN'),
      render: (value: unknown, record: Record<string, unknown> & { key: string }) => {
        if (field.type === 'status' && value) return statusTag(String(value));
        if (index === 0) {
          return <button className="asset-primary-cell" type="button" onClick={() => openRecordDrawer('view', record)}>{String(value ?? '-')}</button>;
        }
        return <span className="asset-table-cell-text">{String(value ?? '-')}</span>;
      }
    })),
    {
      title: <span className="asset-table-head-title">操作</span>,
      key: 'actions',
      fixed: 'right' as const,
      width: actionColumnWidth,
      render: (_: unknown, record: Record<string, unknown> & { key: string }) => (
        <Space size={4}>
          <Button type="link" size="small" onClick={() => openRecordDrawer('view', record)}>查看</Button>
          <Button type="link" size="small" onClick={() => openRecordDrawer('edit', record)}>编辑</Button>
          <Popconfirm
            title="确认删除实例数据？"
            okText="删除"
            cancelText="取消"
            onConfirm={() => activeModel && deleteAssetRecord(activeModel.id, record.key).then(() => { setAssetMessage(''); reloadRecords(); }).catch((error) => setAssetMessage(error instanceof Error ? error.message : '资产实例已被引用，不能删除'))}
          >
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ];
  const activePrimaryField = activeFields.find((field) => field.key === activeModel?.primaryKey) ?? activeFields[0];

  return (
    <section className="page asset-legacy-page">
      <section className="cmdb-workbench asset-instance-workbench">
        <aside className="cmdb-model-sidebar">
          <div className="cmdb-sidebar-head">模型</div>
          <div className="cmdb-model-groups">
            {allModels.length ? allModels.map((model) => (
              <button
                className={`cmdb-model-item ${model.id === activeModelId ? 'active' : ''}`}
                key={model.id}
                type="button"
                onClick={() => setActiveModelId(model.id)}
              >
                <span>{model.name}</span>
                <span>{model.code}</span>
              </button>
            )) : <div className="asset-model-empty">暂无模型</div>}
          </div>
        </aside>
        <section className="asset-model-data-shell">
          <div className="asset-model-data-head">
            <div>
              <span className="cmdb-breadcrumb">模型编码：{activeModel?.code ?? '-'}</span>
              <h5>{activeTitle}</h5>
            </div>
          </div>
          {assetMessage && <div className="asset-inline-message">{assetMessage}</div>}
          <div className="cmdb-query-bar">
            <Select
              className="cmdb-query-field"
              value={searchField}
              options={[{ label: '全部字段', value: 'all' }, ...activeEnabledFields.map((field) => ({ label: field.label, value: field.key }))]}
              onChange={(value) => {
                setSearchField(value);
                setPage(1);
              }}
            />
            <Input
              className="asset-model-search"
              allowClear
              prefix={<SearchOutlined />}
              placeholder={`搜索${activeTitle}实例`}
              value={searchKeyword}
              onChange={(event) => {
                setSearchKeyword(event.target.value);
                setPage(1);
              }}
            />
            <Button type="primary" onClick={() => openRecordDrawer('create')}>新增实例</Button>
          </div>
          <div className="asset-model-table-wrap">
            {visibleRecords.length ? (
              <>
                <Table
                  className="asset-instance-table"
                  rowKey="key"
                  size="middle"
                  dataSource={pagedRecords}
                  rowClassName={(_, index) => index % 2 === 1 ? 'asset-table-row-zebra' : ''}
                  pagination={false}
                  tableLayout="fixed"
                  sticky
                  scroll={{ x: assetRenderedTableWidth, y: 'calc(100vh - 348px)' }}
                  columns={tableColumns}
                  onRow={(record) => ({
                    onDoubleClick: () => openRecordDrawer('view', record)
                  })}
                />
                <div className="asset-table-pagination">
                  <span>共 {visibleRecords.length} 条</span>
                  <Pagination
                    current={currentPage}
                    pageSize={pageSize}
                    total={visibleRecords.length}
                    showSizeChanger
                    pageSizeOptions={[10, 20, 50, 100]}
                    onChange={(nextPage, nextPageSize) => {
                      setPage(nextPage);
                      setPageSize(nextPageSize);
                    }}
                  />
                </div>
              </>
            ) : (
              <div className="asset-table-empty-state">
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description={searchKeyword ? '未匹配到数据' : '暂无数据'}
                >
                  {!searchKeyword && <Button type="primary" onClick={() => openRecordDrawer('create')}>新增实例</Button>}
                </Empty>
              </div>
            )}
          </div>
        <Drawer
          title={recordDrawer?.mode === 'create' ? `新增${activeTitle}实例` : recordDrawer?.record && activePrimaryField ? String(recordDrawer.record[activePrimaryField.key] ?? activeTitle) : activeTitle}
          width={560}
          open={Boolean(recordDrawer)}
          onClose={() => setRecordDrawer(null)}
          extra={recordDrawer?.mode === 'view' && recordDrawer.record ? <Button type="primary" onClick={() => openRecordDrawer('edit', recordDrawer.record)}>编辑</Button> : recordDrawer ? <Space><Button onClick={() => setRecordDrawer(null)}>取消</Button><Button type="primary" onClick={saveRecord}>保存</Button></Space> : null}
        >
          {recordDrawer?.mode === 'view' && recordDrawer.record && (
            <Tabs
              items={[
                {
                  key: 'fields',
                  label: '属性',
                  children: (
                    <Descriptions
                      size="small"
                      column={1}
                      bordered
                      items={activeFields.map((field) => ({
                        key: field.key,
                        label: field.label,
                        children: field.type === 'status' && recordDrawer.record?.[field.key] ? statusTag(String(recordDrawer.record[field.key])) : String(recordDrawer.record?.[field.key] ?? '-')
                      }))}
                    />
                  )
                },
                {
                  key: 'meta',
                  label: '元信息',
                  children: (
                    <Descriptions
                      size="small"
                      column={1}
                      bordered
                      items={[
                        { key: 'source', label: '同步来源', children: String(recordDrawer.record?.source ?? 'Manual') },
                        { key: 'created_by', label: '创建人', children: String(recordDrawer.record?.created_by ?? '-') },
                        { key: 'updated_at', label: '更新时间', children: String(recordDrawer.record?.updated_at ?? '-') }
                      ]}
                    />
                  )
                },
                {
                  key: 'changes',
                  label: '变更记录',
                  children: (
                    <Timeline
                      items={[
                        { children: '最近一次同步更新实例属性' },
                        { children: '通过资产纳管工单创建实例' }
                      ]}
                    />
                  )
                }
              ]}
            />
          )}
          {recordDrawer && recordDrawer.mode !== 'view' && (
            <Space direction="vertical" className="asset-record-form" size={12}>
              {activeEnabledFields.map((field) => (
                <label className="asset-record-field" key={field.key}>
                  <span>{field.label}{field.required ? ' *' : ''}</span>
                  <Input
                    disabled={recordDrawer.mode === 'edit' && field.editable === false}
                    value={recordDraft[field.key] ?? ''}
                    placeholder={field.type}
                    onChange={(event) => setRecordDraft((draft) => ({ ...draft, [field.key]: event.target.value }))}
                  />
                </label>
              ))}
            </Space>
          )}
        </Drawer>
        </section>
      </section>
    </section>
  );
}

function AssetModelManagementPage() {
  const [activeModelId, setActiveModelId] = useState(businessAssetModels[0].id);
  const [apiModels, setApiModels] = useState<AssetModelRow[]>([]);
  const [editor, setEditor] = useState<AssetModelEditorState | null>(null);
  const [savingModel, setSavingModel] = useState(false);
  const [modelMessage, setModelMessage] = useState('');
  const [deletedModelVersion, setDeletedModelVersion] = useState(0);
  const tableWidth = useTableContainerWidth('.model-management-shell', 1120);
  const modelMetaFlexibleWidth = Math.max(420, tableWidth - 700);
  const modelNameColumnWidth = Math.floor(modelMetaFlexibleWidth * 0.46);
  const modelCodeColumnWidth = modelMetaFlexibleWidth - modelNameColumnWidth;
  const reloadApiModels = () => {
    return listAssetModels()
      .then((data) => setApiModels(data.items.map((item) => ({ ...item, key: item.id }))))
      .catch(() => setApiModels([]));
  };
  useEffect(() => {
    reloadApiModels();
  }, []);
  const deletedModelKeys = useMemo(() => new Set(listDeletedAssetModelKeys()), [deletedModelVersion]);
  const managedModels: Array<{
    id: string;
    name: string;
    code: string;
    category: string;
    source: string;
    fields: AssetFieldDraft[];
    primaryKey: string;
    platformDefault: boolean;
  }> = [
    ...businessAssetModels.filter((model) => !deletedModelKeys.has(model.id) && !deletedModelKeys.has(model.code)).map((model) => {
      const override = apiModels.find((item) => item.id === model.id || item.code === model.code);
      return {
        id: override?.id ?? model.id,
        name: override?.name ?? model.name,
        code: model.code,
        category: model.category,
        source: '平台默认',
        fields: override?.fields.map((field) => ({ key: field.key, label: field.label ?? field.key, type: field.type, required: field.required, editable: field.editable, unique: field.unique, disabled: field.disabled })) ?? model.fields,
        primaryKey: override?.primary_key ?? model.fields[0]?.key ?? '',
        platformDefault: true
      };
    }),
    ...apiModels.filter((model) => !businessAssetModels.some((defaultModel) => defaultModel.id === model.id || defaultModel.code === model.code)).map((model) => ({
      id: model.id,
      name: model.name,
      code: model.code,
      category: '自定义模型',
      source: model.created_by,
      fields: model.fields.map((field) => ({ key: field.key, label: field.label ?? field.key, type: field.type, required: field.required, editable: field.editable, unique: field.unique, disabled: field.disabled })),
      primaryKey: model.primary_key ?? model.fields[0]?.key ?? '',
      platformDefault: false
    }))
  ];
  const activeModel = managedModels.find((model) => model.id === activeModelId) ?? managedModels[0];
  const modelRows = managedModels.map((model) => ({
    key: model.id,
    id: model.id,
    name: model.name,
    code: model.code,
    category: model.category,
    source: model.source,
    fields: model.fields.length,
    primary: model.fields.find((field) => field.key === model.primaryKey)?.label ?? model.fields[0]?.label ?? '-',
    type: '自定义'
  }));
  const openCreateModel = () => {
    setModelMessage('');
    setEditor({
      mode: 'create',
      name: '业务服务',
      code: `custom-${Date.now()}`,
      category: '自定义模型',
      source: 'Manual',
      primaryKey: 'name',
      fields: [{ key: 'name', label: '名称', type: 'string', required: true, editable: true, unique: true, disabled: false }]
    });
  };
  const openEditModel = (modelId = activeModel?.id) => {
    const target = managedModels.find((model) => model.id === modelId);
    if (!target) {
      setModelMessage('未找到模型。');
      return;
    }
    setModelMessage('');
    setActiveModelId(target.id);
    setEditor({
      mode: 'edit',
      id: target.id,
      name: target.name,
      code: target.code,
      category: target.category,
      source: target.source,
      primaryKey: target.primaryKey || target.fields[0]?.key || '',
      fields: target.fields.map((field) => ({ ...field }))
    });
  };
  const updateEditorField = (index: number, patch: Partial<AssetFieldDraft>) => {
    setEditor((current) => {
      if (!current) return current;
      const fields = current.fields.map((field, fieldIndex) => fieldIndex === index ? { ...field, ...patch } : field);
      const primaryKey = fields.some((field) => field.key === current.primaryKey) ? current.primaryKey : fields[0]?.key ?? '';
      return { ...current, fields, primaryKey };
    });
  };
  const addEditorField = () => {
    setEditor((current) => {
      if (!current) return current;
      const index = current.fields.length + 1;
      return { ...current, fields: [...current.fields, { key: `field_${index}`, label: `字段 ${index}`, type: 'string', required: false, editable: true, unique: false, disabled: false }] };
    });
  };
  const removeEditorField = async (index: number) => {
    if (!editor || editor.fields.length <= 1) return;
    const field = editor.fields[index];
    const records = editor.mode === 'edit' && editor.id ? (await listAssetRecords(editor.id).catch(() => ({ items: [] }))).items : [];
    const used = records.some((record) => String(record[field.key] ?? '').trim());
    if (used) {
      setModelMessage(`${field.label || field.key} 已被实例数据使用，不能删除，可先禁用字段。`);
      return;
    }
    setEditor((current) => {
      if (!current || current.fields.length <= 1) return current;
      const fields = current.fields.filter((_, fieldIndex) => fieldIndex !== index);
      const primaryKey = fields.some((item) => item.key === current.primaryKey) ? current.primaryKey : fields[0]?.key ?? '';
      return { ...current, fields, primaryKey };
    });
  };
  const removeModel = async (modelId: string) => {
    setModelMessage('');
    try {
      await deleteAssetModel(modelId);
      await reloadApiModels();
      setDeletedModelVersion((version) => version + 1);
      setActiveModelId((current) => current === modelId ? businessAssetModels.find((model) => model.id !== modelId && !listDeletedAssetModelKeys().includes(model.id) && !listDeletedAssetModelKeys().includes(model.code))?.id ?? '' : current);
      setModelMessage('模型已删除。');
    } catch (error) {
      setModelMessage(error instanceof Error ? error.message : '模型已被引用，不能删除');
    }
  };
  const saveEditor = async () => {
    if (!editor || savingModel) return;
    setModelMessage('');
    const fields = editor.fields.map((field) => ({
      key: field.key.trim(),
      label: field.label.trim() || field.key.trim(),
      type: field.type,
      required: Boolean(field.required),
      editable: field.editable === false ? false : true,
      unique: Boolean(field.unique),
      disabled: Boolean(field.disabled)
    }));
    const errors: string[] = [];
    if (!editor.name.trim()) errors.push('模型名称必填');
    if (!editor.code.trim()) errors.push('模型编码必填');
    if (!fields.length) errors.push('至少保留一个字段');
    if (fields.some((field) => !field.key)) errors.push('字段键不能为空');
    if (new Set(fields.map((field) => field.key)).size !== fields.length) errors.push('字段键不能重复');
    if (!fields.some((field) => field.key === editor.primaryKey)) errors.push('主显示字段必须来自字段清单');
    if (errors.length) {
      setModelMessage(errors[0]);
      return;
    }
    const orderedFields = [
      ...fields.filter((field) => field.key === editor.primaryKey),
      ...fields.filter((field) => field.key !== editor.primaryKey)
    ];
    setSavingModel(true);
    try {
      const modelExistsInStore = apiModels.some((model) => model.id === editor.id || model.code === editor.code);
      const saved = editor.mode === 'create'
        ? await createAssetModel({ name: editor.name.trim(), code: editor.code.trim(), fields: orderedFields, primary_key: editor.primaryKey })
        : modelExistsInStore
          ? await updateAssetModel(editor.id ?? editor.code, { name: editor.name.trim(), fields: orderedFields, primary_key: editor.primaryKey, status: 'active' })
          : await createAssetModel({ id: editor.id, name: editor.name.trim(), code: editor.code.trim(), fields: orderedFields, primary_key: editor.primaryKey });
      await reloadApiModels();
      setActiveModelId(saved.id);
      setEditor(null);
      setModelMessage(editor.mode === 'create' ? '模型已创建，模型资产页可见。' : '字段配置已保存。');
    } catch {
      setModelMessage('保存失败，请检查字段配置或权限。');
    } finally {
      setSavingModel(false);
    }
  };

  return (
    <section className="page model-management-page">
      <div className="model-management-content">
        {modelMessage && <div className="model-message"><Text type="secondary">{modelMessage}</Text></div>}
        <div className="model-management-shell">
          <div className="model-management-toolbar">
            <Button type="primary" icon={<BoxPlotOutlined />} onClick={openCreateModel}>新建模型</Button>
          </div>
          <Table
            className="nowrap-table"
            size="middle"
            pagination={false}
            dataSource={modelRows}
            scroll={{ x: tableWidth }}
            tableLayout="fixed"
            rowClassName={(record) => record.id === activeModelId ? 'selected-row' : ''}
            onRow={(record) => ({
              onClick: () => setActiveModelId(record.id)
            })}
            columns={[
              { title: '模型名称', dataIndex: 'name', width: modelNameColumnWidth, ellipsis: true },
              { title: '模型编码', dataIndex: 'code', width: modelCodeColumnWidth, ellipsis: true },
              { title: '分类', dataIndex: 'category', width: 120 },
              { title: '数据来源', dataIndex: 'source', width: 120 },
              { title: '字段数', dataIndex: 'fields', width: 90 },
              { title: '主显示字段', dataIndex: 'primary', width: 130 },
              { title: '类型', dataIndex: 'type', width: 90 },
              {
                title: '操作',
                width: 150,
                render: (_, record) => (
                  <Space size={4}>
                    <Button type="link" onClick={(event) => { event.stopPropagation(); openEditModel(record.id); }}>编辑</Button>
                    <Popconfirm
                      title="确认删除模型？"
                      description="删除前会校验实例、同步任务、工单、告警和策略引用。"
                      okText="删除"
                      cancelText="取消"
                      onConfirm={(event) => {
                        event?.stopPropagation();
                        return removeModel(record.id);
                      }}
                    >
                      <Button type="link" danger onClick={(event) => event.stopPropagation()}>删除</Button>
                    </Popconfirm>
                  </Space>
                )
              }
            ]}
          />
        </div>
      </div>
      <Modal
        title={editor?.mode === 'create' ? '新建模型' : '编辑模型'}
        open={Boolean(editor)}
        width={1040}
        className="model-editor-modal"
        onCancel={() => setEditor(null)}
        onOk={saveEditor}
        confirmLoading={savingModel}
        okText="保存"
        cancelText="取消"
      >
        {editor && (
          <div className="model-editor">
            <div className="model-editor-section">
              <Text className="model-editor-section-title">基础信息</Text>
              <div className="model-editor-base">
                <label className="model-text-field">
                  <span>模型名称</span>
                  <Input value={editor.name} onChange={(event) => setEditor({ ...editor, name: event.target.value })} />
                </label>
                {editor.mode === 'create'
                  ? (
                    <label className="model-text-field">
                      <span>模型编码</span>
                      <Input value={editor.code} onChange={(event) => setEditor({ ...editor, code: event.target.value })} />
                    </label>
                  )
                  : (
                    <div className="model-readonly-field">
                      <span>模型编码</span>
                      <strong>{editor.code}</strong>
                    </div>
                  )}
                <label className="model-select-field">
                  <span>主显示字段</span>
                  <Select value={editor.primaryKey} options={editor.fields.map((field) => ({ label: field.label || field.key, value: field.key }))} onChange={(value) => setEditor({ ...editor, primaryKey: value })} />
                  <em>用于资产列表第一列和详情标题</em>
                </label>
                <label className="model-select-field">
                  <span>唯一键</span>
                  <Select value={editor.primaryKey} options={editor.fields.map((field) => ({ label: field.label || field.key, value: field.key }))} onChange={(value) => setEditor({ ...editor, primaryKey: value, fields: editor.fields.map((field) => ({ ...field, unique: field.key === value })) })} />
                  <em>用于识别同一条资产实例</em>
                </label>
              </div>
            </div>
            <div className="model-editor-toolbar">
              <Text type="secondary">字段配置</Text>
              <Button size="small" onClick={addEditorField}>新增字段</Button>
            </div>
            <Table
              className="model-editor-table"
              size="small"
              pagination={false}
              tableLayout="fixed"
              scroll={{ x: 930, y: 360 }}
              dataSource={editor.fields.map((field, index) => ({ ...field, rowKey: `${field.key}-${index}`, index }))}
              rowKey="rowKey"
              columns={[
                {
                  title: '字段键',
                  dataIndex: 'key',
                  width: 180,
                  render: (value, record) => <Input value={value} onChange={(event) => updateEditorField(record.index, { key: event.target.value })} />
                },
                {
                  title: '显示名',
                  dataIndex: 'label',
                  width: 180,
                  render: (value, record) => <Input value={value} onChange={(event) => updateEditorField(record.index, { label: event.target.value })} />
                },
                {
                  title: '类型',
                  dataIndex: 'type',
                  width: 130,
                  render: (value, record) => <Select className="full-width" value={value} options={[
                    { label: 'string', value: 'string' },
                    { label: 'number', value: 'number' },
                    { label: 'enum', value: 'enum' },
                    { label: 'ip', value: 'ip' },
                    { label: 'url', value: 'url' },
                    { label: 'datetime', value: 'datetime' },
                    { label: 'boolean', value: 'boolean' },
                    { label: 'status', value: 'status' }
                  ]} onChange={(next) => updateEditorField(record.index, { type: next })} />
                },
                {
                  title: '必填',
                  dataIndex: 'required',
                  width: 88,
                  render: (value, record) => <Select className="full-width" value={value ? 'yes' : 'no'} options={[{ label: '是', value: 'yes' }, { label: '否', value: 'no' }]} onChange={(next) => updateEditorField(record.index, { required: next === 'yes' })} />
                },
                {
                  title: '可编辑',
                  dataIndex: 'editable',
                  width: 88,
                  render: (value, record) => <Select className="full-width" value={value === false ? 'no' : 'yes'} options={[{ label: '是', value: 'yes' }, { label: '否', value: 'no' }]} onChange={(next) => updateEditorField(record.index, { editable: next === 'yes' })} />
                },
                {
                  title: '唯一',
                  dataIndex: 'unique',
                  width: 88,
                  render: (value, record) => <Select className="full-width" value={value ? 'yes' : 'no'} options={[{ label: '是', value: 'yes' }, { label: '否', value: 'no' }]} onChange={(next) => updateEditorField(record.index, { unique: next === 'yes' })} />
                },
                {
                  title: '状态',
                  dataIndex: 'disabled',
                  width: 96,
                  render: (value, record) => <Select className="full-width" value={value ? 'disabled' : 'enabled'} options={[{ label: '启用', value: 'enabled' }, { label: '禁用', value: 'disabled' }]} onChange={(next) => updateEditorField(record.index, { disabled: next === 'disabled' })} />
                },
                {
                  title: '操作',
                  width: 80,
                  render: (_, record) => <Button type="link" danger disabled={editor.fields.length <= 1} onClick={() => removeEditorField(record.index)}>删除</Button>
                }
              ]}
            />
          </div>
        )}
      </Modal>
    </section>
  );
}

function AssetSyncPage() {
  const { notification: notificationApi } = AntApp.useApp();
  const { models, loading, reload: reloadModels } = useAssetModelsSnapshot();
  const [selectedModelId, setSelectedModelId] = useState<string>();
  const [scriptName, setScriptName] = useState('sync-assets');
  const [syncScript, setSyncScript] = useState(`# 输出 records 列表，字段名会按下方映射写入目标模型
records = []
for item in items:
    records.append({
        "domain": item.get("domain", ""),
        "system_name": item.get("system_name", ""),
        "owner": item.get("owner", "")
    })

return records`);
  const [scriptDialog, setScriptDialog] = useState<{ open: boolean }>({ open: false });
  const [scriptDraft, setScriptDraft] = useState('');
  const [fieldMapping, setFieldMapping] = useState<Record<string, string>>({});
  const [savedScripts, setSavedScripts] = useState<ApiAssetSyncScript[]>([]);
  const [activeScriptId, setActiveScriptId] = useState<string>();
  const [savingScript, setSavingScript] = useState(false);
  const [runs, setRuns] = useState<ApiAssetSyncRun[]>([]);
  const [runDrawer, setRunDrawer] = useState<ApiAssetSyncRun | null>(null);
  const [syncing, setSyncing] = useState(false);
  const selectedModel = models.find((model) => model.id === selectedModelId) ?? models[0];
  const enabledFields = (selectedModel?.fields ?? []).filter((field) => !field.disabled);
  const primaryKey = selectedModel?.primary_key ?? enabledFields[0]?.key;
  const buildScriptTemplate = (fields = enabledFields) => `# 输出 records 列表，字段名会用于右侧映射
# 后端会提供 items 入参，用户只需要按目标模型组装字段
records = []
for item in items:
    records.append({
${fields.map((field) => `        "${field.key}": item.get("${field.key}", ""),`).join('\n')}
    })

return records`;
  const readScriptOutputFields = (script: string) => {
    const fieldNames = new Set<string>();
    const objectMatch = script.match(/\(\s*\{([\s\S]*?)\}\s*\)/) ?? script.match(/return\s+\[?\s*\{([\s\S]*?)\}/);
    const body = objectMatch?.[1] ?? script;
    for (const match of body.matchAll(/(?:^|\n|\r|,)\s*(?:['"]?)([A-Za-z_][A-Za-z0-9_]*)(?:['"]?)\s*:/g)) {
      fieldNames.add(match[1]);
    }
    return Array.from(fieldNames);
  };
  const scriptOutputFields = useMemo(() => {
    const fieldNames = readScriptOutputFields(syncScript);
    if (!fieldNames.length) {
      return enabledFields.map((field) => ({ label: field.key, value: field.key }));
    }
    return fieldNames.map((field) => ({ label: field, value: field }));
  }, [syncScript, enabledFields.map((field) => field.key).join('|')]);
  const mappingRows = enabledFields.map((field) => {
    const required = Boolean(field.required || field.unique || primaryKey === field.key);
    const mappedSource = fieldMapping[field.key];
    return {
      key: field.key,
      target: field.label ?? field.key,
      targetKey: field.key,
      type: field.type,
      required: required ? '是' : '否',
      source: mappedSource,
      status: mappedSource ? '已映射' : required ? '缺失' : '可选'
    };
  });
  const mappingErrors = mappingRows.filter((row) => row.required === '是' && !row.source).map((row) => `${row.target} 必须映射脚本输出字段`);
  const syncRows = runs.map((item) => ({
    key: item.event_id,
    batch: item.event_id,
    source: item.payload?.script ?? item.payload?.source ?? '-',
    version: item.payload?.script_version ?? '-',
    model: models.find((model) => model.id === item.payload?.model_id)?.name ?? item.payload?.model_id ?? '-',
    status: item.event_type.includes('failed') ? '失败' : '已完成',
    add: item.payload?.count ?? 0,
    update: item.payload?.update_count ?? 0,
    fail: item.payload?.fail_count ?? (item.event_type.includes('failed') ? 1 : 0),
    reason: item.payload?.error_message ?? item.payload?.reason ?? '-',
    operator: item.payload?.operator ?? item.producer ?? '-',
    time: item.created_at?.slice(0, 16).replace('T', ' ') ?? '-',
    raw: item
  }));
  const activeScript = activeScriptId
    ? savedScripts.find((script) => script.id === activeScriptId)
    : selectedModel ? savedScripts.find((script) => script.model_id === selectedModel.id) : undefined;
  const activeScriptForSelectedModel = activeScript?.model_id === selectedModel?.id ? activeScript : undefined;
  const currentScriptVersion = activeScriptForSelectedModel?.current_version ?? activeScriptForSelectedModel?.script_versions?.[0]?.version ?? '草稿';
  const normalizeFieldMapping = (mapping: Record<string, string>) => JSON.stringify(
    Object.keys(mapping).sort().map((key) => [key, mapping[key]])
  );
  const hasSavedConfig = Boolean(activeScriptForSelectedModel);
  const hasUnsavedChanges = !activeScriptForSelectedModel
    || activeScriptForSelectedModel.script_name !== scriptName.trim()
    || activeScriptForSelectedModel.script_content !== syncScript
    || normalizeFieldMapping(activeScriptForSelectedModel.field_mapping) !== normalizeFieldMapping(fieldMapping);
  const canRunSync = Boolean(
    selectedModel
    && hasSavedConfig
    && !hasUnsavedChanges
    && scriptName.trim()
    && syncScript.trim()
    && !mappingErrors.length
  );
  const configStatusText = activeScriptForSelectedModel
    ? hasUnsavedChanges
      ? '有未保存变更'
      : `已保存 · ${activeScriptForSelectedModel.updated_at.slice(0, 16).replace('T', ' ')}`
    : '未保存';
  const reloadRuns = () => {
    listAssetSyncRuns()
      .then((data) => setRuns(data.items ?? []))
      .catch(() => setRuns([]));
  };
  const reloadScripts = () => {
    listAssetSyncScripts()
      .then((data) => setSavedScripts(data.items ?? []))
      .catch(() => setSavedScripts([]));
  };
  const applyScript = (script: ApiAssetSyncScript) => {
    setActiveScriptId(script.id);
    setSelectedModelId(script.model_id);
    setScriptName(script.script_name);
    setSyncScript(script.script_content);
    setFieldMapping(script.field_mapping);
  };
  const loadModelScriptDraft = (model: ApiAssetModel | undefined, scripts = savedScripts) => {
    if (!model) return;
    const existingScript = scripts.find((script) => script.model_id === model.id);
    if (existingScript) {
      applyScript(existingScript);
      return;
    }
    const nextFields = model.fields.filter((field) => !field.disabled);
    setActiveScriptId(undefined);
    setSelectedModelId(model.id);
    setScriptName('sync-assets');
    setSyncScript(buildScriptTemplate(nextFields));
    setFieldMapping(Object.fromEntries(nextFields.map((field) => [field.key, field.key])));
  };
  const openAssetModel = (modelId: string) => {
    window.localStorage.setItem('oneall.asset.activeModelId', modelId);
    window.location.hash = 'assets';
  };
  const notifySyncInfo = (description: string) => {
    notificationApi.info({
      message: '同步配置',
      description,
      placement: 'topRight',
      duration: 3
    });
  };
  const notifySyncSuccess = (description: string, modelId?: string) => {
    notificationApi.success({
      message: '同步完成',
      description,
      placement: 'topRight',
      duration: 4.5,
      actions: modelId ? <Button size="small" type="link" onClick={() => openAssetModel(modelId)}>查看模型资产</Button> : undefined
    });
  };
  const notifySyncFailure = (run: ApiAssetSyncRun, description: string) => {
    notificationApi.error({
      message: '同步失败',
      description,
      placement: 'topRight',
      duration: 0,
      actions: <Button size="small" type="link" onClick={() => setRunDrawer(run)}>查看失败详情</Button>
    });
  };
  const writeFailureRun = (errorType: NonNullable<ApiAssetSyncRun['payload']['error_type']>, errorMessage: string, errorDetail?: string) => {
    recordAssetSyncFailure({
      modelId: selectedModel?.id,
      source: 'script',
      script: scriptName.trim() || 'sync-assets',
      scriptId: activeScriptForSelectedModel?.id,
      scriptVersion: currentScriptVersion,
      errorType,
      errorMessage,
      errorDetail,
      suggestion: errorType === 'mapping'
        ? '检查必填字段是否已经映射到脚本输出字段。'
        : '检查 Python 脚本是否返回 records 列表，以及字段名是否和右侧映射一致。'
    }).then((run) => {
      setRuns((items) => [run, ...items.filter((item) => item.event_id !== run.event_id)]);
      notifySyncFailure(run, errorMessage);
    });
  };
  const downloadTemplateFile = () => {
    const template = buildScriptTemplate();
    const fileName = `${selectedModel?.code || scriptName || 'asset-sync'}-template.py`;
    const blob = new Blob([template], { type: 'text/x-python;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  const downloadCurrentScriptFile = () => {
    const fileName = `${scriptName || 'asset-sync'}.py`;
    const blob = new Blob([syncScript || buildScriptTemplate()], { type: 'text/x-python;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  const openScriptEditor = () => {
    setScriptDraft(syncScript);
    setScriptDialog({ open: true });
  };
  const saveScriptDraft = () => {
    const outputFields = new Set(readScriptOutputFields(scriptDraft));
    setSyncScript(scriptDraft);
    setFieldMapping(Object.fromEntries(enabledFields.filter((field) => outputFields.has(field.key)).map((field) => [field.key, field.key])));
    setScriptDialog({ open: false });
  };
  const clearScriptFile = () => {
    setScriptName('sync-assets');
    setSyncScript('');
    setFieldMapping({});
    notifySyncInfo('已移除当前脚本草稿。');
  };
  const saveCurrentScript = () => {
    if (!selectedModel) {
      notifySyncInfo('请先选择目标模型。');
      return;
    }
    if (!scriptName.trim() || !syncScript.trim()) {
      notifySyncInfo('请先选择脚本文件或编辑脚本草稿。');
      return;
    }
    if (mappingErrors.length) {
      notifySyncInfo(mappingErrors[0]);
      return;
    }
    setSavingScript(true);
    saveAssetSyncScript({
      id: activeScriptForSelectedModel?.id,
      name: `${selectedModel.name} 同步脚本`,
      model_id: selectedModel.id,
      script_name: scriptName.trim(),
      script_content: syncScript,
      field_mapping: fieldMapping,
      enabled: true
    })
      .then((script) => {
        setSavedScripts((items) => [script, ...items.filter((item) => item.id !== script.id)]);
        setActiveScriptId(script.id);
        notificationApi.success({
          message: '配置已保存',
          description: `同步配置已保存：${script.script_name}`,
          placement: 'topRight',
          duration: 3
        });
      })
      .catch(() => {
        notificationApi.error({
          message: '保存失败',
          description: '保存同步配置失败，请检查脚本和字段映射。',
          placement: 'topRight'
        });
      })
      .finally(() => setSavingScript(false));
  };
  const runCurrentSync = () => {
    if (!selectedModel) {
      notifySyncInfo('请先创建模型，再执行同步。');
      return;
    }
    if (!scriptName.trim() || !syncScript.trim()) {
      notifySyncInfo('请先填写同步脚本标识和脚本内容。');
      return;
    }
    if (!activeScriptForSelectedModel) {
      notifySyncInfo('请先保存配置生成版本后再执行同步。');
      return;
    }
    if (hasUnsavedChanges) {
      notifySyncInfo('当前配置有未保存变更，请先保存配置。');
      return;
    }
    if (mappingErrors.length) {
      notifySyncInfo(mappingErrors[0]);
      writeFailureRun('mapping', mappingErrors[0], mappingErrors.join('\n'));
      return;
    }
    setSyncing(true);
    runAssetSync(selectedModel.id, {
      source: 'script',
      script: scriptName.trim(),
      scriptId: activeScriptForSelectedModel?.id,
      scriptVersion: currentScriptVersion,
      mapping: fieldMapping,
      model: selectedModel
    })
      .then((result) => {
        notifySyncSuccess(`写入 ${result.count ?? result.records?.length ?? 0} 条资产记录。`, selectedModel.id);
        reloadRuns();
      })
      .catch((error) => {
        const detail = error instanceof Error ? error.message : String(error);
        writeFailureRun('system', '同步执行失败', detail);
      })
      .finally(() => setSyncing(false));
  };
  useEffect(() => {
    reloadRuns();
    reloadScripts();
  }, []);
  useEffect(() => {
    const refresh = () => {
      reloadModels();
      reloadScripts();
      reloadRuns();
    };
    window.addEventListener('oneall:asset-sync-refresh', refresh);
    return () => window.removeEventListener('oneall:asset-sync-refresh', refresh);
  }, [reloadModels]);
  useEffect(() => {
    if (!selectedModelId && models[0]) {
      setSelectedModelId(models[0].id);
    }
  }, [models, selectedModelId]);
  useEffect(() => {
    if (!selectedModel) return;
    loadModelScriptDraft(selectedModel);
  }, [selectedModel?.id, savedScripts.map((script) => `${script.id}:${script.updated_at}`).join('|')]);

  return (
    <section className="page">
      <div className="sync-page-shell">
        <section className="sync-workbench">
        <div className="sync-config-panel">
          <div className="sync-section-title">脚本配置</div>
          <div className="sync-form-grid">
            <label>
              <span>目标模型</span>
              <Select
                loading={loading}
                value={selectedModel?.id}
                placeholder="选择目标模型"
                options={models.map((model) => ({ label: `${model.name} / ${model.code}`, value: model.id }))}
                onChange={(value) => {
                  const nextModel = models.find((model) => model.id === value);
                  loadModelScriptDraft(nextModel);
                }}
              />
            </label>
            <label>
              <span>同步方式</span>
              <Input value="脚本同步" disabled />
            </label>
            <label>
              <span>脚本标识</span>
              <Input value={scriptName} onChange={(event) => setScriptName(event.target.value)} placeholder="例如 sync-domain-from-cmdb" />
            </label>
            <div className="sync-script-file-section">
              <div className="sync-script-file-header">
                <span>脚本文件</span>
                <Button type="link" size="small" onClick={downloadTemplateFile}>获取模板文件</Button>
              </div>
              <div className="sync-script-file-actions">
                <Upload
                  accept=".py,.txt"
                  showUploadList={false}
                  beforeUpload={(file) => {
                    file.text().then((text) => {
                      const outputFields = new Set(readScriptOutputFields(text));
                      setScriptName(file.name.replace(/\.[^.]+$/, '') || 'sync-assets');
                      setSyncScript(text);
                      setFieldMapping(Object.fromEntries(enabledFields.filter((field) => outputFields.has(field.key)).map((field) => [field.key, field.key])));
                      notifySyncInfo(`已上传 ${file.name}，当前脚本草稿已替换。`);
                    });
                    return false;
                  }}
                >
                  <Button icon={<UploadOutlined />}>选择文件</Button>
                </Upload>
              </div>
              <Text type="secondary" className="sync-script-file-note">Python 脚本输出 records 列表；输出字段用于右侧映射。</Text>
              <div className="sync-script-file-row">
                <div>
                  <strong>{scriptName || '未命名脚本'}</strong>
                  <span>{scriptOutputFields.length} 个输出字段 · {currentScriptVersion}</span>
                </div>
                <Space size={4}>
                  <Button type="text" aria-label="下载当前脚本" icon={<DownloadOutlined />} onClick={downloadCurrentScriptFile} />
                  <Button type="text" onClick={openScriptEditor}>编辑</Button>
                  <Button type="text" danger aria-label="清空当前脚本" icon={<DeleteOutlined />} onClick={clearScriptFile} />
                </Space>
              </div>
            </div>
          </div>
          <Descriptions
            size="small"
            bordered
            column={1}
            items={[
              { key: 'model', label: '模型编码', children: selectedModel?.code ?? '-' },
              { key: 'fields', label: '同步字段', children: enabledFields.length },
              { key: 'required', label: '必映射', children: mappingRows.filter((row) => row.required === '是').length },
              { key: 'missing', label: '缺失映射', children: mappingErrors.length },
              { key: 'version', label: '脚本版本', children: currentScriptVersion },
              { key: 'saved', label: '配置状态', children: configStatusText },
              { key: 'operator', label: '最近保存', children: activeScriptForSelectedModel?.updated_by ?? '-' }
            ]}
          />
          <div className="sync-panel-actions">
            <Button loading={savingScript} disabled={!selectedModel} onClick={saveCurrentScript}>保存配置</Button>
            <Tooltip title={canRunSync ? undefined : '请先保存配置后再执行同步'}>
              <Button type="primary" loading={syncing} disabled={!canRunSync} onClick={runCurrentSync}>执行同步</Button>
            </Tooltip>
          </div>
        </div>
        <div className="sync-main-panel">
          <div className="sync-section-title">字段映射</div>
          <Table
            className="sync-mapping-table"
            size="middle"
            pagination={false}
            dataSource={mappingRows}
            locale={{ emptyText: selectedModel ? '当前模型没有可同步字段' : '请先创建模型' }}
            columns={[
              { title: '目标字段', dataIndex: 'target', width: 180 },
              { title: '字段键', dataIndex: 'targetKey', width: 160 },
              { title: '类型', dataIndex: 'type', width: 100 },
              { title: '必映射', dataIndex: 'required', width: 90 },
              {
                title: '脚本输出字段',
                dataIndex: 'source',
                render: (value, record) => (
                  <Select
                    className="full-width"
                    mode="tags"
                    maxCount={1}
                    placeholder="脚本输出字段"
                    value={value ? [value] : []}
                    options={scriptOutputFields}
                    onChange={(nextValues) => {
                      const next = nextValues[0];
                      setFieldMapping((current) => {
                        const copy = { ...current };
                        if (next) copy[record.targetKey] = next;
                        else delete copy[record.targetKey];
                        return copy;
                      });
                    }}
                  />
                )
              },
              { title: '校验', dataIndex: 'status', width: 100, render: statusTag }
            ]}
          />
        </div>
        </section>
        <section className="sync-history-panel">
        <div className="sync-section-title">同步历史</div>
        <Table
          size="middle"
          dataSource={syncRows}
          locale={{ emptyText: '暂无同步记录' }}
          columns={[
            { title: '批次', dataIndex: 'batch' },
            { title: '数据源', dataIndex: 'source' },
            { title: '版本', dataIndex: 'version', width: 90 },
            { title: '模型', dataIndex: 'model' },
            { title: '状态', dataIndex: 'status', render: statusTag },
            { title: '新增', dataIndex: 'add' },
            { title: '更新', dataIndex: 'update' },
            { title: '失败', dataIndex: 'fail' },
            { title: '失败原因', dataIndex: 'reason', ellipsis: true },
            { title: '操作人', dataIndex: 'operator', width: 110 },
            { title: '时间', dataIndex: 'time' },
            {
              title: '操作',
              width: 120,
              render: (_, record) => (
                <Space size={0}>
                  <Button type="link" onClick={() => setRunDrawer(record.raw)}>详情</Button>
                  {record.raw.event_type.includes('failed') && (
                    <Tooltip title="按当前配置重新执行同步">
                      <Button type="link" disabled={!canRunSync} onClick={runCurrentSync}>重试</Button>
                    </Tooltip>
                  )}
                </Space>
              )
            }
          ]}
        />
        </section>
      </div>
      <Drawer
        title={runDrawer?.event_type.includes('failed') ? '同步失败详情' : '同步执行详情'}
        width={720}
        open={Boolean(runDrawer)}
        onClose={() => setRunDrawer(null)}
      >
        {runDrawer && (
          <Space direction="vertical" size={16} className="full-width">
            <Descriptions
              bordered
              size="small"
              column={2}
              items={[
                { key: 'batch', label: '批次', children: runDrawer.event_id },
                { key: 'status', label: '状态', children: statusTag(runDrawer.event_type.includes('failed') ? '失败' : '已完成') },
                { key: 'script', label: '脚本', children: runDrawer.payload.script ?? '-' },
                { key: 'version', label: '版本', children: runDrawer.payload.script_version ?? '-' },
                { key: 'operator', label: '操作人', children: runDrawer.payload.operator ?? runDrawer.producer },
                { key: 'time', label: '时间', children: runDrawer.created_at }
              ]}
            />
            {runDrawer.event_type.includes('failed') && (
              <div className="sync-error-detail">
                <div className="sync-section-title">错误信息</div>
                <Descriptions
                  bordered
                  size="small"
                  column={1}
                  items={[
                    { key: 'type', label: '错误分类', children: runDrawer.payload.error_type ?? '-' },
                    { key: 'message', label: '失败原因', children: runDrawer.payload.error_message ?? runDrawer.payload.reason ?? '-' },
                    { key: 'suggestion', label: '处理建议', children: runDrawer.payload.suggestion ?? '-' }
                  ]}
                />
                <Input.TextArea
                  className="sync-error-log"
                  value={runDrawer.payload.error_detail ?? runDrawer.payload.error_message ?? ''}
                  rows={8}
                  readOnly
                />
              </div>
            )}
          </Space>
        )}
      </Drawer>
      <Modal
        title="编辑脚本草稿"
        open={scriptDialog.open}
        width={900}
        onCancel={() => setScriptDialog({ open: false })}
        footer={
          <Space>
            <Button onClick={() => setScriptDialog({ open: false })}>取消</Button>
            <Button type="primary" onClick={saveScriptDraft}>保存草稿</Button>
          </Space>
        }
      >
        <div className="sync-script-modal">
          <div className="sync-script-modal-meta">
            <LabeledInput label="脚本标识" value={scriptName} onChange={(event) => setScriptName(event.target.value)} />
            <div className="sync-script-output-tags">
              {readScriptOutputFields(scriptDraft).map((field) => <Tag key={field}>{field}</Tag>)}
            </div>
          </div>
          <Input.TextArea
            value={scriptDraft}
            onChange={(event) => setScriptDraft(event.target.value)}
            rows={18}
            spellCheck={false}
            className="sync-script-editor"
          />
        </div>
      </Modal>
    </section>
  );
}

function useAssetModelsSnapshot() {
  const [models, setModels] = useState<ApiAssetModel[]>([]);
  const [loading, setLoading] = useState(false);
  const reload = () => {
    setLoading(true);
    listAssetModels()
      .then((data) => {
        const deletedKeys = new Set(listDeletedAssetModelKeys());
        const mergedDefaults = businessAssetModels
          .filter((model) => !deletedKeys.has(model.id) && !deletedKeys.has(model.code))
          .map((model) => {
            const override = data.items.find((item) => item.id === model.id || item.code === model.code);
            return override ?? {
              id: model.id,
              name: model.name,
              code: model.code,
              fields: model.fields,
              primary_key: model.fields[0]?.key,
              status: 'active',
              created_by: '平台默认',
              created_at: ''
            };
          });
        const customModels = data.items.filter((model) => !businessAssetModels.some((defaultModel) => defaultModel.id === model.id || defaultModel.code === model.code));
        setModels([...mergedDefaults, ...customModels]);
      })
      .catch(() => setModels([]))
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    reload();
  }, []);
  return { models, loading, reload };
}

function AssetNewPage() {
  const [name, setName] = useState('支付域名服务');
  const [code, setCode] = useState(`asset_model_${Date.now()}`);
  const [created, setCreated] = useState<ApiAssetModel | null>(null);
  const createModel = () => {
    createAssetModel({
      name,
      code,
      fields: [
        { key: 'name', type: 'string', label: '名称' },
        { key: 'domain', type: 'string', label: '域名' },
        { key: 'owner', type: 'string', label: '负责人' },
        { key: 'environment', type: 'enum', label: '环境' }
      ]
    }).then(setCreated);
  };
  return (
    <section className="page">
      <PageHeader
        module="资产中心 / 模型管理"
        title="新建模型"
        desc="平台默认提供四个模型，管理员可继续按自定义模型维护模型编码、字段和数据责任人。"
        action={<Space><Button>保存草稿</Button><Button type="primary" icon={<BoxPlotOutlined />} onClick={createModel}>创建模型</Button></Space>}
      />
      <div className="detail-shell">
        <div className="detail-main">
          <SectionBlock title="模型基础信息">
            <div className="form-grid">
              <LabeledInput label="模型名称" value={name} onChange={(event) => setName(event.target.value)} />
              <LabeledInput label="模型编码" value={code} onChange={(event) => setCode(event.target.value)} />
              <Select value="OpsAdmin" options={[{ label: 'OpsAdmin', value: 'OpsAdmin' }, { label: 'PlatformAdmin', value: 'PlatformAdmin' }]} />
            </div>
            {created && <Descriptions bordered size="small" column={3} style={{ marginTop: 12 }}>
              <Descriptions.Item label="模型 ID">{created.id}</Descriptions.Item>
              <Descriptions.Item label="字段数">{created.fields.length}</Descriptions.Item>
              <Descriptions.Item label="状态">{statusTag(created.status)}</Descriptions.Item>
            </Descriptions>}
          </SectionBlock>
          <SectionBlock title="字段定义">
            <Table
              pagination={false}
              dataSource={[
                { key: 'name', field: 'name', label: '名称', type: 'string', required: '是' },
                { key: 'domain', field: 'domain', label: '域名', type: 'string', required: '是' },
                { key: 'owner', field: 'owner', label: '负责人', type: 'string', required: '否' },
                { key: 'environment', field: 'environment', label: '环境', type: 'enum', required: '否' }
              ]}
              columns={[
                { title: '字段键', dataIndex: 'field' },
                { title: '显示名', dataIndex: 'label' },
                { title: '类型', dataIndex: 'type' },
                { title: '必填', dataIndex: 'required', render: statusTag }
              ]}
            />
          </SectionBlock>
        </div>
        <div className="detail-side">
          <SectionBlock title="创建后配置顺序">
            <Steps direction="vertical" current={0} items={[
              { title: '定义模型字段', description: '名称、编码、字段类型' },
              { title: '配置同步映射', description: '选择 CMDB/Zabbix 等来源' },
              { title: '绑定权限范围', description: '按角色控制读写和同步' },
              { title: '接入策略和工单', description: '成为平台数据底座' }
            ]} />
          </SectionBlock>
        </div>
      </div>
    </section>
  );
}

function AssetRecordsPage() {
  const { models } = useAssetModelsSnapshot();
  const [modelId, setModelId] = useState('');
  const [rows, setRows] = useState<Array<Record<string, unknown> & { key: string }>>([]);
  const activeModel = models.find((item) => item.id === modelId) ?? models[0];
  useEffect(() => {
    if (!modelId && models[0]) setModelId(models[0].id);
  }, [models, modelId]);
  useEffect(() => {
    if (!activeModel) return;
    listAssetRecords(activeModel.id)
      .then((data) => setRows(data.items.map((item) => ({ ...item, key: item.id }))))
      .catch(() => setRows([]));
  }, [activeModel?.id]);
  return (
    <section className="page">
      <PageHeader module="资产中心 / 模型详情" title="数据记录" desc="数据记录页展示某个用户模型下的真实资产实例，支持按模型字段查询和后续关联告警。" action={<Button type="primary">批量导入</Button>} />
      <FilterBar>
        <Select
          value={activeModel?.id}
          options={models.map((item) => ({ label: item.name, value: item.id }))}
          onChange={setModelId}
          placeholder="选择模型"
        />
      </FilterBar>
      <div className="data-card">
        <Table
          dataSource={rows}
          locale={{ emptyText: activeModel ? '暂无资产记录' : '请先创建资产模型' }}
          columns={[
            { title: '记录 ID', dataIndex: 'id', width: 170, ellipsis: true },
            { title: '名称', dataIndex: 'name' },
            { title: '负责人', dataIndex: 'owner', width: 110 },
            { title: '环境', dataIndex: 'environment', width: 90, render: (value) => value ? statusTag(String(value)) : '-' },
            { title: '模型编码', dataIndex: 'model_code', width: 160 },
            { title: '更新时间', dataIndex: 'updated_at', width: 190 },
            { title: '操作', width: 130, render: () => <Button type="link">查看关联</Button> }
          ]}
        />
      </div>
    </section>
  );
}

function AssetFieldsPage() {
  const { models } = useAssetModelsSnapshot();
  const model = models[0];
  const fieldRows = (model?.fields ?? []).map((field) => ({ ...field, key: field.key, label: field.label ?? field.key, source: '用户定义', quality: '已启用' }));
  return (
    <section className="page">
      <PageHeader module="资产中心 / 模型详情" title="字段配置" desc="字段配置决定资产查询、同步映射、告警范围和工单字段，不应该由系统固定预置。" action={<Space><Button>新增字段</Button><Button type="primary">保存版本</Button></Space>} />
      <CompactSummary items={[
        { label: '当前模型', value: model?.name ?? '未创建', tone: 'blue' },
        { label: '字段数', value: fieldRows.length, tone: 'green' },
        { label: '必填字段', value: fieldRows.filter((item) => ['name', 'domain'].includes(item.key)).length, tone: 'orange' }
      ]} />
      <div className="data-card">
        <Table
          dataSource={fieldRows}
          locale={{ emptyText: '请先创建模型字段' }}
          columns={[
            { title: '字段键', dataIndex: 'key' },
            { title: '显示名', dataIndex: 'label' },
            { title: '字段类型', dataIndex: 'type', width: 120 },
            { title: '来源', dataIndex: 'source', width: 120 },
            { title: '状态', dataIndex: 'quality', width: 100, render: statusTag },
            { title: '操作', width: 140, render: () => <Space><Button type="link">编辑</Button><Button type="link">映射</Button></Space> }
          ]}
        />
      </div>
    </section>
  );
}

function AssetSyncConfigPage() {
  const { models } = useAssetModelsSnapshot();
  const model = models[0];
  const fields = model?.fields ?? [];
  return (
    <section className="page">
      <PageHeader module="资产中心 / 模型详情" title="同步配置" desc="同步配置绑定用户自建模型和外部数据源，字段映射校验通过后才能预览和写入。" action={<Button type="primary" icon={<CloudSyncOutlined />}>保存同步配置</Button>} />
      <div className="detail-shell">
        <div className="detail-main">
          <SectionBlock title="目标模型">
            <Descriptions bordered size="small" column={3}>
              <Descriptions.Item label="模型">{model?.name ?? '未创建模型'}</Descriptions.Item>
              <Descriptions.Item label="编码">{model?.code ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="字段数">{fields.length}</Descriptions.Item>
            </Descriptions>
          </SectionBlock>
          <SectionBlock title="字段映射">
            <Table
              pagination={false}
              dataSource={fields.map((field) => ({ key: field.key, target: field.key, source: `bk_${field.key}`, type: field.type, status: '已校验' }))}
              locale={{ emptyText: '请先创建模型字段' }}
              columns={[
                { title: '目标字段', dataIndex: 'target' },
                { title: '来源字段', dataIndex: 'source' },
                { title: '类型', dataIndex: 'type' },
                { title: '校验', dataIndex: 'status', render: statusTag }
              ]}
            />
          </SectionBlock>
        </div>
        <div className="detail-side">
          <SectionBlock title="数据源">
            <Space direction="vertical" className="full-width">
              {dataSourceDefinitions.slice(0, 3).map((item) => <Button block key={item.type}>{item.name}</Button>)}
            </Space>
          </SectionBlock>
          <SectionBlock title="运行策略">
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="频率">每 10 分钟</Descriptions.Item>
              <Descriptions.Item label="冲突策略">按更新时间覆盖</Descriptions.Item>
              <Descriptions.Item label="失败处理">写审计并允许重试</Descriptions.Item>
            </Descriptions>
          </SectionBlock>
        </div>
      </div>
    </section>
  );
}

function AssetSyncPreviewPage() {
  const { models } = useAssetModelsSnapshot();
  const [preview, setPreview] = useState<ApiAssetSyncPreview | null>(null);
  const [resultCount, setResultCount] = useState<number | null>(null);
  const model = models[0];
  const loadPreview = () => {
    if (!model) return;
    previewAssetSync(model.id, { source: 'blueking_cmdb' }).then(setPreview);
  };
  const runSync = () => {
    if (!model) return;
    runAssetSync(model.id, { source: 'blueking_cmdb' }).then((result) => setResultCount(result.count));
  };
  useEffect(() => {
    loadPreview();
  }, [model?.id]);
  return (
    <section className="page">
      <PageHeader module="资产中心 / 同步任务" title="同步预览" desc="写入前先展示新增、更新、删除和样本记录，避免同步任务直接污染资产底座。" action={<Space><Button onClick={loadPreview}>重新预览</Button><Button type="primary" onClick={runSync}>执行同步</Button></Space>} />
      <CompactSummary items={[
        { label: '目标模型', value: model?.name ?? '未创建', tone: 'blue' },
        { label: '新增', value: preview?.creates ?? 0, tone: 'green' },
        { label: '更新', value: preview?.updates ?? 0, tone: 'orange' },
        { label: '删除', value: preview?.deletes ?? 0, tone: 'red' },
        { label: '最近写入', value: resultCount ?? '-', tone: 'blue' }
      ]} />
      <SectionBlock title="样本记录">
        <Table
          dataSource={(preview?.samples ?? []).map((sample, index) => ({ key: String(index), ...sample }))}
          locale={{ emptyText: model ? '暂无预览样本' : '请先创建模型' }}
          columns={[
            { title: '名称', dataIndex: 'name' },
            { title: 'IP', dataIndex: 'ip', width: 130 },
            { title: '负责人', dataIndex: 'owner', width: 110 },
            { title: '环境', dataIndex: 'environment', width: 90, render: (value) => value ? statusTag(String(value)) : '-' },
            { title: '业务线', dataIndex: 'business_line', width: 130 }
          ]}
        />
      </SectionBlock>
    </section>
  );
}

function AssetSyncHistoryPage() {
  const [rows, setRows] = useState<Array<{ key: string; event_id: string; event_type: string; producer: string; model: string; script: string; version: string; count: number; fail: number; status: string; created_at: string }>>([]);
  const reload = () => {
    listAssetSyncRuns()
      .then((data) => setRows(data.items.map((item) => ({
        key: item.event_id,
        event_id: item.event_id,
        event_type: item.event_type,
        producer: item.payload?.operator ?? item.producer,
        model: item.payload?.model_id ?? '-',
        script: item.payload?.script ?? item.payload?.source ?? '-',
        version: item.payload?.script_version ?? '-',
        count: item.payload?.count ?? 0,
        fail: item.payload?.fail_count ?? 0,
        status: item.event_type.includes('failed') ? '失败' : '已完成',
        created_at: item.created_at
      }))))
      .catch(() => setRows([]));
  };
  useEffect(() => {
    reload();
  }, []);
  return (
    <section className="page">
      <PageHeader module="资产中心 / 模型详情" title="同步历史" desc="按模型查看同步批次、写入数量、失败原因和操作人，支持审计追溯。" action={<Button onClick={reload}>刷新历史</Button>} />
      <div className="data-card">
        <Table
          dataSource={rows}
          columns={[
            { title: '批次 ID', dataIndex: 'event_id', width: 170, ellipsis: true },
            { title: '事件', dataIndex: 'event_type' },
            { title: '模型', dataIndex: 'model' },
            { title: '脚本', dataIndex: 'script' },
            { title: '版本', dataIndex: 'version', width: 90 },
            { title: '数量', dataIndex: 'count', width: 80 },
            { title: '失败', dataIndex: 'fail', width: 80 },
            { title: '操作人', dataIndex: 'producer', width: 120 },
            { title: '状态', dataIndex: 'status', width: 100, render: statusTag },
            { title: '时间', dataIndex: 'created_at', width: 190 }
          ]}
        />
      </div>
    </section>
  );
}

function AssetPermissionsAuditPage() {
  const [auditRows, setAuditRows] = useState<AuditLogRow[]>([]);
  useEffect(() => {
    listAuditLogs()
      .then((data) => setAuditRows(data.items.map((item) => ({ ...item, key: item.id }))))
      .catch(() => setAuditRows([]));
  }, []);
  return (
    <section className="page">
      <PageHeader module="资产中心 / 模型详情" title="权限与审计" desc="模型级权限决定谁能看、改、同步和授权，所有高风险动作必须留下审计。" action={<Button>导出审计</Button>} />
      <SectionBlock title="资产中心权限矩阵">
        <Table
          pagination={false}
          dataSource={apiRoles.map((role) => ({
            key: role,
            role,
            actions: localPermissionMatrix.assetCenter[role as Role]?.join(' / ') || 'none',
            scope: role === 'PlatformAdmin' ? '全局' : role === 'OpsAdmin' ? '业务线' : '授权模型'
          }))}
          columns={[
            { title: '角色', dataIndex: 'role', width: 150 },
            { title: '动作', dataIndex: 'actions' },
            { title: '数据范围', dataIndex: 'scope', width: 150 }
          ]}
        />
      </SectionBlock>
      <SectionBlock title="最近审计">
        <Table
          dataSource={auditRows}
          columns={[
            { title: '时间', dataIndex: 'created_at', width: 190 },
            { title: '操作者', dataIndex: 'actor', width: 120 },
            { title: '动作', dataIndex: 'action', width: 140 },
            { title: '对象', dataIndex: 'object' },
            { title: '结果', dataIndex: 'result', width: 100, render: statusTag }
          ]}
        />
      </SectionBlock>
    </section>
  );
}

function PolicyDetailPage() {
  const [strategy, setStrategy] = useState<ApiMonitoringStrategy | null>(null);
  const [requestedStrategyId, setRequestedStrategyId] = useState('');
  useEffect(() => {
    const strategyId = getHashEntityId('policies');
    setRequestedStrategyId(strategyId);
    listMonitoringStrategies()
      .then((data) => setStrategy(data.items.find((item) => item.id === strategyId) ?? null))
      .catch(() => setStrategy(null));
  }, []);
  const sourceLabel = strategy?.source_workorder_id ? `工单 ${strategy.source_workorder_id}` : '手动创建';
  const protocol = strategy?.protocol ?? (strategy?.rule?.signal?.metric === 'certificate_expire_days' ? 'CERTIFICATE' : 'HTTP');
  const condition = strategy?.rule?.condition;
  const conditionValue = Array.isArray(condition?.value) ? condition.value.join(', ') : String(condition?.value ?? '-');
  return (
    <section className="page policy-page">
      <div className="policy-detail-page">
        <div className="policy-detail-head">
          <div className="detail-title-group">
            <Button type="text" icon={<LeftOutlined />} onClick={() => goDetailBack('policy', 'policies')}>返回</Button>
            <div>
              <strong>{strategy?.name ?? '未找到策略'}</strong>
              <span>{strategy?.scope ?? (requestedStrategyId || '未知策略 ID')}</span>
            </div>
          </div>
          {strategy && <Space>
            {strategy && <Button onClick={() => createMonitoringStrategy({ name: `${strategy.name} 副本`, scope: strategy.scope, enabled: false, rule: strategy.rule }).then(() => { window.location.hash = 'policies'; })}>复制策略</Button>}
            {strategy && (
              <Popconfirm title="删除策略" description="删除后该策略不会继续下发。" okText="删除" cancelText="取消" onConfirm={() => deleteMonitoringStrategy(strategy.id).then(() => { window.location.hash = 'policies'; })}>
                <Button danger>删除</Button>
              </Popconfirm>
            )}
            <Button type="primary">编辑规则</Button>
          </Space>}
        </div>
        {strategy ? (
          <div className="policy-detail-layout">
            <main className="policy-detail-main">
              <section className="policy-section">
                <h3>策略信息</h3>
                <div className="alert-overview-grid">
                  <div className="alert-kv"><span>策略 ID</span><strong className="alert-uuid">{strategy.id}</strong></div>
                  <div className="alert-kv"><span>状态</span><strong>{statusTag(strategy.enabled ? '已启用' : '已停用')}</strong></div>
                  <div className="alert-kv"><span>作用对象</span><strong>{strategy.scope}</strong></div>
                  <div className="alert-kv"><span>告警等级</span><strong>{statusTag(strategy.severity ?? '严重')}</strong></div>
                  <div className="alert-kv"><span>协议</span><strong>{protocol}</strong></div>
                  <div className="alert-kv"><span>版本</span><strong>{strategy.version}</strong></div>
                  <div className="alert-kv"><span>来源</span><strong>{sourceLabel}</strong></div>
                  <div className="alert-kv"><span>更新时间</span><strong>{strategy.updated_at ?? '-'}</strong></div>
                  <div className="alert-kv alert-kv-wide"><span>探针</span><strong>{strategy.probes?.join('、') ?? '上海探针'}</strong></div>
                  <div className="alert-kv alert-kv-wide"><span>通知方式</span><strong>{strategy.notify_channels?.join('、') ?? '站内信'}</strong></div>
                </div>
              </section>
              <section className="policy-section">
                <h3>判定规则</h3>
                <div className="policy-rule-grid">
                  <div><span>检测指标</span><strong>{strategy.rule?.signal?.metric ?? '-'}</strong></div>
                  <div><span>判定方式</span><strong>{condition?.operator ?? '-'}</strong></div>
                  <div><span>判定值</span><strong>{conditionValue}</strong></div>
                  <div><span>触发次数</span><strong>连续 {condition?.consecutive ?? 1} 次</strong></div>
                </div>
                <details className="detail-raw-block">
                  <summary>查看规则 DSL</summary>
                  <Input.TextArea className="mono-textarea" rows={10} readOnly value={JSON.stringify(strategy.rule, null, 2)} />
                </details>
              </section>
            </main>
            <aside className="policy-detail-side">
              <h3>下发状态</h3>
              <Steps direction="vertical" current={strategy.enabled ? 3 : 1} items={[
                { title: '保存策略', description: strategy.updated_at ?? '-' },
                { title: 'DSL 校验', description: '已通过' },
                { title: '探针下发', description: strategy.enabled ? '已确认' : '未启用' },
                { title: '进入监控', description: strategy.enabled ? '运行中' : '已停用' }
              ]} />
            </aside>
          </div>
        ) : (
          <div className="empty-detail-state">
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={`未找到策略 ${requestedStrategyId || ''}`} />
          </div>
        )}
      </div>
    </section>
  );
}

function PolicyRuleConfigPage() {
  const [sampleCode, setSampleCode] = useState('500');
  const sampleValue = Number(sampleCode);
  const preview = previewAlertRule(httpAvailabilityRule, { http_status: Number.isFinite(sampleValue) ? sampleValue : sampleCode });
  const validation = validateAlertRuleDsl(httpAvailabilityRule);
  return (
    <section className="page">
      <PageHeader module="监控与告警 / 监控策略" title="规则配置" desc="规则配置页把 DSL、样本试算、升级动作和恢复条件放在同一工作台里。" action={<Space><Button>试算</Button><Button type="primary">保存规则</Button></Space>} />
      <div className="detail-shell">
        <div className="detail-main">
          <SectionBlock title="DSL 编辑器">
            <Input.TextArea className="mono-textarea" rows={14} readOnly value={JSON.stringify(httpAvailabilityRule, null, 2)} />
          </SectionBlock>
          <SectionBlock title="样本试算">
            <div className="form-grid">
              <LabeledInput label="http_status" value={sampleCode} onChange={(event) => setSampleCode(event.target.value)} />
              <Tag color={validation.valid ? 'green' : 'red'}>{validation.valid ? 'DSL 校验通过' : 'DSL 校验失败'}</Tag>
              <Tag color={preview.triggered ? 'orange' : 'green'}>{preview.triggered ? '触发告警' : '未触发'}</Tag>
            </div>
          </SectionBlock>
        </div>
        <div className="detail-side">
          <SectionBlock title="升级动作">
            <Timeline items={[
              { color: 'blue', children: '连续 3 次失败生成事件' },
              { color: 'orange', children: 'P1 15 分钟未处理升级 P0' },
              { color: 'green', children: '连续 2 次成功自动恢复' }
            ]} />
          </SectionBlock>
        </div>
      </div>
    </section>
  );
}

function ProbeDetailPage() {
  const [probe, setProbe] = useState<ApiProbeNode | null>(null);
  const [configVersions, setConfigVersions] = useState<ApiProbeConfigVersion[]>([]);
  const [probeTasks, setProbeTasks] = useState<ApiDetectionTask[]>([]);
  const [runtime, setRuntime] = useState<ApiProbeRuntimePayload | null>(null);
  const [metricPoints, setMetricPoints] = useState<ApiProbeMetricsHistoryPoint[]>([]);
  const [requestedProbeId, setRequestedProbeId] = useState('');
  const loadProbeTasks = (node: ApiProbeNode) => {
    listDetectionTasks()
      .then((data) => {
        const items = data.items ?? [];
        setProbeTasks(items.filter((item) => item.probe === node.name || item.probe === node.id || item.claimed_by_probe_id === node.id || item.metadata?.selected_probe === node.name).slice(0, 8));
      })
      .catch(() => setProbeTasks([]));
  };
  const loadProbe = (id: string) => {
    listProbeNodes()
      .then((data) => {
        const found = data.items.find((item) => item.id === id) ?? null;
        setProbe(found);
        if (!found) {
          setConfigVersions([]);
          setProbeTasks([]);
          setRuntime(null);
          setMetricPoints([]);
          return;
        }
        loadProbeTasks(found);
        getProbeRuntime(id)
          .then(setRuntime)
          .catch(() => setRuntime(null));
        listProbeMetricsHistory(id, { hours: 6, interval_minutes: 60 })
          .then((history) => setMetricPoints(history.points ?? []))
          .catch(() => setMetricPoints([]));
        listProbeConfigVersions(id)
          .then((versionData) => setConfigVersions(versionData.items ?? []))
          .catch(() => setConfigVersions([]));
      })
      .catch(() => {
        setProbe(null);
        setConfigVersions([]);
        setProbeTasks([]);
        setRuntime(null);
        setMetricPoints([]);
      });
  };
  useEffect(() => {
    const probeId = getHashEntityId('probes');
    setRequestedProbeId(probeId);
    loadProbe(probeId);
  }, []);
  const syncProbeConfig = () => {
    if (!probe) return;
    refreshProbeConfig(probe.id).then((updated) => {
      setProbe(updated);
      listProbeConfigVersions(updated.id).then((data) => setConfigVersions(data.items ?? []));
    });
  };
  const retireCurrentProbe = () => {
    if (!probe) return;
    retireProbeNode(probe.id).then(setProbe);
  };
  const rollbackConfigVersion = (version: number) => {
    if (!probe) return;
    rollbackProbeConfig(probe.id, version).then((updated) => {
      setProbe(updated);
      listProbeConfigVersions(updated.id).then((data) => setConfigVersions(data.items ?? []));
    });
  };
  const claimCurrentProbeTasks = () => {
    if (!probe) return;
    claimProbeTasks({ probe_id: probe.id, limit: 1 }).then(() => loadProbe(probe.id));
  };
  const reportProbeTask = (taskId: string, status: 'success' | 'failed') => {
    if (!probe) return;
    submitProbeTaskResult(taskId, {
      probe_id: probe.id,
      status,
      response_time_ms: status === 'success' ? probe.avg_latency_ms ?? 80 : 5000,
      status_code: status === 'success' ? '200' : '504',
      message: status === 'success' ? '探针回传成功' : '探针回传失败'
    }).then(() => loadProbe(probe.id));
  };
  const recentTasks = probeTasks.map((task) => ({ ...task, key: task.id }));
  const metricRows = metricPoints.map((point) => ({ ...point, key: point.timestamp }));
  return (
    <section className="page alert-detail-page probe-detail-page">
      {probe ? (
        <section className="alert-detail-shell">
          <div className="alert-detail-head">
            <div className="detail-title-group">
              <Button type="text" icon={<LeftOutlined />} onClick={() => goDetailBack('probe', 'probes')}>返回</Button>
              <div>
                <strong>{probe.name}</strong>
              </div>
            </div>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => loadProbe(probe.id)}>刷新</Button>
              <Button type="primary" icon={<CloudSyncOutlined />} onClick={syncProbeConfig}>同步配置</Button>
              {probe.status !== 'retired' && (
                <Popconfirm title="确认退役该探针？" onConfirm={retireCurrentProbe}>
                  <Button danger>退役</Button>
                </Popconfirm>
              )}
            </Space>
          </div>
          <div className="alert-detail-layout">
            <main className="alert-detail-main">
              <section className="alert-section">
                <h3>节点概览</h3>
                <div className="alert-overview-grid">
                  <div className="alert-kv"><span>节点 ID</span><strong>{probe.id}</strong></div>
                  <div className="alert-kv"><span>状态</span><strong>{statusTag(probeStatusLabel(probe.status))}</strong></div>
                  <div className="alert-kv"><span>区域</span><strong>{probe.region}</strong></div>
                  <div className="alert-kv"><span>网络类型</span><strong>{probe.network_type ?? '-'}</strong></div>
                  <div className="alert-kv"><span>IP 地址</span><strong>{probe.ip_address || '未上报'}</strong></div>
                  <div className="alert-kv"><span>最近心跳</span><strong>{probe.heartbeat_at ?? '-'}</strong></div>
                  <div className="alert-kv"><span>能力</span><strong>{probe.capabilities.join(' / ')}</strong></div>
                  <div className="alert-kv"><span>运行负载</span><strong>{runtime?.tasks.active ?? probe.active_tasks ?? 0} 任务 / 队列 {runtime?.tasks.queue_depth ?? probe.queue_depth ?? 0}</strong></div>
                  <div className="alert-kv"><span>成功率</span><strong>{probe.success_rate ?? '-'}%</strong></div>
                  <div className="alert-kv"><span>平均耗时</span><strong>{probe.avg_latency_ms ?? '-'}ms</strong></div>
                </div>
              </section>
              <section className="alert-section">
                <h3>资源快照</h3>
                <div className="alert-overview-grid">
                  <div className="alert-kv"><span>CPU</span><strong>{formatProbeMetric(runtime?.resource_metrics.cpu_usage ?? probe.cpu_usage, '%')}</strong></div>
                  <div className="alert-kv"><span>内存</span><strong>{formatProbeMemory(runtime?.resource_metrics.memory_usage_mb ?? probe.memory_usage_mb)} / {formatProbeMetric(runtime?.resource_metrics.memory_usage_pct ?? probe.memory_usage_pct, '%')}</strong></div>
                  <div className="alert-kv"><span>负载</span><strong>{formatProbeMetric(runtime?.resource_metrics.load_avg ?? probe.load_avg)}</strong></div>
                  <div className="alert-kv"><span>队列深度</span><strong>{runtime?.tasks.queue_depth ?? probe.queue_depth ?? 0}</strong></div>
                  <div className="alert-kv"><span>窗口执行</span><strong>{runtime?.tasks.executed ?? probe.executions ?? 0}</strong></div>
                  <div className="alert-kv"><span>失败次数</span><strong>{runtime?.tasks.failed ?? probe.failed ?? 0}</strong></div>
                </div>
              </section>
              <section className="alert-section">
                <h3>指标历史</h3>
                <Table
                  pagination={false}
                  size="middle"
                  tableLayout="fixed"
                  className="enterprise-fixed-table probe-metrics-table"
                  rowKey="timestamp"
                  dataSource={metricRows}
                  columns={[
                    { title: '时间', dataIndex: 'timestamp', width: 140, ellipsis: true, render: (value) => String(value || '-').slice(5, 16).replace('T', ' ') },
                    { title: 'CPU', dataIndex: 'cpu_usage', width: 110, render: (value) => `${value}%` },
                    { title: '内存', dataIndex: 'memory_usage_mb', width: 120, render: (value) => `${value}MB` },
                    { title: '队列', dataIndex: 'queue_depth', width: 100 },
                    { title: '活跃任务', dataIndex: 'active_workers', width: 120 },
                    { title: '执行数', dataIndex: 'tasks_executed', width: 120 },
                    { title: '心跳', dataIndex: 'heartbeats_sent', width: 100 }
                  ]}
                />
              </section>
              <section className="alert-section">
                <h3>接入与配置</h3>
                <div className="alert-overview-grid">
                  <div className="alert-kv"><span>接入地址</span><strong>{probe.gateway_url ?? '-'}</strong></div>
                  <div className="alert-kv"><span>Token</span><strong>{probe.bootstrap_token_hint ?? '-'}</strong></div>
                  <div className="alert-kv"><span>注册时间</span><strong>{probe.registered_at ?? '-'}</strong></div>
                  <div className="alert-kv"><span>配置同步</span><strong>{probe.last_config_sync_at ?? '-'}</strong></div>
                  <div className="alert-kv"><span>心跳周期</span><strong>{probe.agent_config?.heartbeat_interval_seconds ?? 30}s</strong></div>
                  <div className="alert-kv"><span>任务拉取</span><strong>{probe.agent_config?.task_poll_interval_seconds ?? 5}s</strong></div>
                  <div className="alert-kv"><span>并发上限</span><strong>{probe.agent_config?.max_concurrent_tasks ?? 8}</strong></div>
                  <div className="alert-kv"><span>传输协议</span><strong>{probe.agent_config?.transport ?? 'https-json'}</strong></div>
                </div>
              </section>
              <section className="alert-section">
                <h3>配置版本</h3>
                <Table
                  pagination={false}
                  size="middle"
                  tableLayout="fixed"
                  className="enterprise-fixed-table"
                  rowKey="id"
                  dataSource={configVersions}
                  columns={[
                    { title: '版本', dataIndex: 'version', width: 90, render: (value) => <strong>v{value}</strong> },
                    { title: '状态', dataIndex: 'status', width: 110, render: (value) => statusTag(probeConfigVersionLabel(value)) },
                    { title: '发布时间', dataIndex: 'published_at', ellipsis: true },
                    { title: '确认时间', dataIndex: 'acknowledged_at', ellipsis: true, render: (value) => value || '-' },
                    { title: '哈希', dataIndex: 'content_hash', width: 120, render: (value) => <Text code>{String(value || '-').slice(0, 10)}</Text> },
                    {
                      title: '操作',
                      width: 100,
                      render: (_, row) => {
                        const isCurrent = probeVersionNumberForView(probe.version) === row.version;
                        return isCurrent ? <Text type="secondary">当前</Text> : (
                          <Popconfirm title={`确认回滚到 v${row.version}？`} onConfirm={() => rollbackConfigVersion(row.version)}>
                            <Button type="link">回滚</Button>
                          </Popconfirm>
                        );
                      }
                    }
                  ]}
                />
              </section>
              <section className="alert-section">
                <div className="section-title-row">
                  <h3>最近任务</h3>
                  <Button size="small" onClick={claimCurrentProbeTasks}>领取任务</Button>
                </div>
                <Table
                  pagination={false}
                  size="middle"
                  tableLayout="fixed"
                  className="enterprise-fixed-table"
                  rowKey="id"
                  dataSource={recentTasks}
                  columns={[
                    {
                      title: '任务',
                      ellipsis: true,
                      render: (_, row) => (
                        <div className="record-target-cell">
                          <Tooltip title={row.target}><span>{row.target}</span></Tooltip>
                          <Text type="secondary">{row.id}</Text>
                        </div>
                      )
                    },
                    { title: '协议', dataIndex: 'protocol', width: 120, render: (value, row) => value || row.type.toUpperCase() },
                    { title: '状态', dataIndex: 'status', width: 110, render: (value) => statusTag(presentDetectionStatus(value)) },
                    { title: '耗时', dataIndex: 'latency_ms', width: 100, render: (value) => value ? `${value}ms` : '-' },
                    { title: '领取 / 完成', width: 180, render: (_, row) => row.completed_at ? row.completed_at.slice(5, 16).replace('T', ' ') : row.claimed_at ? row.claimed_at.slice(5, 16).replace('T', ' ') : row.created_at.slice(5, 16).replace('T', ' ') },
                    {
                      title: '操作',
                      width: 170,
                      render: (_, row) => row.status === 'running' ? (
                        <Space size={6}>
                          <Button type="link" onClick={() => reportProbeTask(row.id, 'success')}>回传成功</Button>
                          <Button type="link" danger onClick={() => reportProbeTask(row.id, 'failed')}>失败</Button>
                        </Space>
                      ) : <Text type="secondary">-</Text>
                    }
                  ]}
                />
              </section>
            </main>
            <aside className="alert-detail-side">
              <h3>运行状态</h3>
              <div className="probe-side-grid">
                <div><span>配置版本</span><strong>{probe.version ?? '-'}</strong></div>
                <div><span>配置状态</span><strong>{statusTag(probeConfigLabel(probe.config_status))}</strong></div>
                <div><span>连接状态</span><strong>{statusTag(probeConnectionLabel(probe.connection_status))}</strong></div>
                <div><span>运行时长</span><strong>{probe.uptime ?? '-'}</strong></div>
                <div><span>心跳延迟</span><strong>{runtime?.heartbeat_delay_seconds === null || runtime?.heartbeat_delay_seconds === undefined ? '-' : `${runtime.heartbeat_delay_seconds}s`}</strong></div>
              </div>
            </aside>
          </div>
        </section>
      ) : (
        <section className="alert-detail-shell">
          <div className="alert-detail-head">
            <div className="detail-title-group">
              <Button type="text" icon={<LeftOutlined />} onClick={() => goDetailBack('probe', 'probes')}>返回</Button>
              <div>
                <strong>未找到探针节点</strong>
                <span>{requestedProbeId || '未知探针 ID'}</span>
              </div>
            </div>
          </div>
          <div className="empty-detail-state">
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="该探针不存在或当前账号无权查看" />
          </div>
        </section>
      )}
    </section>
  );
}

function ExecutionLogDetailPage() {
  const [task, setTask] = useState<{ id: string; type: string; target: string; probe: string; status: string; related_asset: string; created_at: string } | null>(null);
  const [requestedTaskId, setRequestedTaskId] = useState('');
  useEffect(() => {
    const taskId = getHashEntityId('execution-logs');
    setRequestedTaskId(taskId);
    listDetectionTasks()
      .then((data) => setTask(data.items.find((item) => item.id === taskId) ?? null))
      .catch(() => setTask(null));
  }, []);
  if (!task) {
    return (
      <section className="page alert-detail-page">
        <section className="alert-detail-shell">
          <div className="alert-detail-head">
            <div className="detail-title-group">
              <Button type="text" icon={<LeftOutlined />} onClick={() => goDetailBack('execution-log', 'detection-records')}>返回</Button>
              <div>
                <strong>未找到检测记录</strong>
                <span>{requestedTaskId || '未知记录 ID'}</span>
              </div>
            </div>
          </div>
          <div className="empty-detail-state">
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="该检测记录不存在或当前账号无权查看" />
          </div>
        </section>
      </section>
    );
  }
  return (
    <section className="page">
      <PageHeader module="监控与告警 / 执行日志" title={`执行日志详情 ${task.id}`} desc="日志详情用于排查探针执行、输入参数、结果证据、失败原因和关联对象。" action={<Button type="text" icon={<LeftOutlined />} onClick={() => goDetailBack('execution-log', 'detection-records')}>返回</Button>} />
      <div className="detail-shell">
        <div className="detail-main">
          <SectionBlock title="执行摘要">
            <Descriptions bordered size="small" column={3}>
              <Descriptions.Item label="任务类型">{task?.type ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="目标">{task?.target ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="探针">{task?.probe ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="状态">{statusTag(task?.status === 'success' ? '成功' : task?.status === 'failed' ? '失败' : '待执行')}</Descriptions.Item>
              <Descriptions.Item label="关联资产">{task?.related_asset ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{task?.created_at ?? '-'}</Descriptions.Item>
            </Descriptions>
          </SectionBlock>
          <SectionBlock title="执行证据">
            <Input.TextArea className="mono-textarea" rows={12} readOnly value={JSON.stringify({
              request: { target: task?.target ?? 'https://api.oneall.internal/health', method: 'GET' },
              response: { status: task?.status ?? 'pending', latency_ms: null },
              probe: task?.probe ?? 'probe-sh-01',
              trace_id: task?.id ?? 'DET-demo'
            }, null, 2)} />
          </SectionBlock>
        </div>
        <div className="detail-side">
          <SectionBlock title="后续动作">
            <Space direction="vertical" className="full-width">
              <Button block>转监控策略</Button>
              <Button block>创建工单</Button>
              <Button block>关联资产</Button>
            </Space>
          </SectionBlock>
        </div>
      </div>
    </section>
  );
}

function WorkordersPage(props: { currentRole: ApiRole; mode: 'create' | 'mine' | 'approval' }) {
  const { message: messageApi } = AntApp.useApp();
  const [rows, setRows] = useState<WorkorderRow[]>(workorders);
  const [rejectTarget, setRejectTarget] = useState<WorkorderRow | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [editingDraftId, setEditingDraftId] = useState<string>();
  const [editingSourceStatus, setEditingSourceStatus] = useState<WorkorderStatus>();
  const [target, setTarget] = useState(monitoringRequestDefaults.target);
  const [systemName, setSystemName] = useState(monitoringRequestDefaults.systemName);
  const [networkType, setNetworkType] = useState(monitoringRequestDefaults.networkType);
  const [owner, setOwner] = useState(monitoringRequestDefaults.owner);
  const [alertContacts, setAlertContacts] = useState(monitoringRequestDefaults.alertContacts);
  const [protocol, setProtocol] = useState(monitoringRequestDefaults.protocol);
  const [frequencyValue, setFrequencyValue] = useState(1);
  const [frequencyUnit, setFrequencyUnit] = useState('分钟');
  const [probes, setProbes] = useState<string[]>(['probe-sh-01']);
  const [triggerMode, setTriggerMode] = useState('consecutive');
  const [failureCount, setFailureCount] = useState(3);
  const [windowCount, setWindowCount] = useState(5);
  const [expectedStatusCodes, setExpectedStatusCodes] = useState('200,204');
  const [timeoutSeconds, setTimeoutSeconds] = useState(5);
  const [alertSeverity, setAlertSeverity] = useState('严重');
  const [recoverySuccessCount, setRecoverySuccessCount] = useState(2);
  const [listKeyword, setListKeyword] = useState('');
  const [protocolFilter, setProtocolFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<string>(props.mode === 'approval' ? 'submitted' : 'all');
  const [listPage, setListPage] = useState(1);
  const [listPageSize, setListPageSize] = useState(10);
  const listMinTableWidth = props.mode === 'approval' ? 1180 : 1140;
  const tableWidth = useTableContainerWidth('.workorder-list-table-region', listMinTableWidth);
  const canManageWorkorders = hasPermission(props.currentRole, 'workorders', 'manage');
  const canCreateWorkorder = canManageWorkorders || hasPermission(props.currentRole, 'workorders', 'create');
  const canApproveWorkorder = canManageWorkorders || hasPermission(props.currentRole, 'workorders', 'approve');
  const canExecuteWorkorder = canManageWorkorders || hasPermission(props.currentRole, 'workorders', 'execute');
  const roleView = canManageWorkorders ? '管理员' : canApproveWorkorder ? '审批人' : '申请人';
  const reload = () => {
    listWorkorderRequests()
      .then((data) => setRows(data.items.map((item) => ({ ...item, key: item.id, status: item.status as WorkorderStatus }))))
      .catch(() => setRows(workorders));
  };
  useEffect(() => {
    reload();
  }, []);
  useEffect(() => {
    if (props.mode !== 'create') return;
    const editId = window.sessionStorage.getItem('oneall.editingWorkorderDraft');
    if (!editId) {
      setEditingDraftId(undefined);
      setEditingSourceStatus(undefined);
      return;
    }
    listWorkorderRequests().then((data) => {
      const draft = data.items.find((item) => item.id === editId && ['draft', 'rejected', 'withdrawn', 'failed'].includes(item.status));
      if (!draft?.request_data) return;
      const form = draft.request_data;
      setEditingDraftId(draft.id);
      setEditingSourceStatus(draft.status as WorkorderStatus);
      setTarget(form.target);
      setSystemName(form.systemName);
      setNetworkType(form.networkType);
      setOwner(form.owner);
      setAlertContacts(form.alertContacts);
      setProtocol(form.protocol);
      setFrequencyValue(form.frequencyValue);
      setFrequencyUnit(form.frequencyUnit);
      setProbes(form.probes);
      setTriggerMode(form.triggerMode);
      setFailureCount(form.failureCount);
      setWindowCount(form.windowCount ?? 5);
      setExpectedStatusCodes(form.expectedStatusCodes);
      setTimeoutSeconds(form.timeoutSeconds);
      setAlertSeverity(form.alertSeverity);
      setRecoverySuccessCount(form.recoverySuccessCount);
    });
  }, [props.mode]);
  useEffect(() => {
    setListPage(1);
  }, [props.mode, listKeyword, protocolFilter, statusFilter]);
  const monitoringRows = rows
    .filter((row) => row.type === '拨测监控申请' || row.type === '监控申请')
  const filterListRows = (source: WorkorderRow[]) => source.filter((row) => {
    const request = buildMonitoringRequest(row);
    const keyword = listKeyword.trim().toLowerCase();
    const matchedKeyword = !keyword || [
      row.id,
      row.title,
      row.applicant,
      request.target,
      request.systemName
    ].some((value) => value.toLowerCase().includes(keyword));
    const matchedProtocol = protocolFilter === 'all' || request.protocol === protocolFilter;
    const matchedStatus = statusFilter === 'all' || row.status === statusFilter;
    return matchedKeyword && matchedProtocol && matchedStatus;
  });
  const myRows = filterListRows(monitoringRows.filter((row) => canManageWorkorders || row.applicant === props.currentRole));
  const approvalFilteredRows = filterListRows(monitoringRows.filter((row) => row.status !== 'draft'));
  const statusOptions = [
    { label: '全部', value: 'all' },
    ...(props.mode === 'mine' ? [{ label: '草稿', value: 'draft' }] : []),
    { label: '待审批', value: 'submitted' },
    { label: '待执行', value: 'approved' },
    { label: '执行中', value: 'executing' },
    { label: '已完成', value: 'completed' },
    { label: '已驳回', value: 'rejected' },
    ...(props.mode === 'mine' ? [{ label: '已撤回', value: 'withdrawn' }] : []),
    { label: '执行失败', value: 'failed' },
    { label: '已取消', value: 'canceled' }
  ];
  const approvalDemoRow: WorkorderRow = {
    key: 'approval-demo',
    id: 'WO-demo-approval',
    type: '拨测监控申请',
    title: '新增 demo.oneall.internal HTTP 监控',
    applicant: 'OpsEngineer',
    assignee: props.currentRole,
    status: 'submitted',
    sla: '4h',
    related_object: 'demo.oneall.internal',
    request_data: {
      target: 'demo.oneall.internal',
      systemName: '支付业务',
      networkType: '互联网',
      owner: 'OpsEngineer',
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
  };
  const shouldShowApprovalDemo = statusFilter === 'submitted' && !listKeyword.trim() && protocolFilter === 'all';
  const approvalRows = canApproveWorkorder
    ? (approvalFilteredRows.length ? approvalFilteredRows : shouldShowApprovalDemo ? filterListRows([approvalDemoRow]) : [])
    : [];
  const isDemoWorkorder = (row: WorkorderRow) => row.id === approvalDemoRow.id;
  const approveRequest = (row: WorkorderRow) => {
    approveWorkorder(row.id).then(() => {
      messageApi.success(`已审批通过 ${row.id}，等待执行人下发策略`);
      reload();
    }).catch((error: Error) => {
      messageApi.error(error.message);
      reload();
    });
  };
  const rejectRequest = (row: WorkorderRow, reason: string) => {
    rejectWorkorder(row.id, reason).then(() => {
      messageApi.success(`已驳回 ${row.id}`);
      reload();
      setRejectTarget(null);
      setRejectReason('');
    });
  };
  const openRejectDialog = (row: WorkorderRow) => {
    setRejectTarget(row);
    setRejectReason('');
  };
  const withdrawRequest = (row: WorkorderRow) => {
    withdrawWorkorder(row.id).then(() => {
      messageApi.success(`已撤回 ${row.id}`);
      reload();
    });
  };
  const buildMonitoringRequestInput = (status?: WorkorderStatus) => ({
      type: '拨测监控申请',
      title: `${protocol} 拨测 ${target.trim()}`,
      related_object: target.trim(),
      status,
      request_data: {
        target: target.trim(),
        systemName: systemName.trim(),
        networkType,
        owner: owner.trim(),
        alertContacts: alertContacts.trim(),
        protocol,
        frequencyValue,
        frequencyUnit,
        probes,
        triggerMode,
        failureCount,
        windowCount: triggerMode === 'window' ? windowCount : undefined,
        expectedStatusCodes: expectedStatusCodes.trim(),
        timeoutSeconds,
        alertSeverity,
        recoverySuccessCount
      }
  });
  const validateMonitoringRequestForm = (mode: 'draft' | 'submit') => {
    const trimmedTarget = target.trim();
    const targetPattern = /^(https?:\/\/)?[a-z0-9.-]+\.[a-z]{2,}(?::\d+)?(\/.*)?$/i;
    if (trimmedTarget && !targetPattern.test(trimmedTarget)) {
      messageApi.warning('目标地址格式不正确，请填写域名或 URL');
      return false;
    }
    if (mode === 'draft') return true;

    if (!trimmedTarget) {
      messageApi.warning('请填写目标地址');
      return false;
    }
    if (!systemName.trim()) {
      messageApi.warning('请填写所属系统');
      return false;
    }
    if (!owner.trim()) {
      messageApi.warning('请填写负责人');
      return false;
    }
    if (!alertContacts.trim()) {
      messageApi.warning('请填写告警联系人');
      return false;
    }
    if (!probes.length) {
      messageApi.warning('请至少选择一个探针');
      return false;
    }
    if (frequencyValue < 1) {
      messageApi.warning('频率必须大于 0');
      return false;
    }
    if (failureCount < 1 || timeoutSeconds < 1 || recoverySuccessCount < 1) {
      messageApi.warning('告警规则中的次数和超时时间必须大于 0');
      return false;
    }
    if (protocol === 'HTTP') {
      const codes = expectedStatusCodes.split(',').map((item) => Number(item.trim())).filter((item) => Number.isFinite(item));
      const hasInvalidCode = !codes.length || codes.some((code) => code < 100 || code > 599);
      if (hasInvalidCode) {
        messageApi.warning('期望状态码必须是 100-599 之间的数字，多个用逗号分隔');
        return false;
      }
    }
    return true;
  };
  const saveMonitoringDraft = () => {
    if (!validateMonitoringRequestForm('draft')) return;
    const action = editingDraftId
      ? updateWorkorderRequest(editingDraftId, buildMonitoringRequestInput('draft'))
      : createWorkorderRequest(buildMonitoringRequestInput('draft'));
    action.then(() => {
      messageApi.success('草稿已保存');
      reload();
    });
  };
  const submitMonitoringRequest = () => {
    if (!validateMonitoringRequestForm('submit')) return;
    const input = { ...buildMonitoringRequestInput(), status: 'submitted' };
    const action = editingDraftId
      ? updateWorkorderRequest(editingDraftId, input)
      : createWorkorderRequest({ ...input, status: undefined });
    action.then(() => {
      messageApi.success('申请已提交');
      if (editingDraftId) {
        window.sessionStorage.removeItem('oneall.editingWorkorderDraft');
        setEditingDraftId(undefined);
        setEditingSourceStatus(undefined);
      }
      reload();
    });
  };
  const editWorkorderRequest = (row: WorkorderRow) => {
    window.sessionStorage.setItem('oneall.editingWorkorderDraft', row.id);
    window.location.hash = 'workorder-new';
  };
  const deleteDraft = (row: WorkorderRow) => {
    deleteWorkorderRequest(row.id).then(() => {
      messageApi.success(`已删除草稿 ${row.id}`);
      reload();
    });
  };
  const showWorkorderDetail = (id: string) => {
    rememberDetailReturn('workorder', props.mode === 'approval' ? 'approvals' : 'workorders');
    window.location.hash = `workorders/${encodeURIComponent(id)}`;
  };
  const renderWorkorderActions = (row: WorkorderRow) => {
    if (props.mode === 'approval') {
      const isDemo = isDemoWorkorder(row);
      const canAct = canApproveWorkorder && canTransitionWorkorder(row.status, 'approved') && canTransitionWorkorder(row.status, 'rejected') && !isDemo;
      return (
        <Space>
          <Popconfirm
            title="确认审批通过"
            description="审批通过后进入待执行，由执行人下发监控策略。"
            okText="通过审批"
            cancelText="取消"
            disabled={!canAct}
            onConfirm={() => approveRequest(row)}
          >
            <Button type="link" disabled={!canAct}>通过</Button>
          </Popconfirm>
          <Button type="link" danger disabled={!canAct} onClick={() => openRejectDialog(row)}>驳回</Button>
          <Button type="link" onClick={() => showWorkorderDetail(row.id)}>详情</Button>
        </Space>
      );
    }

    return (
      <Space>
        {props.mode === 'mine' && row.status === 'draft' && <Button type="link" onClick={() => editWorkorderRequest(row)}>编辑</Button>}
        {props.mode === 'mine' && ['rejected', 'withdrawn', 'failed'].includes(row.status) && <Button type="link" onClick={() => editWorkorderRequest(row)}>重新提交</Button>}
        {props.mode === 'mine' && row.status === 'submitted' && canTransitionWorkorder(row.status, 'withdrawn') && (
          <Popconfirm title="撤回申请" description="撤回后该申请不会继续进入审批。" okText="确认撤回" cancelText="取消" onConfirm={() => withdrawRequest(row)}>
            <Button type="link">撤回</Button>
          </Popconfirm>
        )}
        {props.mode === 'mine' && row.status === 'draft' && (
          <Popconfirm title="删除草稿" description="删除后不可恢复。" okText="删除" cancelText="取消" onConfirm={() => deleteDraft(row)}>
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        )}
        <Button type="link" onClick={() => showWorkorderDetail(row.id)}>详情</Button>
      </Space>
    );
  };
  const requestColumns: ColumnsType<WorkorderRow> = [
    { title: '申请编号', dataIndex: 'id', width: 150, ellipsis: true },
    { title: '目标地址', ellipsis: true, render: (_, row) => buildMonitoringRequest(row).target },
    { title: '所属系统', width: 130, ellipsis: true, render: (_, row) => buildMonitoringRequest(row).systemName },
    { title: '网络类型', width: 100, render: (_, row) => buildMonitoringRequest(row).networkType },
    { title: '协议', width: 82, render: (_, row) => buildMonitoringRequest(row).protocol },
    { title: '频率', width: 86, render: (_, row) => buildMonitoringRequest(row).frequency },
    { title: '状态', dataIndex: 'status', width: 96, render: (status: WorkorderStatus) => statusTag(workorderStatusLabel[status]) },
    { title: '操作', width: props.mode === 'approval' ? 150 : 180, fixed: 'right', render: (_, row) => renderWorkorderActions(row) }
  ];
  const approvalColumns: ColumnsType<WorkorderRow> = [
    { title: '申请编号', dataIndex: 'id', width: 150, ellipsis: true },
    { title: '申请人', dataIndex: 'applicant', width: 100 },
    { title: '目标地址', ellipsis: true, render: (_, row) => buildMonitoringRequest(row).target },
    { title: '所属系统', width: 130, ellipsis: true, render: (_, row) => buildMonitoringRequest(row).systemName },
    { title: '协议', width: 82, render: (_, row) => buildMonitoringRequest(row).protocol },
    { title: '告警规则', width: 280, ellipsis: true, render: (_, row) => buildMonitoringRequest(row).alertThreshold },
    { title: '操作', width: 150, fixed: 'right', render: (_, row) => renderWorkorderActions(row) }
  ];
  const renderRequestTable = (dataSource: WorkorderRow[], columns: ColumnsType<WorkorderRow>) => {
    const pageCount = Math.max(1, Math.ceil(dataSource.length / listPageSize));
    const safePage = Math.min(listPage, pageCount);
    const currentRows = dataSource.slice((safePage - 1) * listPageSize, safePage * listPageSize);

    return (
      <div className="workorder-list-layout">
        <div className="workorder-list-table-region">
          <Table
            className="workorder-list-table"
            size="middle"
            dataSource={currentRows}
            pagination={false}
            tableLayout="fixed"
            scroll={{ x: tableWidth }}
            columns={columns}
          />
        </div>
        <div className="workorder-list-pagination">
          <Pagination
            current={safePage}
            total={dataSource.length}
            pageSize={listPageSize}
            showSizeChanger
            showTotal={(total) => `共 ${total} 条`}
            onChange={(page, pageSize) => {
              setListPage(page);
              setListPageSize(pageSize);
            }}
          />
        </div>
      </div>
    );
  };
  const requestForm = (
    <section className="monitoring-request-form-page">
      <div className="request-form-toolbar">
        <div>
          <strong>{editingDraftId ? editingSourceStatus === 'draft' ? '编辑拨测监控草稿' : '重新提交拨测监控申请' : '拨测监控申请'}</strong>
          <span>{editingDraftId ? `当前工单 ${editingDraftId} · ${workorderStatusLabel[editingSourceStatus ?? 'draft']}` : '提交后进入审批，通过后下发监控策略。'}</span>
        </div>
        <Space className="request-form-actions">
          <Button disabled={!canCreateWorkorder} onClick={saveMonitoringDraft}>保存草稿</Button>
          <Button className="request-submit-button" type="primary" disabled={!canCreateWorkorder} onClick={submitMonitoringRequest}>提交申请</Button>
        </Space>
      </div>
      <div className="request-form-body">
        <div className="request-form-sections">
          <section>
            <h3>基础信息</h3>
            <div className="request-form-grid">
              <div className="request-field"><label>目标地址</label><Input value={target} onChange={(event) => setTarget(event.target.value)} /></div>
              <div className="request-field"><label>所属系统</label><Input value={systemName} onChange={(event) => setSystemName(event.target.value)} /></div>
              <div className="request-field"><label>网络类型</label><Select value={networkType} onChange={setNetworkType} options={[{ label: '互联网', value: '互联网' }, { label: '内网', value: '内网' }]} /></div>
              <div className="request-field"><label>负责人</label><Input value={owner} onChange={(event) => setOwner(event.target.value)} /></div>
              <div className="request-field"><label>告警联系人</label><Input value={alertContacts} onChange={(event) => setAlertContacts(event.target.value)} /></div>
            </div>
          </section>
          <section>
            <h3>拨测配置</h3>
            <div className="request-form-grid">
              <div className="request-field">
                <label>协议</label>
                <Select
                  value={protocol}
                  onChange={(value) => {
                    setProtocol(value);
                    setFrequencyValue(1);
                    setFrequencyUnit(value === 'CERTIFICATE' ? '天' : '分钟');
                  }}
                  options={[{ label: 'HTTP', value: 'HTTP' }, { label: 'TCP', value: 'TCP' }, { label: 'CERTIFICATE', value: 'CERTIFICATE' }]}
                />
              </div>
              <div className="request-field">
                <label>频率</label>
                <div className="request-number-unit request-number-unit-select">
                  <InputNumber min={1} max={1440} value={frequencyValue} onChange={(value) => setFrequencyValue(value ?? 1)} />
                  <Select value={frequencyUnit} onChange={setFrequencyUnit} options={[{ label: '秒', value: '秒' }, { label: '分钟', value: '分钟' }, { label: '小时', value: '小时' }, { label: '天', value: '天' }]} />
                </div>
              </div>
              <div className="request-field request-field-wide">
                <label>探针</label>
                <Select
                  mode="multiple"
                  value={probes}
                  onChange={setProbes}
                  options={[
                    { label: '上海探针', value: 'probe-sh-01' },
                    { label: '北京探针', value: 'probe-bj-01' },
                    { label: '广州探针', value: 'probe-gz-01' }
                  ]}
                />
              </div>
            </div>
          </section>
          <section>
            <h3>告警规则</h3>
            <div className="request-form-grid">
              <div className="request-field">
                <label>触发方式</label>
                <Select
                  value={triggerMode}
                  onChange={setTriggerMode}
                  options={[
                    { label: '连续失败', value: 'consecutive' },
                    { label: '最近 N 次失败', value: 'window' }
                  ]}
                />
              </div>
              <div className="request-field">
                <label>失败次数</label>
                <div className="request-number-unit">
                  <InputNumber min={1} max={20} value={failureCount} onChange={(value) => setFailureCount(value ?? 1)} />
                  <span className="request-unit-label">次</span>
                </div>
              </div>
              {triggerMode === 'window' && (
                <div className="request-field">
                  <label>统计窗口</label>
                  <div className="request-number-unit">
                    <InputNumber min={1} max={50} value={windowCount} onChange={(value) => setWindowCount(value ?? 1)} />
                    <span className="request-unit-label">次检测</span>
                  </div>
                </div>
              )}
              <div className="request-field">
                <label>期望状态码</label>
                <Input value={expectedStatusCodes} onChange={(event) => setExpectedStatusCodes(event.target.value)} placeholder="200,204,301,302" disabled={protocol !== 'HTTP'} />
              </div>
              <div className="request-field">
                <label>超时时间</label>
                <div className="request-number-unit">
                  <InputNumber min={1} max={120} value={timeoutSeconds} onChange={(value) => setTimeoutSeconds(value ?? 1)} />
                  <span className="request-unit-label">秒</span>
                </div>
              </div>
              <div className="request-field">
                <label>告警等级</label>
                <Select value={alertSeverity} onChange={setAlertSeverity} options={[{ label: '预警', value: '预警' }, { label: '严重', value: '严重' }, { label: '致命', value: '致命' }]} />
              </div>
              <div className="request-field">
                <label>恢复条件</label>
                <div className="request-number-unit">
                  <InputNumber min={1} max={20} value={recoverySuccessCount} onChange={(value) => setRecoverySuccessCount(value ?? 1)} />
                  <span className="request-unit-label">次连续成功</span>
                </div>
              </div>
            </div>
          </section>
        </div>
        <aside className="request-approval-panel">
          <h3>审批信息</h3>
          <div className="request-approval-flow">
            <div className="request-approval-step is-current">
              <span>申请人</span>
              <strong>{props.currentRole}</strong>
            </div>
            <div className="request-approval-step">
              <span>审批人</span>
              <strong>Approver</strong>
            </div>
            <div className="request-approval-step">
              <span>执行人</span>
              <strong>OpsAdmin</strong>
            </div>
          </div>
          <div className="request-approval-rule">
            <span>生效方式</span>
            <strong>审批通过后下发策略</strong>
          </div>
        </aside>
      </div>
    </section>
  );

  return (
    <section className={`page workorder-page ${props.mode === 'create' ? 'workorder-create-page' : ''}`}>
      <section className={`workorder-page-shell ${props.mode === 'create' ? 'workorder-create-shell' : ''}`}>
        {props.mode !== 'create' && <div className="workorder-role-bar">
          <Space>
            <Text type="secondary">当前视角</Text>
            <Tag color={roleView === '管理员' ? 'blue' : roleView === '审批人' ? 'orange' : 'green'}>{roleView}</Tag>
          </Space>
          <Space>
            <Input prefix={<SearchOutlined />} placeholder="搜索申请编号、目标地址、所属系统" value={listKeyword} onChange={(event) => setListKeyword(event.target.value)} allowClear />
            <Select className="workorder-status-filter" value={statusFilter} onChange={setStatusFilter} options={statusOptions} />
            <Select value={protocolFilter} onChange={setProtocolFilter} options={[{ label: '全部协议', value: 'all' }, { label: 'HTTP', value: 'HTTP' }, { label: 'TCP', value: 'TCP' }, { label: 'CERTIFICATE', value: 'CERTIFICATE' }]} />
          </Space>
        </div>}
        {props.mode === 'create' && requestForm}
        {props.mode === 'mine' && renderRequestTable(myRows, requestColumns)}
        {props.mode === 'approval' && renderRequestTable(approvalRows, approvalColumns)}
      </section>
      <Modal
        title="驳回申请"
        open={Boolean(rejectTarget)}
        okText="确认驳回"
        okButtonProps={{ danger: true, disabled: !rejectReason.trim() }}
        onOk={() => rejectTarget && rejectRequest(rejectTarget, rejectReason.trim())}
        onCancel={() => {
          setRejectTarget(null);
          setRejectReason('');
        }}
      >
        <Space direction="vertical" className="full-width">
          <Text type="secondary">请填写驳回原因，原因会写入工单审批记录。</Text>
          <Input.TextArea
            rows={4}
            value={rejectReason}
            onChange={(event) => setRejectReason(event.target.value)}
            placeholder="例如：目标地址不符合命名规范，需补充负责人或告警联系人。"
            maxLength={200}
            showCount
          />
        </Space>
      </Modal>
    </section>
  );
}

function AlertDetailPage() {
  const [alert, setAlert] = useState<ApiAlertEvent | null>(null);
  const [requestedAlertId, setRequestedAlertId] = useState('');
  useEffect(() => {
    const alertId = getHashEntityId('alerts');
    setRequestedAlertId(alertId);
    listAlertEvents()
      .then((data) => setAlert(data.items.find((item) => item.id === alertId) ?? null))
      .catch(() => setAlert(null));
  }, []);
  const refresh = (id: string) => {
    listAlertEvents().then((data) => setAlert(data.items.find((item) => item.id === id) ?? null));
  };
  const acknowledge = () => alert && acknowledgeAlertEvent(alert.id).then(() => refresh(alert.id));
  const close = () => alert && closeAlertEvent(alert.id, '详情页人工确认恢复').then(() => refresh(alert.id));
  return (
    <section className="page alert-detail-page">
      {alert ? (
        <section className="alert-detail-shell">
          <div className="alert-detail-head">
            <div className="detail-title-group">
              <Button type="text" icon={<LeftOutlined />} onClick={() => goDetailBack('alert', 'alerts')}>返回</Button>
              <div>
                <strong>{alert.title}</strong>
              </div>
            </div>
            {alert.status !== '已恢复' && (
              <Space>
                {alert.status === '待认领' && <Button onClick={acknowledge}>认领</Button>}
                <Button danger onClick={close}>关闭告警</Button>
              </Space>
            )}
          </div>
          <div className="alert-detail-layout">
            <main className="alert-detail-main">
              <section className="alert-section">
                <h3>告警概览</h3>
                <div className="alert-overview-grid">
                  <div className="alert-kv"><span>告警事件ID</span><strong className="alert-uuid">{getStableAlertUuid(alert.id)}</strong></div>
                  <div className="alert-kv"><span>告警事件</span><strong>{getAlertEventName(alert)}</strong></div>
                  <div className="alert-kv"><span>告警域名</span><strong>{alert.asset}</strong></div>
                  <div className="alert-kv"><span>告警时间</span><strong>{alert.trigger_at ?? '-'}</strong></div>
                  <div className="alert-kv"><span>告警等级</span><strong>{statusTag(alert.severity)}</strong></div>
                  <div className="alert-kv"><span>当前状态</span><strong>{statusTag(alert.status)}</strong></div>
                  <div className="alert-kv"><span>持续时间</span><strong>{alert.duration}</strong></div>
                  <div className="alert-kv"><span>告警策略</span><strong>{alert.strategy ?? '-'}</strong></div>
                  <div className="alert-kv"><span>探针节点</span><strong>{alert.probe ?? '-'}</strong></div>
                  <div className="alert-kv"><span>通知对象</span><strong>{getAlertRecipients(alert)}</strong></div>
                  <div className="alert-kv"><span>关联工单</span><strong>{alert.workorder && alert.workorder !== '-' ? alert.workorder : '未创建'}</strong></div>
                  {alert.close_reason && <div className="alert-kv"><span>关闭原因</span><strong>{alert.close_reason}</strong></div>}
                  <div className="alert-kv"><span>通知状态</span><NotifyChannelStatus alert={alert} /></div>
                </div>
              </section>
              <section className="alert-section">
                <h3>检测证据</h3>
                <Table
                  pagination={false}
                  size="middle"
                  dataSource={(alert.evidence ?? []).map((item, index) => ({ ...item, key: `${alert.id}-${index}` }))}
                  columns={[
                    { title: '时间', dataIndex: 'time', width: 120 },
                    { title: '探针', dataIndex: 'probe', width: 140 },
                    { title: '结果', dataIndex: 'result', width: 100, render: statusTag },
                    { title: '耗时', dataIndex: 'latency', width: 120 },
                    { title: '说明', dataIndex: 'message' }
                  ]}
                />
              </section>
            </main>
            <aside className="alert-detail-side">
              <h3>流转记录</h3>
              <Timeline items={(alert.timeline ?? []).map((item) => ({
                color: item.action.includes('关闭') ? 'green' : item.action.includes('触发') ? 'red' : 'blue',
                children: `${item.time} ${item.action} / ${item.actor} / ${item.remark}`
              }))} />
            </aside>
          </div>
        </section>
      ) : (
        <section className="alert-detail-shell">
          <div className="alert-detail-head">
            <div className="detail-title-group">
              <Button type="text" icon={<LeftOutlined />} onClick={() => goDetailBack('alert', 'alerts')}>返回</Button>
              <div>
                <strong>未找到告警事件</strong>
                <span>{requestedAlertId || '未知告警事件 ID'}</span>
              </div>
            </div>
          </div>
          <div className="empty-detail-state">
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="该告警事件不存在或当前账号无权查看" />
          </div>
        </section>
      )}
    </section>
  );
}

function AssetDetailPage() {
  return (
    <section className="page">
      <PageHeader
        module="资产中心 / 模型详情"
        title="支付域名服务模型"
        desc="模型详情是跨模块入口，必须展示字段、来源、同步批次、关联告警、关联策略、工单和变更历史。"
        action={<Space><Button>编辑字段</Button><Button>配置同步</Button><Button type="primary">创建监控策略</Button></Space>}
      />
      <div className="detail-shell">
        <div className="detail-main">
          <SectionBlock title="模型基础信息">
            <Descriptions bordered size="small" column={3}>
              <Descriptions.Item label="模型编码">pay_domain_service</Descriptions.Item>
              <Descriptions.Item label="创建方式">从模板创建</Descriptions.Item>
              <Descriptions.Item label="状态">{statusTag('运行')}</Descriptions.Item>
              <Descriptions.Item label="负责人">张三</Descriptions.Item>
              <Descriptions.Item label="部门">支付业务</Descriptions.Item>
              <Descriptions.Item label="环境">{statusTag('prod')}</Descriptions.Item>
              <Descriptions.Item label="来源">用户创建</Descriptions.Item>
              <Descriptions.Item label="字段数量">12</Descriptions.Item>
              <Descriptions.Item label="最近同步">2026-05-26 09:00</Descriptions.Item>
            </Descriptions>
          </SectionBlock>
          <SectionBlock title="字段质量与来源映射">
            <Table
              pagination={false}
              dataSource={[
                { key: '1', field: 'name', value: 'api.oneall.internal', source: 'bk_domain', quality: '完整' },
                { key: '2', field: 'owner', value: '张三', source: 'bk_biz_owner', quality: '完整' },
                { key: '3', field: 'department', value: '支付业务', source: 'bk_department', quality: '完整' },
                { key: '4', field: 'ssl_expire_at', value: '-', source: '未映射', quality: '缺失' }
              ]}
              columns={[
                { title: '字段', dataIndex: 'field' },
                { title: '当前值', dataIndex: 'value' },
                { title: '来源字段', dataIndex: 'source' },
                { title: '质量', dataIndex: 'quality', render: statusTag }
              ]}
            />
          </SectionBlock>
          <SectionBlock title="关联告警与策略">
            <Table
              pagination={false}
              dataSource={[
                { key: '1', type: '告警', name: 'HTTP 检测连续超时', status: '处理中', time: '09:23' },
                { key: '2', type: '策略', name: 'HTTP 可用性', status: '运行', time: '08:00' },
                { key: '3', type: '工单', name: 'WO-20260526-014', status: '执行中', time: '09:26' }
              ]}
              columns={[
                { title: '类型', dataIndex: 'type' },
                { title: '名称', dataIndex: 'name' },
                { title: '状态', dataIndex: 'status', render: statusTag },
                { title: '时间', dataIndex: 'time' }
              ]}
            />
          </SectionBlock>
        </div>
        <div className="detail-side">
          <SectionBlock title="资产健康">
            <Space direction="vertical" className="full-width">
              <div><Text>字段完整度</Text><Progress percent={91} strokeColor="#15803d" /></div>
              <div><Text>监控覆盖</Text><Progress percent={80} strokeColor="#1d4ed8" /></div>
              <div><Text>同步可信度</Text><Progress percent={96} strokeColor="#15803d" /></div>
            </Space>
          </SectionBlock>
          <SectionBlock title="变更历史">
            <Timeline items={[
              { color: 'blue', children: '09:00 蓝鲸 CMDB 同步 owner 字段' },
              { color: 'green', children: '昨天 新增 HTTP 可用性策略' },
              { color: 'orange', children: '05-20 资产纳管申请完成' }
            ]} />
          </SectionBlock>
        </div>
      </div>
    </section>
  );
}

function WorkorderDetailPage() {
  const { message: messageApi } = AntApp.useApp();
  const [workorder, setWorkorder] = useState<WorkorderRow | null>(null);
  const [requestedWorkorderId, setRequestedWorkorderId] = useState('');
  const currentRole = getCurrentApiRole();
  const canExecuteCurrentWorkorder = hasPermission(currentRole, 'workorders', 'manage') || hasPermission(currentRole, 'workorders', 'execute');
  const reloadWorkorder = (id: string) => {
    listWorkorderRequests()
      .then((data) => {
        const rows = data.items.map((item) => ({ ...item, key: item.id, status: item.status as WorkorderStatus }));
        setWorkorder(rows.find((item) => item.id === id) ?? null);
      })
      .catch(() => setWorkorder(null));
  };
  useEffect(() => {
    const id = getHashEntityId('workorders');
    setRequestedWorkorderId(id);
    reloadWorkorder(id);
  }, []);
  const request = workorder ? buildMonitoringRequest(workorder) : null;
  const deployFromWorkorder = (row: WorkorderRow) => {
    const data = buildMonitoringRequest(row);
    const statusCodes = data.expectedStatusCodes
      .split(',')
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isFinite(item));
    return createMonitoringStrategy({
      name: `${data.protocol} 拨测 ${data.target}`,
      scope: data.systemName,
      enabled: true,
      source_workorder_id: row.id,
      rule: {
        signal: { metric: data.protocol === 'CERTIFICATE' ? 'certificate_expire_days' : 'http_status' },
        condition: {
          operator: data.protocol === 'HTTP' ? 'not_in' : 'timeout',
          value: data.protocol === 'HTTP' ? statusCodes : Number.parseInt(data.timeoutSeconds, 10),
          consecutive: row.request_data?.failureCount ?? 3
        }
      }
    });
  };
  const executeAndDeploy = () => {
    if (!workorder || !canExecuteCurrentWorkorder || !canTransitionWorkorder(workorder.status, 'executing')) return;
    executeWorkorder(workorder.id)
      .then(() => deployFromWorkorder(workorder))
      .then((strategy) => {
        messageApi.success(`已下发监控策略 ${strategy.id}`);
        reloadWorkorder(workorder.id);
      })
      .catch((error: Error) => updateWorkorderRequest(workorder.id, { status: 'failed', remark: error.message }).then(() => {
        messageApi.error(error.message);
        reloadWorkorder(workorder.id);
      }));
  };
  const completeExecution = () => {
    if (!workorder || !canExecuteCurrentWorkorder || !canTransitionWorkorder(workorder.status, 'completed')) return;
    completeWorkorder(workorder.id).then(() => {
      messageApi.success(`已完成 ${workorder.id}`);
      reloadWorkorder(workorder.id);
    });
  };
  const markExecutionFailed = () => {
    if (!workorder || !canExecuteCurrentWorkorder || !canTransitionWorkorder(workorder.status, 'failed')) return;
    updateWorkorderRequest(workorder.id, { status: 'failed', remark: '执行人标记失败' }).then(() => {
      messageApi.error(`已标记执行失败 ${workorder.id}`);
      reloadWorkorder(workorder.id);
    });
  };
  const renderWorkorderDetailActions = () => {
    if (!workorder || !canExecuteCurrentWorkorder) return null;
    if (workorder.status === 'approved') {
      return (
        <Popconfirm title="执行下发" description="将按申请内容生成并启用监控策略。" okText="执行下发" cancelText="取消" onConfirm={executeAndDeploy}>
          <Button type="primary">执行下发</Button>
        </Popconfirm>
      );
    }
    if (workorder.status === 'executing') {
      return (
        <Space>
          <Button onClick={completeExecution}>标记完成</Button>
          <Button danger onClick={markExecutionFailed}>标记失败</Button>
        </Space>
      );
    }
    return null;
  };
  return (
    <section className="page alert-detail-page">
      {workorder && request ? (
        <section className="alert-detail-shell">
          <div className="alert-detail-head">
            <div className="detail-title-group">
              <Button type="text" icon={<LeftOutlined />} onClick={() => goDetailBack('workorder', 'workorders')}>返回</Button>
              <div>
                <strong>{workorder.id}</strong>
                <span>{workorder.title}</span>
              </div>
            </div>
            {renderWorkorderDetailActions()}
          </div>
          <div className="alert-detail-layout">
            <main className="alert-detail-main">
              <section className="alert-section">
                <h3>工单概览</h3>
                <div className="alert-overview-grid workorder-overview-grid">
                  <div className="alert-kv"><span>工单编号</span><strong>{workorder.id}</strong></div>
                  <div className="alert-kv"><span>当前状态</span><strong>{statusTag(workorderStatusLabel[workorder.status])}</strong></div>
                  <div className="alert-kv"><span>工单类型</span><strong>{workorder.type}</strong></div>
                  <div className="alert-kv"><span>申请人</span><strong>{workorder.applicant}</strong></div>
                  <div className="alert-kv"><span>执行人</span><strong>{workorder.assignee}</strong></div>
                  <div className="alert-kv"><span>关联策略</span><strong>{workorder.strategy_id ?? '待生成'}</strong></div>
                </div>
              </section>
              <section className="alert-section">
                <h3>申请内容</h3>
                <div className="alert-overview-grid workorder-request-grid">
                  <div className="alert-kv"><span>目标地址</span><strong>{request.target}</strong></div>
                  <div className="alert-kv"><span>所属系统</span><strong>{request.systemName}</strong></div>
                  <div className="alert-kv"><span>网络类型</span><strong>{request.networkType}</strong></div>
                  <div className="alert-kv"><span>负责人</span><strong>{request.owner}</strong></div>
                  <div className="alert-kv"><span>协议</span><strong>{request.protocol}</strong></div>
                  <div className="alert-kv"><span>频率</span><strong>{request.frequency}</strong></div>
                  <div className="alert-kv"><span>超时时间</span><strong>{request.timeoutSeconds}</strong></div>
                  <div className="alert-kv"><span>期望状态码</span><strong>{request.expectedStatusCodes}</strong></div>
                  <div className="alert-kv"><span>探针</span><strong>{request.probes}</strong></div>
                  <div className="alert-kv"><span>通知对象</span><strong>{request.alertContacts}</strong></div>
                  <div className="alert-kv alert-kv-wide"><span>告警规则</span><strong>{request.alertThreshold}</strong></div>
                </div>
              </section>
              <section className="alert-section">
                <h3>流转记录</h3>
                <Table
                  size="middle"
                  pagination={false}
                  dataSource={(workorder.approval_records ?? []).map((item, index) => ({ ...item, key: `${item.step}-${index}` }))}
                  columns={[
                    { title: '节点', dataIndex: 'step' },
                    { title: '处理人', dataIndex: 'actor' },
                    { title: '结果', dataIndex: 'result', render: statusTag },
                    { title: '时间', dataIndex: 'time' },
                    { title: '备注', dataIndex: 'remark', ellipsis: true }
                  ]}
                />
              </section>
            </main>
            <aside className="alert-detail-side">
              <section className="workorder-side-section">
                <h3>审批执行</h3>
                <div className="workorder-side-kv">
                  <div><span>审批人</span><strong>Approver</strong></div>
                  <div><span>SLA</span><strong>{workorder.sla}</strong></div>
                  <div><span>来源告警</span><strong>{workorder.relatedAlertId ?? '-'}</strong></div>
                </div>
              </section>
              <section className="workorder-side-section">
                <h3>流程</h3>
                <Steps direction="vertical" current={getWorkorderStepCurrent(workorder.status)} status={getWorkorderStepStatus(workorder.status)} items={[
                  { title: '提交申请', description: workorder.applicant },
                  { title: '业务审批', description: 'Approver' },
                  { title: '平台执行', description: workorder.assignee },
                  { title: '完成审计', description: workorder.strategy_id ?? '等待完成' }
                ]} />
              </section>
            </aside>
          </div>
        </section>
      ) : (
        <section className="alert-detail-shell">
          <div className="alert-detail-head">
            <div className="detail-title-group">
              <Button type="text" icon={<LeftOutlined />} onClick={() => goDetailBack('workorder', 'workorders')}>返回</Button>
              <div>
                <strong>未找到工单</strong>
                <span>{requestedWorkorderId || '未知工单 ID'}</span>
              </div>
            </div>
          </div>
          <div className="empty-detail-state">
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="该工单不存在或当前账号无权查看" />
          </div>
        </section>
      )}
    </section>
  );
}

function DetectionPage() {
  type DetectionRow = ApiDetectionTask & { key: string };
  const routeKey = getPageFromHash();
  const activeKind: 'http' | 'certificate' | 'cmdb' = routeKey === 'certificate-detection' ? 'certificate' : routeKey === 'cmdb-domain-check' ? 'cmdb' : 'http';
  const detectionTitle = activeKind === 'certificate' ? '证书检测' : activeKind === 'cmdb' ? 'CMDB 域名校验' : '域名拨测';
  const detectionActionText = activeKind === 'cmdb' ? '执行校验' : '执行检测';
  const [httpTarget, setHttpTarget] = useState('https://api.oneall.internal/health');
  const [httpProtocol, setHttpProtocol] = useState('HTTPS');
  const [certificateTarget, setCertificateTarget] = useState('www.oneall.internal');
  const [cmdbTarget, setCmdbTarget] = useState('api.oneall.internal');
  const [selectedProbes, setSelectedProbes] = useState<string[]>(['probe-sh-01']);
  const [timeoutSeconds, setTimeoutSeconds] = useState(10);
  const [port, setPort] = useState(443);
  const [followRedirects, setFollowRedirects] = useState(true);
  const [tasks, setTasks] = useState<DetectionRow[]>([]);
  const [probes, setProbeOptions] = useState<ApiProbeNode[]>([]);
  const [detectionMessage, setDetectionMessage] = useState('');
  const reloadTasks = () => {
    listDetectionTasks()
      .then((data) => setTasks(data.items.map((item) => ({ ...item, key: item.id }))))
      .catch(() => setTasks([]));
  };
  const reloadProbes = () => {
    listProbeNodes()
      .then((data) => {
        const nodes = data.items ?? [];
        setProbeOptions(nodes);
        setSelectedProbes((current) => current.length ? current : nodes.filter((node) => node.status === 'online').slice(0, 1).map((node) => node.name));
      })
      .catch(() => setProbeOptions([]));
  };
  useEffect(() => {
    reloadTasks();
    reloadProbes();
  }, []);
  const currentTarget = activeKind === 'certificate' ? certificateTarget : activeKind === 'cmdb' ? cmdbTarget : httpTarget;
  const runDetection = async () => {
    setDetectionMessage('');
    const input = {
      kind: activeKind,
      target: currentTarget,
      protocol: activeKind === 'http' ? httpProtocol : activeKind === 'certificate' ? 'CERTIFICATE' : 'CMDB',
      probes: activeKind === 'cmdb' ? [] : selectedProbes,
      port: activeKind === 'http' && httpProtocol !== 'Telnet' ? undefined : port,
      timeoutSeconds,
      followRedirects
    };
    const errors = validateDetectionInput(input);
    if (errors.length) {
      setDetectionMessage(errors[0]);
      return;
    }
    const probeTargets = activeKind === 'cmdb' ? [undefined] : selectedProbes;
    await Promise.all(probeTargets.map((probe) => createDetectionTask(buildDetectionRequest({ ...input, probe }))));
    setDetectionMessage(activeKind === 'cmdb' ? 'CMDB 校验已完成' : `已提交 ${probeTargets.length} 个探针检测`);
    reloadTasks();
  };
  const detectionHistoryWidth = useTableContainerWidth('.detection-history-body', 920);
  const detectionHistoryColumnWidths = distributeTableWidths(detectionHistoryWidth, [
    { min: 240, weight: 2 },
    { min: 150, weight: 0.9 },
    { min: 130, weight: 0.7 },
    { min: 220, weight: 1.4 },
    { min: 120, weight: 0 }
  ]);
  const probeOptions = probes.map((probe) => ({
    label: `${probe.region} / ${probe.name}`,
    value: probe.name,
    disabled: probe.status !== 'online'
  }));
  const statusResultTag = (value: string) => {
    if (value === 'success') return <Tag color="green">成功</Tag>;
    if (value === 'failed') return <Tag color="red">失败</Tag>;
    if (value === 'running') return <Tag color="blue">检测中</Tag>;
    return <Tag>{presentDetectionStatus(value)}</Tag>;
  };
  const detectionColumns: ColumnsType<DetectionRow> = [
    {
      title: '检测对象',
      width: detectionHistoryColumnWidths[0],
      render: (_, row) => (
        <div className="record-target-cell">
          <Tooltip title={row.target}><span>{row.target}</span></Tooltip>
          <Text type="secondary">{row.protocol ?? row.type}</Text>
        </div>
      )
    },
    { title: '执行探针', dataIndex: 'probe', width: detectionHistoryColumnWidths[1], ellipsis: true, render: (value, row) => row.type === 'cmdb' ? '-' : value },
    { title: '结果 / 耗时', width: detectionHistoryColumnWidths[2], render: (_, row) => <Space size={6}>{statusResultTag(row.status)}<Text type="secondary">{row.latency_ms ? `${row.latency_ms}ms` : '-'}</Text></Space> },
    { title: '说明', dataIndex: 'message', width: detectionHistoryColumnWidths[3], ellipsis: true, render: (value) => value ?? '-' },
    { title: '时间', dataIndex: 'created_at', width: detectionHistoryColumnWidths[4], ellipsis: true, render: (value) => value ? value.slice(5, 16).replace('T', ' ') : '-' }
  ];

  return (
    <section className="page">
      <section className="legacy-list-panel detection-console">
        <div className="detection-tabs">
          <div className="detection-page-title">
            <strong>{detectionTitle}</strong>
          </div>
          <div className="legacy-list-toolbar-right">
            {detectionMessage && <Text type={detectionMessage.includes('已') ? 'secondary' : 'danger'}>{detectionMessage}</Text>}
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={runDetection}>{detectionActionText}</Button>
          </div>
        </div>
        <div className="detection-console-body">
          {activeKind === 'http' && (
            <div className="detection-form-grid">
              <LabeledInput label="目标" value={httpTarget} onChange={(event) => setHttpTarget(event.target.value)} placeholder="https://api.oneall.internal/health" />
              <Space.Compact className="full-width"><span className="compact-input-label">协议</span><Select className="full-width" value={httpProtocol} options={['HTTPS', 'HTTP', 'WSS', 'Telnet'].map((value) => ({ label: value, value }))} onChange={setHttpProtocol} /></Space.Compact>
              {httpProtocol === 'Telnet' && <Space.Compact className="full-width"><span className="compact-input-label">端口</span><InputNumber className="full-width" min={1} max={65535} value={port} onChange={(value) => setPort(Number(value ?? 80))} /></Space.Compact>}
              <Space.Compact className="full-width"><span className="compact-input-label">超时</span><InputNumber className="full-width" min={1} max={60} value={timeoutSeconds} onChange={(value) => setTimeoutSeconds(Number(value ?? 10))} /><span className="compact-input-label compact-input-suffix">秒</span></Space.Compact>
              <Space.Compact className="full-width detection-probe-select"><span className="compact-input-label">探针</span><Select mode="multiple" className="full-width" value={selectedProbes} options={probeOptions} onChange={setSelectedProbes} /></Space.Compact>
              <Space align="center"><Switch checked={followRedirects} onChange={setFollowRedirects} /><Text type="secondary">跟随重定向</Text></Space>
            </div>
          )}
          {activeKind === 'certificate' && (
            <div className="detection-form-grid">
              <LabeledInput label="域名" value={certificateTarget} onChange={(event) => setCertificateTarget(event.target.value)} placeholder="www.oneall.internal" />
              <Space.Compact className="full-width"><span className="compact-input-label">端口</span><InputNumber className="full-width" min={1} max={65535} value={port} onChange={(value) => setPort(Number(value ?? 443))} /></Space.Compact>
              <Space.Compact className="full-width"><span className="compact-input-label">超时</span><InputNumber className="full-width" min={1} max={60} value={timeoutSeconds} onChange={(value) => setTimeoutSeconds(Number(value ?? 15))} /><span className="compact-input-label compact-input-suffix">秒</span></Space.Compact>
              <Space.Compact className="full-width detection-probe-select"><span className="compact-input-label">探针</span><Select mode="multiple" className="full-width" value={selectedProbes} options={probeOptions} onChange={setSelectedProbes} /></Space.Compact>
            </div>
          )}
          {activeKind === 'cmdb' && (
            <div className="detection-form-grid">
              <LabeledInput label="域名" value={cmdbTarget} onChange={(event) => setCmdbTarget(event.target.value)} placeholder="api.oneall.internal" />
            </div>
          )}
        </div>
      </section>
      <section className="legacy-list-panel detection-history-panel">
        <div className="legacy-list-toolbar">
          <div className="legacy-list-toolbar-left"><strong>检测历史</strong></div>
          <div className="legacy-list-toolbar-right"><Button icon={<ReloadOutlined />} onClick={reloadTasks}>刷新</Button></div>
        </div>
        <div className="legacy-list-body platform-table-body detection-history-body">
          <Table className="enterprise-fixed-table" tableLayout="fixed" size="middle" dataSource={tasks} columns={detectionColumns} pagination={tablePagination(10)} />
        </div>
      </section>
    </section>
  );
}

function IpRegexToolPage() {
  const [ipInput, setIpInput] = useState('');
  const [regexOutput, setRegexOutput] = useState('');
  const [invalidIps, setInvalidIps] = useState<string[]>([]);
  const [matchedCount, setMatchedCount] = useState(0);
  const [regexInput, setRegexInput] = useState('');
  const [reverseLimit, setReverseLimit] = useState(500);
  const [reverseResult, setReverseResult] = useState<string[]>([]);
  const [duplicateCount, setDuplicateCount] = useState(0);
  const [testIp, setTestIp] = useState('192.168.1.10');
  const [testResult, setTestResult] = useState<{ matched: boolean; validIp: boolean; error: string } | null>(null);
  const [error, setError] = useState('');
  const [showReversePanel, setShowReversePanel] = useState(false);

  const fillSample = () => {
    setIpInput(['192.168.1.10', '192.168.1.11', '192.168.1.12', '10.0.0.5', '10.0.0.6'].join('\n'));
    setError('');
  };

  const clearAll = () => {
    setIpInput('');
    setRegexOutput('');
    setInvalidIps([]);
    setMatchedCount(0);
    setRegexInput('');
    setReverseResult([]);
    setDuplicateCount(0);
    setTestResult(null);
    setError('');
  };

  const generateRegex = () => {
    const result = compileIpRegexFromText(ipInput);
    setRegexOutput(result.regex);
    setMatchedCount(result.matchedCount);
    setInvalidIps(result.invalidIps);
    setDuplicateCount(result.duplicateCount);
    if (result.regex && testIp.trim()) setTestResult(testIpAgainstRegex(testIp, result.regex));
    setError(result.matchedCount ? '' : '请至少输入一个合法 IPv4 地址');
  };

  const useGeneratedRegex = () => {
    if (!regexOutput) {
      setError('请先生成正则表达式');
      return;
    }
    setRegexInput(regexOutput);
    setShowReversePanel(true);
    setError('');
  };

  const expandRegex = () => {
    try {
      const result = expandIpRegex(regexInput, reverseLimit);
      setReverseResult(result.ips);
      setError(result.truncated ? `已按上限展示 ${result.limit} 条，共匹配 ${result.count} 条` : '');
    } catch (err) {
      setReverseResult([]);
      setError(err instanceof Error ? err.message : '解析失败，请检查正则');
    }
  };

  const runRegexTest = () => {
    const result = testIpAgainstRegex(testIp, regexOutput || regexInput);
    setTestResult(result);
    setError(result.error);
  };

  const copyText = async (text: string) => {
    if (!text.trim()) return;
    try {
      await navigator.clipboard.writeText(text);
      setError('');
    } catch {
      setError('复制失败，请手动选择内容');
    }
  };

  const ipLineCount = parseIpLines(ipInput).length;

  return (
    <section className="page">
      <section className="ip-regex-workbench">
        <div className="ip-regex-toolbar">
          <div className="ip-regex-toolbar-title">
            <strong>IP 正则助手</strong>
          </div>
          <Space>
            <Button onClick={fillSample}>填入示例</Button>
            <Button onClick={clearAll}>清空</Button>
          </Space>
        </div>
        <div className="ip-regex-panels ip-regex-panels-single">
          <div className="ip-regex-panel ip-regex-main-panel">
            <div className="ip-regex-primary-grid">
              <div className="ip-regex-flow-block">
                <div className="panel-title-line">
                  <span>输入 IP</span>
                  <Space size={6}><Tag color="blue">输入 {ipLineCount} 个</Tag><Tag>有效 {matchedCount} 个</Tag></Space>
                </div>
                <Input.TextArea
                  value={ipInput}
                  onChange={(event) => setIpInput(event.target.value)}
                  rows={8}
                  className="mono-textarea"
                  placeholder={'192.168.1.10\n192.168.1.11'}
                />
                <div className="panel-actions">
                  <Button type="primary" onClick={generateRegex}>生成正则</Button>
                  <Button onClick={() => setIpInput('')}>清空 IP</Button>
                  {duplicateCount > 0 && <Tag color="orange">重复 {duplicateCount} 个</Tag>}
                </div>
                {invalidIps.length > 0 && <Tag color="orange">无效 IP：{invalidIps.join(', ')}</Tag>}
              </div>
              <div className="ip-regex-flow-block">
                <div className="panel-title-line">
                  <span>生成结果</span>
                  <Space>
                    <Button type="link" icon={<CopyOutlined />} disabled={!regexOutput} onClick={() => copyText(regexOutput)}>复制</Button>
                    <Button type="link" disabled={!regexOutput} onClick={useGeneratedRegex}>覆盖校验</Button>
                  </Space>
                </div>
                <Input.TextArea value={regexOutput} rows={8} readOnly className="mono-textarea" placeholder="生成的正则会显示在这里" />
                <div className="panel-title-line sub">
                  <span>命中测试</span>
                  {testResult && <Tag color={testResult.matched ? 'green' : 'red'}>{testResult.matched ? '命中' : '未命中'}</Tag>}
                </div>
                <Space.Compact className="full-width">
                  <Input value={testIp} onChange={(event) => setTestIp(event.target.value)} placeholder="输入一个 IPv4 测试正则是否命中" />
                  <Button onClick={runRegexTest}>测试</Button>
                </Space.Compact>
              </div>
            </div>
          </div>
        </div>
        {error && <div className="regex-message"><Text type={error.includes('失败') || error.includes('合法') || error.includes('无法') || error.includes('不支持') ? 'danger' : 'secondary'}>{error}</Text></div>}
      </section>
      <Drawer title="覆盖校验" width={720} open={showReversePanel} onClose={() => setShowReversePanel(false)}>
        <Space direction="vertical" className="full-width" size={12}>
          <div className="panel-title-line"><span>正则表达式</span><Tag>最多 {reverseLimit} 条</Tag></div>
          <Input.TextArea
            value={regexInput}
            onChange={(event) => setRegexInput(event.target.value)}
            rows={8}
            className="mono-textarea"
            placeholder="^(192\\.168\\.1\\.10|192\\.168\\.1\\.11)$"
          />
          <div className="panel-actions">
            <Button type="primary" onClick={expandRegex}>解析范围</Button>
            <Button onClick={useGeneratedRegex}>使用生成结果</Button>
            <Select
              value={reverseLimit}
              onChange={setReverseLimit}
              options={[100, 500, 1000, 2000].map((value) => ({ label: `${value} 条`, value }))}
            />
          </div>
          <div className="panel-title-line sub">
            <span>解析结果</span>
            <Space>
              <Button type="link" icon={<CopyOutlined />} disabled={!reverseResult.length} onClick={() => copyText(reverseResult.join('\n'))}>复制</Button>
              <Tag>共 {reverseResult.length} 个</Tag>
            </Space>
          </div>
          <Input.TextArea value={reverseResult.join('\n')} rows={8} readOnly className="mono-textarea" placeholder="解析结果将显示在这里" />
        </Space>
      </Drawer>
    </section>
  );
}

function SettingsPage() {
  const [catalog, setCatalog] = useState<ApiPermissionCatalog | null>(null);
  useEffect(() => {
    getPermissionCatalog()
      .then(setCatalog)
      .catch(() => setCatalog(null));
  }, []);
  const matrix = catalog?.permissionMatrix ?? localPermissionMatrix;
  const permissionRows = buildPermissionRows(matrix);
  const rolesForTable = catalog?.roles?.length ? catalog.roles : apiRoles;

  return (
    <section className="page">
      <PageHeader module="系统设置" title="用户与权限" desc="企业级平台必须把角色、权限动作、数据范围、凭据授权和审计边界讲清楚。" action={<Button type="primary" icon={<UserOutlined />}>新建角色</Button>} />
      <div className="settings-grid">
        {rolesForTable.map((role) => (
          <div className="setting-card" key={role}>
            <div className="setting-icon">{role === 'PlatformAdmin' ? <UserOutlined /> : role === 'OpsAdmin' ? <DeploymentUnitOutlined /> : role === 'OpsEngineer' ? <ControlOutlined /> : <AuditOutlined />}</div>
            <strong>{role}</strong>
            <Text type="secondary">{roleDescriptions[role] ?? '按数据范围读取授权资源'}</Text>
          </div>
        ))}
      </div>
      <SectionBlock title="权限矩阵">
        <Table pagination={false} size="middle" dataSource={permissionRows} columns={[
          { title: '模块', dataIndex: 'module', width: 140 },
          ...rolesForTable.map((role) => ({ title: role, dataIndex: role, ellipsis: true }))
        ]} />
      </SectionBlock>
    </section>
  );
}

const credentialRows = [
  maskCredential({ id: 'cred_1', name: 'bk-prod-token', type: 'token', owner: 'PlatformAdmin', secret: 'bk_live_secret' }),
  maskCredential({ id: 'cred_2', name: 'zabbix-readonly', type: 'account', owner: 'OpsAdmin', secret: 'zabbix_pwd' }),
  maskCredential({ id: 'cred_3', name: 'ldap-bind', type: 'password', owner: 'PlatformAdmin', masked_secret: '******' })
];

function DataSourceManagementPage() {
  type DataSourceRow = { key: string; name: string; type: any; credential: any; status: string; owner: string };
  const dataSourceRows: DataSourceRow[] = [
    { key: '1', name: '蓝鲸 CMDB', type: 'blueking_cmdb', credential: 'token', status: '已连通', owner: 'PlatformAdmin' },
    { key: '2', name: 'Zabbix', type: 'zabbix', credential: 'account', status: '已连通', owner: 'OpsAdmin' },
    { key: '3', name: 'LDAP', type: 'ldap', credential: 'password', status: '待校验', owner: 'PlatformAdmin' }
  ];

  return (
    <section className="page">
      <PageHeader
        module="系统设置"
        title="数据源管理"
        desc="蓝鲸 CMDB、Zabbix、LDAP、Webhook 等统一在这里登记，资产同步只能引用已授权凭据。"
        action={<Button type="primary" icon={<DatabaseOutlined />}>新建数据源</Button>}
      />
      <div className="settings-grid">
        {dataSourceDefinitions.slice(0, 4).map((item) => (
          <div className="setting-card" key={item.type}>
            <div className="setting-icon">{item.type === 'blueking_cmdb' ? <DatabaseOutlined /> : item.type === 'webhook' ? <BellOutlined /> : <DeploymentUnitOutlined />}</div>
            <strong>{item.name}</strong>
            <Text type="secondary">{item.usage} / {item.allowedCredentialTypes.length ? item.allowedCredentialTypes.join('、') : '无需凭据'}</Text>
          </div>
        ))}
      </div>
      <SectionBlock title="数据源详情">
        <Table
          pagination={false}
          dataSource={dataSourceRows}
          columns={[
            { title: '数据源', dataIndex: 'name' },
            { title: '类型', dataIndex: 'type' },
            { title: '凭据类型', dataIndex: 'credential' },
            { title: '引用校验', render: (_, row: DataSourceRow) => statusTag(canReferenceCredential(row.type, row.credential) ? '已启用' : '失败') },
            { title: '负责人', dataIndex: 'owner' },
            { title: '状态', dataIndex: 'status', render: statusTag },
            { title: '操作', render: () => <Space><Button type="link">测试连接</Button><Button type="link">预览数据</Button></Space> }
          ]}
        />
      </SectionBlock>
    </section>
  );
}

function CredentialManagementPage() {
  return (
    <section className="page">
      <PageHeader
        module="系统设置"
        title="凭据管理"
        desc="敏感信息独立管理，API 响应只返回脱敏值；数据源和同步任务只能引用凭据 ID。"
        action={<Button type="primary" icon={<LockOutlined />}>新建凭据</Button>}
      />
      <SectionBlock title="凭据授权">
        <Table
          pagination={false}
          dataSource={credentialRows.map((row, index) => ({ ...row, key: row.id, status: index === 2 ? '待校验' : '已启用', scope: index === 0 ? '资产同步服务' : index === 1 ? '用户模型同步' : '用户同步' }))}
          columns={[
            { title: '凭据名称', dataIndex: 'name' },
            { title: '类型', dataIndex: 'type' },
            { title: '脱敏密钥', dataIndex: 'masked_secret' },
            { title: '授权范围', dataIndex: 'scope' },
            { title: '负责人', dataIndex: 'owner' },
            { title: '状态', dataIndex: 'status', render: statusTag },
            { title: '操作', render: () => <Space><Button type="link">轮换</Button><Button type="link">审计</Button></Space> }
          ]}
        />
      </SectionBlock>
    </section>
  );
}

function NotificationCenterPage() {
  const [deliveries, setDeliveries] = useState<Array<{ key: string; id: string; target: string; title: string; status: string; created_at: string }>>([]);
  useEffect(() => {
    listNotifications()
      .then((data) => setDeliveries(data.items.map((item) => ({ ...item, key: item.id }))))
      .catch(() => setDeliveries([]));
  }, []);

  return (
    <section className="page">
      <PageHeader
        module="系统设置"
        title="通知中心"
        desc="通知通道面向人，出站 Webhook 面向系统集成；事件订阅、模板变量和投递记录必须分开管理。"
        action={<Space><Button>新建模板</Button><Button type="primary" icon={<BellOutlined />}>新建通道</Button></Space>}
      />
      <div className="settings-grid">
        {notificationChannels.map((channel) => (
          <div className="setting-card" key={channel.type}>
            <div className="setting-icon">{channel.type === 'webhook' ? <DatabaseOutlined /> : <BellOutlined />}</div>
            <strong>{channel.name}</strong>
            <Text type="secondary">{channel.target === 'person' ? '面向人员通知' : '面向系统集成'} / {channel.supportedEvents.length} 类事件</Text>
          </div>
        ))}
      </div>
      <SectionBlock title="通知模板">
        <Table
          pagination={false}
          dataSource={notificationTemplates.map((item) => ({
            key: item.key,
            title: item.title,
            eventType: item.eventType,
            variables: item.variables.join('、'),
            webhookSupported: supportsNotificationEvent('webhook', item.eventType) ? '支持' : '不支持'
          }))}
          columns={[
            { title: '模板', dataIndex: 'title' },
            { title: '事件类型', dataIndex: 'eventType' },
            { title: '变量', dataIndex: 'variables' },
            { title: 'Webhook', dataIndex: 'webhookSupported', render: statusTag },
            { title: '操作', render: () => <Space><Button type="link">编辑</Button><Button type="link">投递记录</Button></Space> }
          ]}
        />
      </SectionBlock>
      <SectionBlock title="最近投递记录">
        <Table
          pagination={false}
          dataSource={deliveries}
          locale={{ emptyText: '暂无投递记录' }}
          columns={[
            { title: '时间', dataIndex: 'created_at', width: 210 },
            { title: '接收方', dataIndex: 'target', width: 130 },
            { title: '标题', dataIndex: 'title' },
            { title: '状态', dataIndex: 'status', width: 100, render: statusTag }
          ]}
        />
      </SectionBlock>
    </section>
  );
}

function ExecutionLogsPage() {
  const [rows, setRows] = useState<Array<{ key: string; id: string; task: string; target: string; probe: string; result: string; latency: string; time: string }>>([]);
  const reload = () => {
    listDetectionTasks()
      .then((data) => setRows(data.items.map((item) => ({
        key: item.id,
        id: item.id,
        task: `${item.type.toUpperCase()} 检测`,
        target: item.target,
        probe: item.probe,
        result: item.status === 'success' ? '成功' : item.status === 'failed' ? '失败' : '待执行',
        latency: '等待回传',
        time: item.created_at?.slice(11, 19) || '-'
      }))))
      .catch(() => setRows([]));
  };
  useEffect(() => {
    reload();
  }, []);
  return (
    <section className="page">
      <PageHeader
        module="监控与告警"
        title="执行日志"
        desc="记录探针任务、策略下发、检测结果和失败原因，便于排障与审计回溯。"
      />
      <FilterBar primary={<Button icon={<ReloadOutlined />} onClick={reload}>刷新</Button>}>
        <Select value="failed" options={[{ label: '失败优先', value: 'failed' }, { label: '全部状态', value: 'all' }]} />
      </FilterBar>
      <div className="data-card">
        <Table
          size="middle"
          dataSource={rows}
          columns={[
            { title: '执行 ID', dataIndex: 'id', width: 170 },
            { title: '任务', dataIndex: 'task', width: 150 },
            { title: '目标', dataIndex: 'target' },
            { title: '探针', dataIndex: 'probe', width: 130 },
            { title: '结果', dataIndex: 'result', width: 90, render: statusTag },
            { title: '耗时', dataIndex: 'latency', width: 100 },
            { title: '时间', dataIndex: 'time', width: 100 },
            { title: '操作', width: 120, render: () => <Button type="link">查看证据</Button> }
          ]}
        />
      </div>
    </section>
  );
}

function AssetMappingTemplatesPage() {
  const [models, setModels] = useState<AssetModelRow[]>([]);
  useEffect(() => {
    listAssetModels()
      .then((data) => setModels(data.items.map((item) => ({ ...item, key: item.id, workorder: '-', status: item.status }))))
      .catch(() => setModels([]));
  }, []);
  return (
    <section className="page">
      <PageHeader
        module="资产中心"
        title="字段映射模板"
        desc="把外部数据源字段映射到用户自建模型字段，模板只提供映射方法，不预置资产模型。"
        action={<Button type="primary" icon={<DatabaseOutlined />}>新建模板</Button>}
      />
      <CompactSummary items={[
        { label: '用户模型', value: models.length, tone: 'blue' },
        { label: '可用数据源', value: 2, tone: 'green' },
        { label: '待映射字段', value: models.reduce((total, item) => total + item.fields.length, 0), tone: 'orange' }
      ]} />
      <div className="data-card">
        <Table
          dataSource={models.map((item) => ({ key: item.id, name: `${item.name} 字段映射`, source: '用户选择数据源', model: item.name, fields: `${item.fields.length} / ${item.fields.length}`, status: item.fields.length ? '已校验' : '待校验' }))}
          columns={[
            { title: '模板名称', dataIndex: 'name' },
            { title: '数据源', dataIndex: 'source', width: 140 },
            { title: '目标模型', dataIndex: 'model', width: 150 },
            { title: '字段覆盖', dataIndex: 'fields', width: 120 },
            { title: '状态', dataIndex: 'status', width: 100, render: statusTag },
            { title: '操作', width: 150, render: () => <Space><Button type="link">编辑</Button><Button type="link">试映射</Button></Space> }
          ]}
        />
      </div>
    </section>
  );
}

function AssetImportExportRecordsPage() {
  const [rows, setRows] = useState<Array<{ key: string; batch: string; type: string; model: string; operator: string; success: number; failed: number; status: string; time: string }>>([]);
  const reload = () => {
    listAssetSyncRuns()
      .then((data) => setRows(data.items.map((item) => ({
        key: item.event_id,
        batch: item.event_id,
        type: item.event_type.includes('failed') ? '失败' : item.event_type.includes('completed') ? '同步' : '变更',
        model: item.payload?.model_id || '-',
        operator: item.producer,
        success: item.payload?.count || 0,
        failed: item.event_type.includes('failed') ? 1 : 0,
        status: item.event_type.includes('failed') ? '失败' : '已完成',
        time: item.created_at?.slice(11, 16) || '-'
      }))))
      .catch(() => setRows([]));
  };
  useEffect(() => {
    reload();
  }, []);
  return (
    <section className="page">
      <PageHeader
        module="资产中心"
        title="导入导出记录"
        desc="导入、导出、回滚和失败明细需要留痕，避免资产数据变更不可追溯。"
        action={<Button onClick={reload}>刷新记录</Button>}
      />
      <FilterBar primary={<Button type="primary">重新导入</Button>}>
        <Select value="all" options={[{ label: '全部类型', value: 'all' }, { label: '导入', value: 'import' }, { label: '导出', value: 'export' }]} />
      </FilterBar>
      <div className="data-card">
        <Table
          dataSource={rows}
          columns={[
            { title: '批次', dataIndex: 'batch', width: 165 },
            { title: '类型', dataIndex: 'type', width: 80 },
            { title: '模型', dataIndex: 'model' },
            { title: '操作人', dataIndex: 'operator', width: 100 },
            { title: '成功', dataIndex: 'success', width: 80 },
            { title: '失败', dataIndex: 'failed', width: 80 },
            { title: '状态', dataIndex: 'status', width: 100, render: statusTag },
            { title: '时间', dataIndex: 'time', width: 90 },
            { title: '操作', width: 130, render: () => <Button type="link">查看明细</Button> }
          ]}
        />
      </div>
    </section>
  );
}

function DetectionRecordsPage() {
  const [rows, setRows] = useState<Array<{ key: string; id: string; type: string; target: string; probe: string; result: string; related: string; time: string; latency: string; message: string }>>([]);
  const [keyword, setKeyword] = useState('');
  const [resultFilter, setResultFilter] = useState<'all' | 'success' | 'failed' | 'pending'>('all');
  const recordTableWidth = useTableContainerWidth('.detection-record-table-body', 940);
  const recordColumnWidths = distributeTableWidths(recordTableWidth, [
    { min: 250, weight: 2.2 },
    { min: 140, weight: 0.9 },
    { min: 130, weight: 0.7 },
    { min: 210, weight: 1.4 },
    { min: 110, weight: 0 },
    { min: 100, weight: 0 }
  ]);
  const formatDetectionType = (item: ApiDetectionTask) => {
    if (item.type === 'cmdb') return 'CMDB';
    if (item.type === 'certificate') return 'CERT';
    return item.protocol ?? 'HTTP';
  };
  const formatRecordId = (id: string) => id.length > 16 ? `${id.slice(0, 9)}…${id.slice(-4)}` : id;
  const formatRecordTime = (value?: string) => value ? value.slice(5, 16).replace('T', ' ') : '-';
  const reload = () => {
    listDetectionTasks()
      .then((data) => setRows(data.items.map((item) => ({
        key: item.id,
        id: item.id,
        type: formatDetectionType(item),
        target: item.target,
        probe: item.probe || '-',
        result: item.status === 'success' ? '成功' : item.status === 'failed' ? '失败' : '待执行',
        related: item.related_asset || '-',
        time: formatRecordTime(item.created_at),
        latency: item.latency_ms ? `${item.latency_ms}ms` : '-',
        message: item.message ?? '-'
      }))))
      .catch(() => setRows([]));
  };
  useEffect(() => {
    reload();
  }, []);
  const filteredRows = rows.filter((row) => {
    const keywordHit = !keyword.trim() || [row.id, row.type, row.target, row.probe, row.related, row.message].join(' ').toLowerCase().includes(keyword.trim().toLowerCase());
    const resultHit = resultFilter === 'all' || (resultFilter === 'success' && row.result === '成功') || (resultFilter === 'failed' && row.result === '失败') || (resultFilter === 'pending' && row.result === '待执行');
    return keywordHit && resultHit;
  });
  return (
    <section className="page">
      <section className="legacy-list-panel platform-table-panel detection-records-panel">
        <div className="legacy-list-toolbar">
          <div className="legacy-list-toolbar-left">
            <Input prefix={<SearchOutlined />} allowClear value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索记录、目标、探针、说明" />
            <Select
              value={resultFilter}
              onChange={setResultFilter}
              options={[
                { label: '全部结果', value: 'all' },
                { label: '成功', value: 'success' },
                { label: '失败', value: 'failed' },
                { label: '待执行', value: 'pending' }
              ]}
            />
          </div>
          <div className="legacy-list-toolbar-right">
            <Button icon={<ReloadOutlined />} onClick={reload}>刷新</Button>
          </div>
        </div>
        <div className="legacy-list-body platform-table-body detection-record-table-body">
          <Table
            className="enterprise-fixed-table detection-record-table"
            tableLayout="fixed"
            dataSource={filteredRows}
            columns={[
              {
                title: '检测对象',
                width: recordColumnWidths[0],
                render: (_, row) => (
                  <div className="record-target-cell">
                    <Tooltip title={row.target}><span>{row.target}</span></Tooltip>
                    <Text type="secondary">{formatRecordId(row.id)} / {row.type}</Text>
                  </div>
                )
              },
              { title: '执行探针', dataIndex: 'probe', width: recordColumnWidths[1], ellipsis: true },
              { title: '结果 / 耗时', width: recordColumnWidths[2], render: (_, row) => <Space size={6}>{statusTag(row.result)}<Text type="secondary">{row.latency}</Text></Space> },
              { title: '说明', dataIndex: 'message', width: recordColumnWidths[3], ellipsis: true },
              { title: '时间', dataIndex: 'time', width: recordColumnWidths[4], ellipsis: true },
              {
                title: '操作',
                width: recordColumnWidths[5],
                render: (_, row) => (
                  <Button type="link" onClick={() => {
                    rememberDetailReturn('execution-log', 'detection-records');
                    window.location.hash = `execution-logs/${encodeURIComponent(row.id)}`;
                  }}>详情</Button>
                )
              }
            ]}
            pagination={tablePagination(10)}
          />
        </div>
      </section>
    </section>
  );
}

function WorkorderNewPage() {
  return <WorkordersPage currentRole={getCurrentApiRole()} mode="create" />;
}

function PermissionMatrixPage() {
  return <SettingsPage />;
}

function SettingsPlatformPage() {
  return (
    <section className="page">
      <PageHeader
        module="系统设置"
        title="平台参数"
        desc="集中管理环境、业务线、SLA、任务并发和安全开关，变更必须进入审计日志。"
        action={<Button type="primary">保存变更</Button>}
      />
      <div className="settings-grid">
        {[
          ['环境', 'prod / staging / test', <DeploymentUnitOutlined />],
          ['任务并发', '探针任务 200，导入任务 20', <ControlOutlined />],
          ['SLA', 'P0 15m，P1 30m，P2 4h', <FieldTimeOutlined />],
          ['安全策略', '凭据脱敏、审计保留、Webhook 签名', <SafetyCertificateOutlined />]
        ].map(([title, desc, icon]) => <div className="setting-card" key={String(title)}><div className="setting-icon">{icon}</div><strong>{title}</strong><Text type="secondary">{desc}</Text></div>)}
      </div>
      <SectionBlock title="参数清单">
        <Table
          pagination={false}
          dataSource={[
            { key: '1', name: 'alert.auto_create_workorder', value: 'false', scope: '全局', owner: 'PlatformAdmin', status: '已启用' },
            { key: '2', name: 'probe.max_concurrency', value: '200', scope: '生产环境', owner: 'OpsAdmin', status: '已启用' },
            { key: '3', name: 'audit.retention_days', value: '365', scope: '全局', owner: 'PlatformAdmin', status: '已启用' }
          ]}
          columns={[
            { title: '参数', dataIndex: 'name' },
            { title: '值', dataIndex: 'value', width: 140 },
            { title: '范围', dataIndex: 'scope', width: 140 },
            { title: '负责人', dataIndex: 'owner', width: 130 },
            { title: '状态', dataIndex: 'status', width: 100, render: statusTag },
            { title: '操作', width: 120, render: () => <Button type="link">编辑</Button> }
          ]}
        />
      </SectionBlock>
    </section>
  );
}

function AuditLogsPage() {
  const fallbackRows: AuditLogRow[] = [
    { key: '1', id: 'AUD-demo-1', created_at: '09:31:12', actor: '张三', action: '关闭告警', object: 'ALERT-a1', result: '成功' },
    { key: '2', id: 'AUD-demo-2', created_at: '09:26:44', actor: '系统', action: '创建工单', object: 'WO-014', result: '成功' },
    { key: '3', id: 'AUD-demo-3', created_at: '09:10:03', actor: '李四', action: '引用凭据', object: 'bk-prod-token', result: '成功' }
  ];
  const [rows, setRows] = useState<AuditLogRow[]>(fallbackRows);
  useEffect(() => {
    listAuditLogs()
      .then((data) => setRows(data.items.map((item) => ({ ...item, key: item.id }))))
      .catch(() => setRows(fallbackRows));
  }, []);

  return (
    <section className="page">
      <PageHeader
        module="系统设置"
        title="审计日志"
        desc="记录用户、系统任务、凭据引用和数据变更，支持按对象和 trace_id 回放。"
        action={<Button>导出审计</Button>}
      />
      <FilterBar primary={<Button type="primary">查询</Button>}>
        <Select value="all" options={[{ label: '全部动作', value: 'all' }, { label: '高风险动作', value: 'risk' }]} />
      </FilterBar>
      <div className="data-card">
        <Table
          dataSource={rows}
          columns={[
            { title: '时间', dataIndex: 'created_at', width: 210 },
            { title: '操作者', dataIndex: 'actor', width: 110 },
            { title: '动作', dataIndex: 'action', width: 130 },
            { title: '对象', dataIndex: 'object' },
            { title: '结果', dataIndex: 'result', width: 90, render: statusTag },
            { title: '操作', width: 110, render: () => <Button type="link">查看上下文</Button> }
          ]}
        />
      </div>
    </section>
  );
}

function RetentionPolicyPage() {
  return (
    <section className="page">
      <PageHeader
        module="系统设置"
        title="数据保留策略"
        desc="按数据类型定义保留、归档、脱敏和删除策略，满足审计与成本控制。"
        action={<Button type="primary">新建策略</Button>}
      />
      <div className="data-card">
        <Table
          pagination={false}
          dataSource={[
            { key: '1', type: '告警事件', hot: '90 天', archive: '365 天', mask: '否', status: '已启用' },
            { key: '2', type: '检测日志', hot: '30 天', archive: '180 天', mask: '否', status: '已启用' },
            { key: '3', type: '审计日志', hot: '365 天', archive: '3 年', mask: '是', status: '已启用' },
            { key: '4', type: '凭据密文', hot: '仅引用', archive: '不归档', mask: '是', status: '已启用' }
          ]}
          columns={[
            { title: '数据类型', dataIndex: 'type' },
            { title: '在线保留', dataIndex: 'hot' },
            { title: '归档周期', dataIndex: 'archive' },
            { title: '脱敏', dataIndex: 'mask' },
            { title: '状态', dataIndex: 'status', render: statusTag },
            { title: '操作', render: () => <Space><Button type="link">编辑</Button><Button type="link">试算成本</Button></Space> }
          ]}
        />
      </div>
    </section>
  );
}

function PlaceholderPage(props: { title: string; module: string; icon: React.ReactNode }) {
  return (
    <section className="page">
      <PageHeader module={props.module} title={props.title} desc="该页面沿用同一套企业级信息密度、筛选、表格、详情抽屉和权限动作规范。" action={<Button type="primary">新增</Button>} />
      <div className="placeholder">{props.icon}<Text type="secondary">当前先以核心页面定风格，后续展开完整表格与详情。</Text></div>
    </section>
  );
}

function Root() {
  const [active, setActive] = useState<PageKey>(getPageFromHash());
  const [currentRole] = useState<ApiRole>(() => getCurrentApiRole());
  const currentModule = getRouteByKey(active)?.module;
  const [openNavGroups, setOpenNavGroups] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(nextNavGroups.map((group) => [group.title, group.title === currentModule]))
  );
  useEffect(() => {
    const handleHashChange = () => {
      const nextActive = getPageFromHash();
      setActive(nextActive);
      const nextModule = getRouteByKey(nextActive)?.module;
      if (nextModule) {
        setOpenNavGroups((prev) => ({ ...prev, [nextModule]: true }));
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);
  const switchPage = (key: string) => {
    window.location.hash = key;
    setActive(key as PageKey);
    const nextModule = getRouteByKey(key as PageKey)?.module;
    if (nextModule) {
      setOpenNavGroups((prev) => ({ ...prev, [nextModule]: true }));
    }
  };

  const render: Partial<Record<PageKey, React.ReactNode>> = useMemo(() => ({
    'monitoring-overview': <MonitoringOverviewPage onOpenAlert={() => switchPage('alert-detail')} />,
    alerts: <AlertsPage onOpenDetail={() => switchPage('alert-detail')} />,
    'alert-detail': <AlertDetailPage />,
    policies: <PoliciesPage />,
    'policy-detail': <PolicyDetailPage />,
    'policy-rule-config': <PolicyRuleConfigPage />,
    probes: <ProbesPage />,
    'probe-detail': <ProbeDetailPage />,
    'execution-logs': <ExecutionLogsPage />,
    'execution-log-detail': <ExecutionLogDetailPage />,
    assets: <AssetsPage />,
    'asset-model-management': <AssetModelManagementPage />,
    'asset-new': <AssetNewPage />,
    'asset-detail': <AssetDetailPage />,
    'asset-records': <AssetRecordsPage />,
    'asset-fields': <AssetFieldsPage />,
    'asset-sync-config': <AssetSyncConfigPage />,
    'asset-sync-history': <AssetSyncHistoryPage />,
    'asset-permissions-audit': <AssetPermissionsAuditPage />,
    'asset-sync': <AssetSyncPage />,
    'asset-sync-preview': <AssetSyncPreviewPage />,
    'asset-sync-history-list': <AssetSyncHistoryPage />,
    'asset-mapping-templates': <AssetMappingTemplatesPage />,
    'asset-import-export-records': <AssetImportExportRecordsPage />,
    detection: <DetectionPage />,
    'certificate-detection': <DetectionPage />,
    'cmdb-domain-check': <DetectionPage />,
    'detection-records': <DetectionRecordsPage />,
    'workorder-new': <WorkordersPage currentRole={currentRole} mode="create" />,
    workorders: <WorkordersPage currentRole={currentRole} mode="mine" />,
    'workorder-detail': <WorkorderDetailPage />,
    approvals: <WorkordersPage currentRole={currentRole} mode="approval" />,
    'workorder-execution': <WorkordersPage currentRole={currentRole} mode="mine" />,
    'settings-platform': <SettingsPlatformPage />,
    'settings-permissions': <SettingsPage />,
    'settings-permission-matrix': <PermissionMatrixPage />,
    'settings-integrations': <DataSourceManagementPage />,
    'settings-credentials': <CredentialManagementPage />,
    'settings-notification-channels': <NotificationCenterPage />,
    'settings-notification-templates': <NotificationCenterPage />,
    'settings-webhooks': <NotificationCenterPage />,
    'settings-audit-logs': <AuditLogsPage />,
    'settings-retention': <RetentionPolicyPage />,
    'ip-regex': <IpRegexToolPage />
  }), [currentRole]);
  const activeRoute = getRouteByKey(active);
  const activeNavKey = getNavParentKey(active);

  return (
    <ConfigProvider locale={zhCN} theme={{ token: { borderRadius: 6, colorPrimary: '#1d4ed8', fontFamily: 'Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif' } }}>
      <AntApp>
        <Layout className="app-shell oneall-next-shell">
          <Header className="topbar next-topbar">
            <div className="brand"><div className="logo">OA</div><div><b>OneAll</b><span>控制台</span></div></div>
            <div className="top-context-tools">
              {active === 'asset-sync' && (
                <Button
                  className="sync-refresh-button"
                  icon={<ReloadOutlined />}
                  title="刷新同步脚本"
                  aria-label="刷新同步脚本"
                  onClick={() => window.dispatchEvent(new Event('oneall:asset-sync-refresh'))}
                />
              )}
            </div>
            <Space className="top-actions">
              <Badge count={6}><Button shape="circle" icon={<BellOutlined />} /></Badge>
              <Avatar style={{ background: '#eaf1ff', color: '#1d4ed8' }}>OA</Avatar>
            </Space>
          </Header>
          <Layout className="below-shell">
            <Sider width={252} theme="light" className="sider next-sider">
              <div className="nav-context">
                <strong>OneAll 下一版</strong>
                <span>轻量运维控制台</span>
              </div>
              <nav className="next-nav">
                {nextNavGroups.map((group) => (
                  <div className="next-nav-group" key={group.title}>
                    <button
                      className="next-nav-title"
                      onClick={() => setOpenNavGroups((prev) => ({ ...prev, [group.title]: !prev[group.title] }))}
                    >
                      <span className="next-nav-title-main">{group.icon}<span>{group.title}</span></span>
                      {openNavGroups[group.title] ? <DownOutlined /> : <RightOutlined />}
                    </button>
                    {openNavGroups[group.title] && (
                      <div className="next-nav-items">
                        {group.items.map((item) => (
                          <button
                            key={item.key}
                            className={activeNavKey === item.key ? 'next-nav-item active' : 'next-nav-item'}
                            onClick={() => switchPage(item.key)}
                          >
                            {item.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </nav>
              <div className="side-footer"><SafetyCertificateOutlined /><span>OneAll 控制台</span></div>
            </Sider>
            <Layout>
            <Content key={`${active}-${currentRole}`}>{render[active] ?? <PlaceholderPage title={activeRoute?.label ?? '页面'} module={activeRoute?.module ?? 'OneAll'} icon={<SettingOutlined />} />}</Content>
          </Layout>
          </Layout>
        </Layout>
      </AntApp>
    </ConfigProvider>
  );
}

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element #root was not found');
}

const rootHost = rootElement as HTMLElement & { __oneallRoot?: ReturnType<typeof createRoot> };
const appRoot = rootHost.__oneallRoot ?? createRoot(rootElement);
rootHost.__oneallRoot = appRoot;
appRoot.render(<Root />);
