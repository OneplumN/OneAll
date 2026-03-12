import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import { ElMessage } from 'element-plus';

import { i18n } from '@/i18n';
import { useSessionStore } from '@/stores/session';
import { useBrandingStore } from '@/stores/branding';

declare module 'vue-router' {
  interface RouteMeta {
    modulePermission?: string;
    navGroup?: string;
    navLabel?: string;
    title?: string;
  }
}

export interface NavGroupConfig {
  key: string;
  label: string;
  permission?: string;
  items: Array<NavItemConfig>;
}

export interface NavItemConfig {
  label: string;
  path?: string;
  hidden?: boolean;
  pluginType?: string;
  permission?: string;
  children?: Array<{
    label: string;
    path: string;
    hidden?: boolean;
    pluginType?: string;
    permission?: string;
  }>;
}

const GROUP_MODULE_PERMISSIONS: Record<string, string> = {
  monitoring: 'monitoring.module.access',
  oneoff: 'detection.module.access',
  request: 'detection.module.access',
  analytics: 'analytics.module.access',
  assets: 'assets.module.access',
  tools: 'tools.module.access',
  code: 'tools.module.access',
  integrations: 'integrations.module.access',
  probes: 'probes.module.access',
  knowledge: 'knowledge.module.access',
  settings: 'settings.module.access'
};

export const NAV_GROUPS: NavGroupConfig[] = [
  {
    key: 'monitoring',
    label: '监控',
    permission: GROUP_MODULE_PERMISSIONS.monitoring,
    items: [
      {
        label: '驾驶舱',
        children: [
          {
            label: '蜂窝总览',
            path: '/monitoring/overview',
            permission: 'monitoring.overview.view'
          },
          { label: '探针中心', path: '/monitoring/probes', permission: 'probes.nodes.view' }
        ]
      },
      {
        label: 'Zabbix',
        path: '/monitoring/zabbix',
        permission: GROUP_MODULE_PERMISSIONS.monitoring
      },
      {
        label: 'Prometheus',
        path: '/monitoring/prometheus',
        permission: GROUP_MODULE_PERMISSIONS.monitoring
      }
    ]
  },
  {
    key: 'oneoff',
    label: '一次性检验',
    permission: GROUP_MODULE_PERMISSIONS.oneoff,
    items: [
      { label: '域名拨测', path: '/oneoff/domain', permission: 'detection.oneoff.view' },
      { label: '证书检测', path: '/oneoff/certificate', permission: 'detection.oneoff.view' },
      { label: 'CMDB 域名检测', path: '/oneoff/cmdb', permission: 'detection.oneoff.view' }
    ]
  },
  {
    key: 'request',
    label: '工单申请',
    permission: GROUP_MODULE_PERMISSIONS.request,
    items: [
      { label: '拨测监控申请', path: '/monitoring/request', permission: 'detection.schedules.view' }
    ]
  },
  {
    key: 'analytics',
    label: '统计分析',
    permission: GROUP_MODULE_PERMISSIONS.analytics,
    items: [
      { label: '拨测', path: '/analytics/detection', permission: 'analytics.reports.view' },
      { label: '资产监控治理', path: '/analytics/assets', permission: 'analytics.reports.view' }
    ]
  },
  {
    key: 'assets',
    label: '资产信息',
    permission: GROUP_MODULE_PERMISSIONS.assets,
    items: [
      { label: '域名', path: '/assets/domain', permission: 'assets.records.view' },
      { label: 'Zabbix 主机', path: '/assets/zabbix', permission: 'assets.records.view' },
      { label: 'IPMP 项目', path: '/assets/ipmp', permission: 'assets.records.view' },
      {
        label: '工单纳管主机信息',
        path: '/assets/workorder-hosts',
        permission: 'assets.records.view'
      }
    ]
  },
  {
    key: 'tools',
    label: '运维工具',
    permission: GROUP_MODULE_PERMISSIONS.tools,
    items: [
      { label: 'IP 正则助手', path: '/tools/ip-regex', permission: 'tools.library.view' },
      { label: '账号同步', path: '/tools/account-sync', permission: 'tools.library.view' },
      { label: 'Grafana 同步', path: '/tools/grafana-sync', permission: 'tools.library.view' }
    ]
  },
  {
    key: 'code',
    label: '代码管理',
    permission: GROUP_MODULE_PERMISSIONS.code,
    items: [{ label: '全部脚本', path: '/code/repository', permission: 'tools.repository.view' }]
  },
  {
    key: 'integrations',
    label: '集成',
    permission: GROUP_MODULE_PERMISSIONS.integrations,
    items: [
      { label: '监控插件', path: '/integrations/monitoring', permission: 'integrations.hub.view' },
      { label: '检测工具插件', path: '/integrations/detection', permission: 'integrations.hub.view' },
      { label: '报表插件', path: '/integrations/reports', permission: 'integrations.hub.view' },
      { label: '资产信息插件', path: '/integrations/assets', permission: 'integrations.hub.view' },
      { label: '运维脚本插件', path: '/integrations/tools', permission: 'integrations.hub.view' }
    ]
  },
  {
    key: 'probes',
    label: '探针',
    permission: GROUP_MODULE_PERMISSIONS.probes,
    items: [
      { label: '节点', path: '/probes/nodes', permission: 'probes.nodes.view' },
      { label: '调度', path: '/probes/schedules', permission: 'detection.schedules.view' },
      { label: '日志', path: '/probes/logs', permission: 'detection.schedules.view' }
    ]
  },
  {
    key: 'knowledge',
    label: '知识库',
    permission: GROUP_MODULE_PERMISSIONS.knowledge,
    items: [{ label: '知识库', path: '/knowledge', permission: 'knowledge.articles.view' }]
  },
  {
    key: 'settings',
    label: '系统设置',
    permission: GROUP_MODULE_PERMISSIONS.settings,
    items: [
      { label: '用户', path: '/settings/users', permission: 'settings.users.view' },
      { label: '权限', path: '/settings/permissions', permission: 'settings.roles.view' },
      { label: '日志', path: '/settings/logs', permission: 'settings.audit_log.view' },
      { label: '告警', path: '/settings/alerts', permission: 'alerts.channels.view' },
      { label: '主题', path: '/settings/theme', hidden: true, permission: 'settings.system.view' },
      { label: '全局设置', path: '/settings/system', permission: 'settings.system.view' }
    ]
  }
];

const authMeta = (group: string, label: string) => ({
  requiresAuth: true,
  navGroup: group,
  navLabel: label,
  modulePermission: GROUP_MODULE_PERMISSIONS[group]
});

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../pages/auth/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('../pages/errors/Forbidden.vue'),
    meta: { title: '无权限' }
  },
  {
    path: '/profile',
    name: 'user-profile',
    component: () => import('../pages/profile/UserProfile.vue'),
    meta: {
      requiresAuth: true,
      title: '个人资料',
      layoutFlat: true,
      hideSideNav: true,
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/',
    redirect: '/monitoring/overview'
  },
  {
    path: '/monitoring/dashboard',
    redirect: '/integrations/monitoring/overview'
  },
  {
    path: '/monitoring/history',
    redirect: '/probes/logs'
  },
  {
    path: '/probes',
    redirect: '/monitoring/probes'
  },
  {
    path: '/tools/code-repository',
    redirect: '/code/repository'
  },
  {
    path: '/analytics/reports',
    redirect: '/analytics/detection'
  },
  {
    path: '/assets',
    redirect: '/assets/domain'
  },
  {
    path: '/monitoring/overview',
    name: 'monitoring-overview',
    component: () => import('../pages/Home.vue'),
    meta: {
      ...authMeta('monitoring', '驾驶舱'),
      pluginType: 'monitoring_overview',
      permission: 'monitoring.overview.view'
    }
  },
  {
    path: '/monitoring/probes',
    name: 'monitoring-probes',
    component: () => import('../pages/probes/ProbeCenter.vue'),
    meta: {
      ...authMeta('monitoring', '探针中心'),
      permission: 'probes.nodes.view',
      layoutFlat: true,
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/monitoring/zabbix',
    name: 'monitoring-zabbix',
    component: () => import('../pages/monitoring/MonitoringZabbixPlugin.vue'),
    meta: {
      ...authMeta('monitoring', 'Zabbix'),
      pluginType: 'monitoring_zabbix',
      permission: GROUP_MODULE_PERMISSIONS.monitoring
    }
  },
  {
    path: '/monitoring/prometheus',
    name: 'monitoring-prometheus',
    component: () => import('../pages/monitoring/MonitoringPrometheusPlugin.vue'),
    meta: {
      ...authMeta('monitoring', 'Prometheus'),
      pluginType: 'monitoring_prometheus',
      permission: GROUP_MODULE_PERMISSIONS.monitoring
    }
  },
  {
    path: '/oneoff/domain',
    name: 'oneoff-domain',
    component: () => import('../pages/detection/OneOffDetection.vue'),
    meta: {
      ...authMeta('oneoff', '域名拨测'),
      layoutFlat: true,
      contentPadding: '0 16px 16px',
      pluginType: 'tool_domain_probe',
      permission: 'detection.oneoff.view'
    }
  },
  {
    path: '/oneoff/certificate',
    name: 'oneoff-certificate',
    component: () => import('../pages/detection/CertificateDetection.vue'),
    meta: {
      ...authMeta('oneoff', '证书检测'),
      layoutFlat: true,
      contentPadding: '0 16px 16px',
      pluginType: 'tool_certificate',
      permission: 'detection.oneoff.view'
    }
  },
  {
    path: '/oneoff/cmdb',
    name: 'oneoff-cmdb',
    component: () => import('../pages/detection/CmdbDomainCheck.vue'),
    meta: {
      ...authMeta('oneoff', 'CMDB 域名检测'),
      layoutFlat: true,
      contentPadding: '0 16px 16px',
      pluginType: 'tool_cmdb_check',
      permission: 'detection.oneoff.view'
    }
  },
  {
    path: '/monitoring/request',
    name: 'monitoring-request',
    component: () => import('../pages/monitoring/MonitoringRequestForm.vue'),
    meta: {
      ...authMeta('request', '拨测监控申请'),
      permission: 'detection.schedules.view',
      layoutFlat: true,
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/analytics/detection',
    name: 'analytics-detection',
    component: () => import('../pages/analytics/MonitoringReports.vue'),
    meta: {
      ...authMeta('analytics', '拨测'),
      pluginType: 'report_detection',
      permission: 'analytics.reports.view',
      layoutFlat: true
    }
  },
  {
    path: '/analytics/assets',
    name: 'analytics-assets',
    component: () => import('../pages/analytics/AssetGovernance.vue'),
    meta: {
      ...authMeta('analytics', '资产监控治理'),
      pluginType: 'report_asset_governance',
      permission: 'analytics.reports.view',
      layoutFlat: true
    }
  },
  {
    path: '/assets/domain',
    name: 'assets-domain',
    component: () => import('../pages/assets/AssetCenter.vue'),
    meta: {
      ...authMeta('assets', '域名'),
      pluginType: 'asset_cmdb_domain',
      permission: 'assets.records.view',
      layoutFlat: true
    }
  },
  {
    path: '/assets/zabbix',
    name: 'assets-zabbix',
    component: () => import('../pages/assets/AssetCenter.vue'),
    meta: {
      ...authMeta('assets', 'Zabbix 主机'),
      pluginType: 'asset_zabbix_host',
      permission: 'assets.records.view',
      layoutFlat: true
    }
  },
  {
    path: '/assets/ipmp',
    name: 'assets-ipmp',
    component: () => import('../pages/assets/AssetCenter.vue'),
    meta: {
      ...authMeta('assets', 'IPMP 项目'),
      pluginType: 'asset_ipmp_project',
      permission: 'assets.records.view',
      layoutFlat: true
    }
  },
  {
    path: '/assets/workorder-hosts',
    name: 'assets-workorder-hosts',
    component: () => import('../pages/assets/AssetCenter.vue'),
    meta: {
      ...authMeta('assets', '工单纳管主机信息'),
      pluginType: 'asset_workorder_host',
      permission: 'assets.records.view',
      layoutFlat: true
    }
  },
  {
    path: '/tools/library',
    name: 'tools-library',
    component: () => import('../pages/tools/ToolLibrary.vue'),
    meta: { ...authMeta('tools', '运维工具'), permission: 'tools.library.view' }
  },
  {
    path: '/tools/ip-regex',
    name: 'tools-ip-regex',
    component: () => import('../pages/tools/IpRegexHelper.vue'),
    meta: {
      ...authMeta('tools', 'IP 正则助手'),
      permission: 'tools.library.view',
      scriptPlugin: 'ip-regex-helper',
      layoutFlat: true
    }
  },
  {
    path: '/tools/account-sync',
    name: 'tools-account-sync',
    component: () => import('../pages/tools/AccountSync.vue'),
    meta: {
      ...authMeta('tools', '账号同步'),
      permission: 'tools.library.view',
      scriptPlugin: 'account-sync',
      layoutFlat: true
    }
  },
  {
    path: '/tools/grafana-sync',
    name: 'tools-grafana-sync',
    component: () => import('../pages/tools/GrafanaSync.vue'),
    meta: {
      ...authMeta('tools', 'Grafana 同步'),
      permission: 'tools.library.view',
      scriptPlugin: 'grafana-sync',
      layoutFlat: true
    }
  },
  {
    path: '/code/repository/:directoryKey?',
    name: 'code-repository',
    component: () => import('../pages/tools/CodeRepository.vue'),
    meta: {
      ...authMeta('code', '代码管理'),
      layoutFlat: true,
      hideSideNav: true,
      permission: 'tools.repository.view'
    }
  },
  {
    path: '/integrations/:groupKey?',
    name: 'integrations-hub',
    component: () => import('../pages/integrations/IntegrationHub.vue'),
    meta: {
      ...authMeta('integrations', '插件中心'),
      layoutFlat: true,
      permission: 'integrations.hub.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/probes/nodes',
    name: 'probes-nodes',
    component: () => import('../pages/probes/ProbeManager.vue'),
    meta: {
      ...authMeta('probes', '节点'),
      permission: 'probes.nodes.view',
      contentPadding: '0 16px 16px',
      layoutFlat: true
    }
  },
  {
    path: '/probes/schedules',
    name: 'probes-schedules',
    component: () => import('../pages/probes/ProbeSchedules.vue'),
    meta: {
      ...authMeta('probes', '调度'),
      permission: 'detection.schedules.view',
      contentPadding: '0 16px 16px',
      layoutFlat: true
    }
  },
  {
    path: '/probes/logs',
    name: 'probes-logs',
    component: () => import('../pages/monitoring/MonitoringHistory.vue'),
    meta: {
      ...authMeta('probes', '日志'),
      permission: 'detection.schedules.view',
      contentPadding: '0 16px 16px',
      layoutFlat: true
    }
  },
  {
    path: '/knowledge',
    name: 'knowledge-center',
    component: () => import('../pages/knowledge/KnowledgeCenter.vue'),
    meta: {
      ...authMeta('knowledge', '知识库'),
      layoutFlat: true,
      hideSideNav: true,
      permission: 'knowledge.articles.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/knowledge/view/:slug',
    name: 'knowledge-view',
    component: () => import('../pages/knowledge/KnowledgeArticleView.vue'),
    meta: {
      ...authMeta('knowledge', '知识库'),
      layoutFlat: true,
      hideSideNav: true,
      permission: 'knowledge.articles.view'
    }
  },
  {
    path: '/settings/users',
    name: 'settings-users',
    component: () => import('../pages/settings/Users.vue'),
    meta: {
      ...authMeta('settings', '用户'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.users.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/permissions',
    name: 'settings-permissions',
    component: () => import('../pages/settings/Permissions.vue'),
    meta: {
      ...authMeta('settings', '权限'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.roles.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/permissions/new',
    name: 'settings-permissions-new',
    component: () => import('../pages/settings/PermissionRoleDetail.vue'),
    meta: {
      ...authMeta('settings', '权限'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.roles.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/permissions/:roleId',
    name: 'settings-permissions-detail',
    component: () => import('../pages/settings/PermissionRoleDetail.vue'),
    meta: {
      ...authMeta('settings', '权限'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.roles.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/logs',
    name: 'settings-logs',
    component: () => import('../pages/settings/AuditLogViewer.vue'),
    meta: {
      ...authMeta('settings', '日志'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.audit_log.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/theme',
    name: 'settings-theme',
    component: () => import('../pages/settings/Theme.vue'),
    meta: { ...authMeta('settings', '主题'), permission: 'settings.system.view' }
  },
  {
    path: '/settings/system',
    name: 'settings-system',
    component: () => import('../pages/settings/SystemSettings.vue'),
    meta: {
      ...authMeta('settings', '全局设置'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.system.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/alerts',
    name: 'settings-alerts',
    component: () => import('../pages/settings/Alerts.vue'),
    meta: {
      ...authMeta('settings', '告警'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'alerts.channels.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/alerts/templates',
    name: 'settings-alert-templates',
    component: () => import('../pages/settings/AlertTemplates.vue'),
    meta: {
      ...authMeta('settings', '告警'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'alerts.channels.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/alerts/:type',
    name: 'settings-alert-channel',
    component: () => import('../pages/settings/AlertChannelDetail.vue'),
    meta: {
      ...authMeta('settings', '告警'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'alerts.channels.view',
      contentPadding: '0 16px 16px'
    }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

function resolveRouteTitle(meta: Record<string, unknown>) {
  const explicitTitle = typeof meta.title === 'string' ? meta.title : '';
  if (explicitTitle) return explicitTitle;

  const navGroup = typeof meta.navGroup === 'string' ? meta.navGroup : '';
  const navLabel = typeof meta.navLabel === 'string' ? meta.navLabel : '';
  const groupLabel = navGroup ? NAV_GROUPS.find((group) => group.key === navGroup)?.label ?? '' : '';

  if (groupLabel && navLabel) {
    return groupLabel === navLabel ? groupLabel : `${groupLabel} - ${navLabel}`;
  }

  return navLabel || groupLabel;
}

router.beforeEach(async (to, from, next) => {
  const session = useSessionStore();
  if (!to.meta?.requiresAuth) return next();

  if (!session.isAuthenticated) {
    return next({ path: '/login', query: { redirect: to.fullPath } });
  }

  if (!session.user) {
    try {
      await session.fetchProfile();
    } catch {
      if (!session.isAuthenticated) {
        ElMessage.warning('登录已过期，请重新登录');
        return next({ path: '/login', query: { redirect: to.fullPath } });
      }
      ElMessage.error('无法获取用户信息，请检查网络后重试');
      return next(false);
    }
  }

  const modulePermission = to.meta?.modulePermission as string | undefined;
  if (modulePermission && !session.hasPermission(modulePermission)) {
    try {
      await session.fetchProfile();
    } catch {
      // 网络/服务异常：保留当前页面，不误判为无权限
      ElMessage.error('无法校验权限，请检查网络后重试');
      return next(false);
    }
    if (to.path !== '/403') {
      ElMessage.error('当前账号暂无访问权限');
    }
    return next({ path: '/403' });
  }

  const permission = to.meta?.permission as string | undefined;
  if (permission && !session.hasPermission(permission)) {
    try {
      await session.fetchProfile();
    } catch {
      ElMessage.error('无法校验权限，请检查网络后重试');
      return next(false);
    }
    if (to.path !== '/403') {
      ElMessage.error('当前账号暂无访问权限');
    }
    return next({ path: '/403' });
  }

  return next();
});

router.afterEach((to) => {
  if (typeof document === 'undefined') return;
  const title = resolveRouteTitle(to.meta as Record<string, unknown>);
  if (!title) return;

  const branding = useBrandingStore();
  const base = branding.platformName || String(i18n.global.t('common.appName') || '').trim() || '多维运维平台';
  document.title = `${title} · ${base}`;
});

export default router;
