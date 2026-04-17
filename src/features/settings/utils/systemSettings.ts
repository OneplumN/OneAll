import type {
  IntegrationsForm,
  IntegrationsPayload,
  LDAPIntegration,
  SystemSettingsForm,
} from '@/features/settings/api/settingsApi';

const defaultLdap = (): LDAPIntegration => ({
  enabled: false,
  host: '',
  port: 389,
  use_ssl: false,
  base_dn: '',
  bind_dn: '',
  bind_password: '',
  has_bind_password: false,
  user_filter: '(uid={username})',
  username_attr: 'uid',
  display_name_attr: 'cn',
  email_attr: 'mail',
  sync_filter: '(uid=*)',
  sync_size_limit: null,
  default_role_ids: [],
});

export const createDefaultSystemSettings = (): SystemSettingsForm => ({
  platform_name: '多维运维平台',
  platform_logo: '',
  default_timezone: 'Asia/Shanghai',
  alert_escalation_threshold: 60,
  theme: 'light',
  notification_channels: {
    email: 'ops@example.com',
    webhook: '',
  },
  integrations: {
    ldap: defaultLdap(),
    assets: {
      types: {},
    },
  },
});

export const assignSystemSettings = (target: SystemSettingsForm, data: Partial<SystemSettingsForm>) => {
  if (data.platform_name !== undefined) target.platform_name = data.platform_name;
  if (data.platform_logo !== undefined) target.platform_logo = data.platform_logo || '';
  if (data.default_timezone !== undefined) target.default_timezone = data.default_timezone;
  if (data.alert_escalation_threshold !== undefined) {
    target.alert_escalation_threshold = data.alert_escalation_threshold;
  }
  if (data.theme !== undefined) target.theme = data.theme;
  if (data.notification_channels) {
    target.notification_channels.email = data.notification_channels.email ?? '';
    target.notification_channels.webhook = data.notification_channels.webhook ?? '';
  }
  if (data.integrations) {
    assignIntegrations(target.integrations, data.integrations);
  }
};

export const assignIntegrations = (target: IntegrationsForm, payload: Partial<IntegrationsForm>) => {
  if (payload.ldap) {
    const source = payload.ldap;
    target.ldap.enabled = Boolean(source.enabled);
    target.ldap.host = source.host ?? '';
    target.ldap.port = Number(source.port ?? target.ldap.port ?? 389);
    target.ldap.use_ssl = Boolean(source.use_ssl);
    target.ldap.base_dn = source.base_dn ?? '';
    target.ldap.bind_dn = source.bind_dn ?? '';
    target.ldap.has_bind_password = Boolean(source.has_bind_password);
    target.ldap.bind_password = '';
    target.ldap.user_filter = source.user_filter ?? '(uid={username})';
    target.ldap.username_attr = source.username_attr ?? 'uid';
    target.ldap.display_name_attr = source.display_name_attr ?? 'cn';
    target.ldap.email_attr = source.email_attr ?? 'mail';
    target.ldap.sync_filter = source.sync_filter ?? '(uid=*)';
    const limit = source.sync_size_limit;
    target.ldap.sync_size_limit = typeof limit === 'number' ? limit : limit ? Number(limit) : null;
    target.ldap.default_role_ids = source.default_role_ids ?? [];
  }

  if (payload.assets) {
    if (!target.assets) {
      target.assets = { types: {} };
    }
    const source = payload.assets;
    if (source.types && typeof source.types === 'object') {
      target.assets.types = {
        ...(target.assets.types || {}),
        ...source.types,
      };
    }
  }
};

export const buildIntegrationsPayload = (integrations: IntegrationsForm): IntegrationsPayload => {
  const ldap = integrations.ldap;
  const payload: IntegrationsPayload = {
    ldap: {
      enabled: ldap.enabled,
      host: ldap.host,
      port: ldap.port,
      use_ssl: ldap.use_ssl,
      base_dn: ldap.base_dn,
      bind_dn: ldap.bind_dn,
      user_filter: ldap.user_filter,
      username_attr: ldap.username_attr,
      display_name_attr: ldap.display_name_attr,
      email_attr: ldap.email_attr,
      sync_filter: ldap.sync_filter,
      default_role_ids: ldap.default_role_ids,
    },
  };

  if (typeof ldap.sync_size_limit === 'number') {
    payload.ldap.sync_size_limit = ldap.sync_size_limit;
  }

  if (ldap.bind_password) {
    payload.ldap.bind_password = ldap.bind_password;
  }

  const assets = integrations.assets;
  if (assets?.types) {
    const nextTypes: NonNullable<IntegrationsPayload['assets']>['types'] = {};
    Object.entries(assets.types).forEach(([key, value]) => {
      if (!value) return;
      const cleanedUnique = (value.unique_fields || [])
        .map((item) => String(item).trim())
        .filter((item) => item.length > 0);
      const cleanedExtras = (value.extra_fields || []).filter(
        (field) => field && String(field.key || '').trim().length > 0
      );
      if (!cleanedUnique.length && !cleanedExtras.length) {
        return;
      }
      nextTypes[key] = {
        ...(cleanedUnique.length ? { unique_fields: cleanedUnique } : {}),
        ...(cleanedExtras.length ? { extra_fields: cleanedExtras } : {}),
      };
    });
    if (Object.keys(nextTypes).length > 0) {
      payload.assets = { types: nextTypes };
    }
  }

  return payload;
};
