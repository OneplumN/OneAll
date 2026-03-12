import type { ScriptPluginRecord } from '@/services/toolsApi';

export type PluginFieldType = 'input' | 'textarea' | 'script';

export interface PluginFieldDefinition {
  key: string;
  label: string;
  placeholder?: string;
  type?: PluginFieldType;
}

export type PluginRuntimeMode = 'embedded' | 'script';

export interface PluginRuntimeDefinition {
  mode: PluginRuntimeMode;
  description: string;
  scriptLabel?: string;
}

export type IntegrationPluginGroupKey = 'monitoring' | 'detection' | 'reports' | 'assets' | 'tools';

export interface IntegrationPluginDefinition {
  key: string;
  name: string;
  route: string;
  component: string;
  group: IntegrationPluginGroupKey;
  builtin?: boolean;
  notes?: string;
  configFields: PluginFieldDefinition[];
  managerComponent?: 'monitoring-overview-config';
  runtime: PluginRuntimeDefinition;
  pluginSource?: 'static' | 'script';
  scriptPlugin?: ScriptPluginRecord;
}

export interface IntegrationPluginGroup {
  key: IntegrationPluginGroupKey;
  title: string;
  description: string;
  plugins: IntegrationPluginDefinition[];
}

const monitoringPlugins: IntegrationPluginDefinition[] = [
  {
    key: 'monitoring_overview',
    name: '驾驶舱',
    route: '/monitoring/overview',
    component: 'Home.vue',
    group: 'monitoring',
    builtin: true,
    managerComponent: undefined,
    configFields: [],
    runtime: {
      mode: 'embedded',
      description: '后端聚合计算驾驶舱指标，无需额外配置。'
    }
  },
  {
    key: 'monitoring_zabbix',
    name: 'Zabbix',
    route: '/monitoring/zabbix',
    component: 'MonitoringDashboard.vue',
    group: 'monitoring',
    builtin: true,
    configFields: [
      {
        key: 'base_url',
        label: 'API 地址',
        placeholder: 'https://zabbix.example.com/api_jsonrpc.php'
      },
      {
        key: 'username',
        label: '用户名',
        placeholder: 'automation-user'
      },
      {
        key: 'token',
        label: 'API Token / 密码',
        placeholder: '在 Zabbix 后台生成的 API Token'
      }
    ],
    runtime: {
      mode: 'embedded',
      description: '填写 API 地址与凭据后，平台即可拉取 Zabbix 告警、主机等数据。'
    }
  },
  {
    key: 'monitoring_prometheus',
    name: 'Prometheus',
    route: '/monitoring/prometheus',
    component: 'MonitoringDashboard.vue',
    group: 'monitoring',
    builtin: true,
    configFields: [
      {
        key: 'base_url',
        label: 'Prometheus API',
        placeholder: 'http://prometheus.example.com'
      },
      {
        key: 'bearer_token',
        label: 'Bearer Token',
        placeholder: '可选，用于受保护的 API'
      }
    ],
    runtime: {
      mode: 'embedded',
      description: '在此维护 Prometheus 接入地址与可选的访问令牌。'
    }
  }
];

const detectionPlugins: IntegrationPluginDefinition[] = [
  {
    key: 'tool_domain_probe',
    name: '域名拨测',
    route: '/oneoff/domain',
    component: 'OneOffDetection.vue',
    group: 'detection',
    builtin: true,
    configFields: [],
    runtime: {
      mode: 'embedded',
      description: '一次性拨测由后端检测服务执行，无需脚本。'
    }
  },
  {
    key: 'tool_certificate',
    name: '证书检测',
    route: '/oneoff/certificate',
    component: 'CertificateDetection.vue',
    group: 'detection',
    builtin: true,
    configFields: [],
    runtime: {
      mode: 'embedded',
      description: '证书检测直接调用后端探针任务，无需配置。'
    }
  },
  {
    key: 'tool_cmdb_check',
    name: 'CMDB 域名检测',
    route: '/oneoff/cmdb',
    component: 'CmdbDomainCheck.vue',
    group: 'detection',
    builtin: true,
    configFields: [],
    runtime: {
      mode: 'embedded',
      description: 'CMDB 域名检测走后端资产校验逻辑，无需额外脚本。'
    }
  }
];

const reportPlugins: IntegrationPluginDefinition[] = [
  {
    key: 'report_detection',
    name: '拨测报表',
    route: '/analytics/detection',
    component: 'MonitoringReports.vue',
    group: 'reports',
    builtin: true,
    configFields: [],
    runtime: {
      mode: 'script',
      description: '固定报表脚本生成并推送拨测数据，前端只负责触发。',
      scriptLabel: 'reports_detection_export'
    }
  },
  {
    key: 'report_asset_governance',
    name: '资产监控治理',
    route: '/analytics/assets',
    component: 'AssetGovernance.vue',
    group: 'reports',
    builtin: true,
    configFields: [],
    runtime: {
      mode: 'embedded',
      description: '基于资产入库数据生成治理统计，无需额外脚本与配置。'
    }
  }
];

const assetPlugins: IntegrationPluginDefinition[] = [
  {
    key: 'asset_cmdb_domain',
    name: '域名',
    route: '/assets/domain',
    component: 'AssetCenter.vue',
    group: 'assets',
    builtin: true,
    configFields: [],
    runtime: {
      mode: 'script',
      description: '固定脚本同步 CMDB 域名资产。',
      scriptLabel: 'assets_sync_domain'
    }
  },
  {
    key: 'asset_zabbix_host',
    name: 'Zabbix 主机',
    route: '/assets/zabbix',
    component: 'AssetCenter.vue',
    group: 'assets',
    configFields: [],
    runtime: {
      mode: 'script',
      description: '固定脚本拉取 Zabbix 主机信息。',
      scriptLabel: 'assets_sync_zabbix_host'
    }
  },
  {
    key: 'asset_ipmp_project',
    name: 'IPMP 项目',
    route: '/assets/ipmp',
    component: 'AssetCenter.vue',
    group: 'assets',
    configFields: [],
    runtime: {
      mode: 'script',
      description: '固定脚本通过 IPMP 接口拉取项目数据。',
      scriptLabel: 'assets_sync_ipmp_project'
    }
  },
  {
    key: 'asset_workorder_host',
    name: '工单纳管主机信息',
    route: '/assets/workorder-hosts',
    component: 'AssetCenter.vue',
    group: 'assets',
    configFields: [],
    runtime: {
      mode: 'script',
      description: '固定脚本解析 ITSM 导出并入库工单纳管主机信息。',
      scriptLabel: 'assets_sync_workorder_host'
    }
  }
];

const toolPlugins: IntegrationPluginDefinition[] = [];

export const INTEGRATION_PLUGIN_GROUPS: Record<IntegrationPluginGroupKey, IntegrationPluginGroup> = {
  monitoring: {
    key: 'monitoring',
    title: '监控插件',
    description: '管理驾驶舱、Zabbix、Prometheus 等监控能力的接入与配置。',
    plugins: monitoringPlugins
  },
  detection: {
    key: 'detection',
    title: '检测工具插件',
    description: '一次性拨测、证书检测、CMDB 检测等临时检测能力的入口。',
    plugins: detectionPlugins
  },
  reports: {
    key: 'reports',
    title: '报表插件',
    description: '配置拨测统计报表的模板、调度与投递渠道。',
    plugins: reportPlugins
  },
  assets: {
    key: 'assets',
    title: '资产信息插件',
    description: '域名、Zabbix 主机、IPMP 项目、工单纳管主机等资产同步入口。',
    plugins: assetPlugins
  },
  tools: {
    key: 'tools',
    title: '运维脚本插件',
    description: '依托代码管理的脚本助手，例如 IP 正则等运维工具。',
    plugins: toolPlugins
  }
};

export const INTEGRATION_PLUGIN_MAP: Record<string, IntegrationPluginDefinition> = Object.values(
  INTEGRATION_PLUGIN_GROUPS
).reduce<Record<string, IntegrationPluginDefinition>>((acc, group) => {
  group.plugins.forEach((plugin) => {
    acc[plugin.key] = plugin;
  });
  return acc;
}, {});

export function getPluginGroup(key: IntegrationPluginGroupKey) {
  return INTEGRATION_PLUGIN_GROUPS[key];
}

export function getPluginDefinition(key: string) {
  return INTEGRATION_PLUGIN_MAP[key];
}
