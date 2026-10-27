import assert from 'node:assert/strict';
import test from 'node:test';

import { readFileSync } from 'node:fs';

import { apiV1Endpoints, domainEventTypes } from '../src/platformContracts.ts';
import { routeRegistry } from '../src/navigationContract.ts';
import { notificationChannels, notificationTemplates } from '../src/settingsContracts.ts';

const tasklist = readFileSync(new URL('../../oneall-redesign/05-tasklist.md', import.meta.url), 'utf8');

test('API contract covers routed product domains', () => {
  const requiredDomains = ['detection', 'workorders', 'assets', 'monitoring', 'alerts', 'probes', 'settings', 'tools'];
  const endpointDomains = new Set(apiV1Endpoints.map((endpoint) => endpoint.domain));

  for (const domain of requiredDomains) {
    assert.equal(endpointDomains.has(domain), true, `${domain} should have API endpoints`);
  }

  assert.equal(routeRegistry.some((route) => route.key === 'ip-regex'), true);
  assert.equal(apiV1Endpoints.some((endpoint) => endpoint.key === 'tools.ipRegex.compile'), true);
});

test('API contract keeps sensitive and integration operations explicit', () => {
  assert.equal(apiV1Endpoints.some((endpoint) => endpoint.key === 'settings.credentials.list'), true);
  assert.equal(apiV1Endpoints.some((endpoint) => endpoint.key === 'settings.webhooks.test'), true);
  assert.equal(apiV1Endpoints.some((endpoint) => endpoint.key === 'assets.sync.preview'), true);
  assert.equal(apiV1Endpoints.some((endpoint) => endpoint.key === 'probes.tasks.result'), true);
});

test('notification event contract covers cross-domain lifecycle events', () => {
  assert.equal(domainEventTypes.includes('asset.sync.failed'), true);
  assert.equal(domainEventTypes.includes('alert.event.created'), true);
  assert.equal(domainEventTypes.includes('workorder.completed'), true);
  assert.equal(domainEventTypes.includes('probe.result.received'), true);
  const knownEvents = new Set(domainEventTypes);
  for (const channel of notificationChannels) {
    assert.equal(channel.supportedEvents.every((event) => knownEvents.has(event)), true);
  }
  for (const template of notificationTemplates) {
    assert.equal(knownEvents.has(template.eventType), true);
  }
});

test('tasklist records platform contracts as confirmed', () => {
  assert.match(tasklist, /- \[x\] 确认 API v1 契约/);
  assert.match(tasklist, /- \[x\] 确认探针生命周期状态机/);
  assert.match(tasklist, /- \[x\] 确认通知事件列表/);
  assert.match(tasklist, /- \[x\] 确认数据迁移策略/);
});
