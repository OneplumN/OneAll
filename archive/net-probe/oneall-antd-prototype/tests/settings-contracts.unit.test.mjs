import assert from 'node:assert/strict';
import test from 'node:test';

import {
  canReferenceCredential,
  dataSourceDefinitions,
  maskCredential,
  notificationChannels,
  notificationTemplates,
  supportsNotificationEvent,
  validateTemplateVariables
} from '../src/settingsContracts.ts';

test('data source definitions keep credentials separate from sources', () => {
  assert.equal(dataSourceDefinitions.some((item) => item.type === 'blueking_cmdb'), true);
  assert.equal(canReferenceCredential('blueking_cmdb', 'token'), true);
  assert.equal(canReferenceCredential('blueking_cmdb', 'password'), false);
  assert.equal(canReferenceCredential('ldap', 'password'), true);
});

test('credential records are masked before presentation', () => {
  const safe = maskCredential({ id: 'cred_1', name: 'prod-token', type: 'token', owner: 'PlatformAdmin', secret: 'real-secret' });

  assert.equal('secret' in safe, false);
  assert.equal(safe.masked_secret, '******');
});

test('notification channels distinguish human and system targets', () => {
  const webhook = notificationChannels.find((item) => item.type === 'webhook');
  const site = notificationChannels.find((item) => item.type === 'site');

  assert.equal(webhook?.target, 'system');
  assert.equal(site?.target, 'person');
  assert.equal(supportsNotificationEvent('webhook', 'probe.result.received'), true);
  assert.equal(supportsNotificationEvent('wechat_work', 'probe.result.received'), false);
});

test('notification templates validate required payload variables', () => {
  const template = notificationTemplates.find((item) => item.key === 'asset-sync-failed');

  assert.ok(template);
  assert.deepEqual(validateTemplateVariables(template, { source_name: 'CMDB', failed_count: 3, trace_id: 'trc_1' }), {
    valid: true,
    missing: []
  });
  assert.deepEqual(validateTemplateVariables(template, { source_name: 'CMDB' }), {
    valid: false,
    missing: ['failed_count', 'trace_id']
  });
});
