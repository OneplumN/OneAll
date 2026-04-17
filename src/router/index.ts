import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import { ElMessage } from 'element-plus';

import { i18n } from '@/i18n';
import { SETTINGS_PRIMARY_NAV_ITEMS } from '@/features/settings/config/navigation';
import { useSessionStore } from '@/app/stores/session';
import { useBrandingStore } from '@/app/stores/branding';

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
  activePaths?: string[];
  targets?: Array<{
    path: string;
    permission?: string;
  }>;
  children?: Array<{
    label: string;
    path: string;
    hidden?: boolean;
    pluginType?: string;
    permission?: string;
    activePaths?: string[];
  }>;
}

const GROUP_MODULE_PERMISSIONS: Record<string, string> = {
  monitoring: 'monitoring.module.access',
  oneoff: 'detection.module.access',
  request: 'detection.module.access',
  assets: 'assets.module.access',
  tools: 'tools.module.access',
  alerts: 'alerts.module.access',
  probes: 'probes.module.access',
  settings: 'settings.module.access'
};

export const NAV_GROUPS: NavGroupConfig[] = [
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
    key: 'assets',
    label: '资产中心',
    permission: GROUP_MODULE_PERMISSIONS.assets,
    items: [
      {
        label: '资产中心',
        path: '/assets/domain',
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
    key: 'alerts',
    label: '监控与告警',
    items: [
      {
        label: '拨测可视化',
        path: '/monitoring/overview',
        permission: 'monitoring.overview.view'
      },
      {
        label: '告警事件',
        path: '/alerts/events'
      },
      {
        label: '监控策略',
        path: '/alerts/checks'
      },
      {
        label: '节点',
        path: '/probes/nodes',
        permission: 'probes.nodes.view'
      },
      {
        label: '日志',
        path: '/probes/logs',
        permission: 'detection.schedules.view'
      }
    ]
  },
  {
    key: 'settings',
    label: '系统设置',
    permission: GROUP_MODULE_PERMISSIONS.settings,
    items: SETTINGS_PRIMARY_NAV_ITEMS
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
    component: () => import('../features/auth/pages/LoginPage.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('../features/errors/pages/ForbiddenPage.vue'),
    meta: { title: '无权限' }
  },
  {
    path: '/profile',
    name: 'user-profile',
    component: () => import('../features/profile/pages/UserProfilePage.vue'),
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
    redirect: '/monitoring/overview'
  },
  {
    path: '/monitoring/history',
    redirect: '/probes/logs'
  },
  {
    path: '/probes',
    redirect: '/probes/nodes'
  },
  {
    path: '/tools/code-repository',
    redirect: '/code/repository'
  },
  {
    path: '/assets',
    redirect: '/assets/domain'
  },
  {
    path: '/monitoring/overview',
    name: 'monitoring-overview',
    component: () => import('../features/dashboard/pages/HomeOverviewPage.vue'),
    meta: {
      requiresAuth: true,
      navGroup: 'alerts',
      navLabel: '拨测可视化',
      title: '监控与告警 - 拨测可视化',
      modulePermission: GROUP_MODULE_PERMISSIONS.monitoring,
      pluginType: 'monitoring_overview',
      permission: 'monitoring.overview.view',
      contentPadding: '0 0 16px'
    }
  },
  {
    path: '/monitoring/probes',
    name: 'monitoring-probes',
    redirect: '/probes/nodes'
  },
  {
    path: '/oneoff/domain',
    name: 'oneoff-domain',
    component: () => import('../features/detection/pages/OneOffDetectionPage.vue'),
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
    component: () => import('../features/detection/pages/CertificateDetectionPage.vue'),
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
    component: () => import('../features/detection/pages/CmdbDomainCheckPage.vue'),
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
    component: () => import('../features/monitoring/pages/MonitoringRequestFormPage.vue'),
    meta: {
      ...authMeta('request', '拨测监控申请'),
      permission: 'detection.schedules.view',
      layoutFlat: true,
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/assets/domain',
    name: 'assets-domain',
    component: () => import('../features/assets/pages/AssetCenterPage.vue'),
    meta: {
      ...authMeta('assets', '域名资产'),
      pluginType: 'asset_cmdb_domain',
      permission: 'assets.records.view',
      layoutFlat: true
    }
  },
  {
    path: '/assets/zabbix',
    name: 'assets-zabbix',
    component: () => import('../features/assets/pages/AssetCenterPage.vue'),
    meta: {
      ...authMeta('assets', 'Zabbix 主机资产'),
      pluginType: 'asset_zabbix_host',
      permission: 'assets.records.view',
      layoutFlat: true
    }
  },
  {
    path: '/assets/ipmp',
    name: 'assets-ipmp',
    component: () => import('../features/assets/pages/AssetCenterPage.vue'),
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
    component: () => import('../features/assets/pages/AssetCenterPage.vue'),
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
    component: () => import('../features/tools/pages/ToolLibraryPage.vue'),
    meta: { ...authMeta('tools', '运维工具'), permission: 'tools.library.view' }
  },
  {
    path: '/tools/ip-regex',
    name: 'tools-ip-regex',
    component: () => import('../features/tools/pages/IpRegexHelperPage.vue'),
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
    component: () => import('../features/tools/pages/AccountSyncPage.vue'),
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
    component: () => import('../features/tools/pages/GrafanaSyncPage.vue'),
    meta: {
      ...authMeta('tools', 'Grafana 同步'),
      permission: 'tools.library.view',
      scriptPlugin: 'grafana-sync',
      layoutFlat: true
    }
  },
  {
    path: '/alerts/events',
    name: 'alerts-events',
    component: () => import('../features/alerts/pages/AlertEvents.vue'),
    meta: {
      ...authMeta('alerts', '告警事件'),
      layoutFlat: true,
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/alerts/events/:eventId',
    name: 'alerts-event-detail',
    component: () => import('../features/alerts/pages/AlertEventDetail.vue'),
    meta: {
      ...authMeta('alerts', '告警事件'),
      layoutFlat: true,
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/alerts/checks',
    name: 'alerts-checks',
    component: () => import('../features/alerts/pages/AlertChecks.vue'),
    meta: {
      ...authMeta('alerts', '监控策略'),
      layoutFlat: true,
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/alerts/checks/:checkId',
    name: 'alerts-check-detail',
    component: () => import('../features/alerts/pages/AlertCheckDetail.vue'),
    meta: {
      ...authMeta('alerts', '监控策略'),
      layoutFlat: true,
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/code/repository/:directoryKey?',
    name: 'code-repository',
    component: () => import('../features/tools/pages/CodeRepositoryPage.vue'),
    meta: {
      ...authMeta('tools', '脚本仓库'),
      title: '运维工具 - 脚本仓库',
      layoutFlat: true,
      hideSideNav: true,
      permission: 'tools.repository.view'
    }
  },
  {
    path: '/probes/nodes',
    name: 'probes-nodes',
    component: () => import('../features/probes/pages/ProbeManagerPage.vue'),
    meta: {
      requiresAuth: true,
      navGroup: 'alerts',
      navLabel: '节点',
      modulePermission: GROUP_MODULE_PERMISSIONS.probes,
      permission: 'probes.nodes.view',
      contentPadding: '0 16px 16px',
      layoutFlat: true
    }
  },
  {
    path: '/probes/schedules',
    redirect: '/alerts/checks'
  },
  {
    path: '/probes/logs',
    name: 'probes-logs',
    component: () => import('../features/monitoring/pages/MonitoringHistoryPage.vue'),
    meta: {
      requiresAuth: true,
      navGroup: 'alerts',
      navLabel: '日志',
      modulePermission: GROUP_MODULE_PERMISSIONS.probes,
      permission: 'detection.schedules.view',
      contentPadding: '0 16px 16px',
      layoutFlat: true
    }
  },
  {
    path: '/settings/system',
    redirect: '/settings/platform'
  },
  {
    path: '/settings/alerts',
    redirect: '/settings/notifications'
  },
  {
    path: '/settings/users',
    name: 'settings-users',
    component: () => import('../features/settings/pages/Users.vue'),
    meta: {
      ...authMeta('settings', '用户与权限'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.users.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/permissions',
    name: 'settings-permissions',
    component: () => import('../features/settings/pages/Permissions.vue'),
    meta: {
      ...authMeta('settings', '用户与权限'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.roles.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/permissions/new',
    name: 'settings-permissions-new',
    component: () => import('../features/settings/pages/PermissionRoleDetail.vue'),
    meta: {
      ...authMeta('settings', '用户与权限'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.roles.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/permissions/:roleId',
    name: 'settings-permissions-detail',
    component: () => import('../features/settings/pages/PermissionRoleDetail.vue'),
    meta: {
      ...authMeta('settings', '用户与权限'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.roles.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/logs',
    name: 'settings-logs',
    component: () => import('../features/settings/pages/AuditLogViewer.vue'),
    meta: {
      ...authMeta('settings', '用户与权限'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.audit_log.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/platform',
    name: 'settings-platform',
    component: () => import('../features/settings/pages/SystemSettings.vue'),
    meta: {
      ...authMeta('settings', '平台配置'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.system.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/notifications',
    name: 'settings-notifications',
    component: () => import('../features/settings/pages/Alerts.vue'),
    meta: {
      ...authMeta('settings', '通知管理'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'alerts.channels.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/notifications/templates',
    name: 'settings-notification-templates',
    component: () => import('../features/settings/pages/AlertTemplates.vue'),
    meta: {
      ...authMeta('settings', '通知管理'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'alerts.channels.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/notifications/:type',
    name: 'settings-notification-channel',
    component: () => import('../features/settings/pages/AlertChannelDetail.vue'),
    meta: {
      ...authMeta('settings', '通知管理'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'alerts.channels.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/settings/auth',
    name: 'settings-auth',
    component: () => import('../features/settings/pages/AuthIntegration.vue'),
    meta: {
      ...authMeta('settings', '认证接入'),
      layoutFlat: true,
      lockMainScroll: true,
      permission: 'settings.system.view',
      contentPadding: '0 16px 16px'
    }
  },
  {
    path: '/assets/admin/models',
    name: 'assets-model-admin',
    component: () => import('../features/assets/pages/AssetModelAdminPage.vue'),
    meta: {
      ...authMeta('assets', '模型管理'),
      layoutFlat: true,
      contentPadding: '0 16px 16px',
      permission: 'assets.records.manage'
    }
  },
  {
    path: '/assets/admin/fields',
    name: 'assets-field-admin',
    component: () => import('../features/assets/pages/AssetFieldAdminPage.vue'),
    meta: {
      ...authMeta('assets', '字段管理'),
      layoutFlat: true,
      contentPadding: '0 16px 16px',
      permission: 'assets.records.manage'
    }
  },
  {
    path: '/assets/model/:modelKey',
    name: 'assets-model-generic',
    component: () => import('../features/assets/pages/AssetModelCenterPage.vue'),
    meta: {
      ...authMeta('assets', '扩展模型'),
      layoutFlat: true,
      permission: 'assets.records.view'
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
