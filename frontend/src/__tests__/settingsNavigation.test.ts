import { describe, expect, it } from 'vitest';

import { SETTINGS_PRIMARY_NAV_ITEMS } from '@/features/settings/config/navigation';
import { buildIntegrationsPayload, createDefaultSystemSettings } from '@/features/settings/utils/systemSettings';

describe('settings navigation config', () => {
  it('exposes the four primary system settings entries', () => {
    expect(SETTINGS_PRIMARY_NAV_ITEMS).toEqual([
      expect.objectContaining({ label: '平台配置', path: '/settings/platform' }),
      expect.objectContaining({ label: '用户与权限', path: '/settings/users' }),
      expect.objectContaining({ label: '通知管理', path: '/settings/notifications' }),
      expect.objectContaining({ label: '认证接入', path: '/settings/auth' }),
    ]);
  });
});

describe('system settings payload helper', () => {
  it('preserves ldap values and omits empty asset type overrides', () => {
    const settings = createDefaultSystemSettings();
    settings.integrations.ldap.enabled = true;
    settings.integrations.ldap.host = 'ldap.example.com';
    settings.integrations.ldap.bind_password = 'secret';
    settings.integrations.assets = {
      types: {
        domain: {
          unique_fields: ['domain_name', '  '],
        },
        empty: {
          unique_fields: [],
          extra_fields: [],
        },
      },
    };

    const payload = buildIntegrationsPayload(settings.integrations);

    expect(payload.ldap).toMatchObject({
      enabled: true,
      host: 'ldap.example.com',
      bind_password: 'secret',
    });
    expect(payload.assets?.types).toEqual({
      domain: {
        unique_fields: ['domain_name'],
      },
    });
  });
});
