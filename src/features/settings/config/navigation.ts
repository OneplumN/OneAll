export interface SettingsPrimaryNavItem {
  label: string;
  path: string;
  permission?: string;
  activePaths?: string[];
  targets?: Array<{
    path: string;
    permission?: string;
  }>;
}

export interface SettingsSecondaryNavItem {
  label: string;
  path: string;
  permission?: string;
  activePaths?: string[];
}

export const SETTINGS_PRIMARY_NAV_ITEMS: SettingsPrimaryNavItem[] = [
  {
    label: '平台配置',
    path: '/settings/platform',
    activePaths: ['/settings/platform'],
    targets: [
      { path: '/settings/platform', permission: 'settings.system.view' },
    ],
  },
  {
    label: '用户与权限',
    path: '/settings/users',
    activePaths: ['/settings/users', '/settings/permissions', '/settings/logs'],
    targets: [
      { path: '/settings/users', permission: 'settings.users.view' },
      { path: '/settings/permissions', permission: 'settings.roles.view' },
      { path: '/settings/logs', permission: 'settings.audit_log.view' },
    ],
  },
  {
    label: '通知管理',
    path: '/settings/notifications',
    activePaths: ['/settings/notifications', '/settings/notifications/templates'],
    targets: [
      { path: '/settings/notifications', permission: 'alerts.channels.view' },
      { path: '/settings/notifications/templates', permission: 'alerts.channels.view' },
    ],
  },
  {
    label: '认证接入',
    path: '/settings/auth',
    activePaths: ['/settings/auth'],
    targets: [
      { path: '/settings/auth', permission: 'settings.system.view' },
    ],
  },
];

export const SETTINGS_SECONDARY_NAV_ITEMS: Record<string, SettingsSecondaryNavItem[]> = {
  用户与权限: [
    {
      label: '用户管理',
      path: '/settings/users',
      permission: 'settings.users.view',
      activePaths: ['/settings/users'],
    },
    {
      label: '角色模板',
      path: '/settings/permissions',
      permission: 'settings.roles.view',
      activePaths: ['/settings/permissions'],
    },
    {
      label: '审计日志',
      path: '/settings/logs',
      permission: 'settings.audit_log.view',
      activePaths: ['/settings/logs'],
    },
  ],
  通知管理: [
    {
      label: '通知渠道',
      path: '/settings/notifications',
      permission: 'alerts.channels.view',
      activePaths: ['/settings/notifications'],
    },
    {
      label: '通知模板',
      path: '/settings/notifications/templates',
      permission: 'alerts.channels.view',
      activePaths: ['/settings/notifications/templates'],
    },
  ],
};
