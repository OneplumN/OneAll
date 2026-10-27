import assert from 'node:assert/strict';
import test from 'node:test';

import {
  apiV1Endpoints,
  canTransitionProbe,
  classifyProbeStatus,
  domainEventTypes,
  getEndpoint,
  migrationPhases,
  normalizeLegacyApiPath,
  probeLifecyclePolicy,
  validateDomainEvent
} from '../src/platformContracts.ts';

test('API v1 contract uses versioned business endpoints', () => {
  assert.ok(apiV1Endpoints.length > 30);
  assert.equal(apiV1Endpoints.every((endpoint) => endpoint.path.startsWith('/api/v1/')), true);
  assert.equal(new Set(apiV1Endpoints.map((endpoint) => endpoint.key)).size, apiV1Endpoints.length);
  assert.equal(getEndpoint('tools.ipRegex.compile')?.path, '/api/v1/tools/ip-regex/compile');
  assert.equal(getEndpoint('probes.tasks.claim')?.method, 'POST');
  assert.equal(getEndpoint('probes.nodes.health')?.path, '/api/v1/probes/nodes/health');
  assert.equal(getEndpoint('probes.nodes.metricsHistory')?.path, '/api/v1/probes/nodes/{id}/metrics/history');
  assert.equal(getEndpoint('probes.nodes.retire')?.path, '/api/v1/probes/nodes/{id}/retire');
  assert.equal(getEndpoint('probes.config.refresh')?.method, 'POST');
  assert.equal(getEndpoint('probes.config.rollback')?.path, '/api/v1/probes/nodes/{id}/config/rollback');
});

test('legacy API paths normalize toward the v1 target contract', () => {
  assert.equal(normalizeLegacyApiPath('/api/tools/ip-regex/compile'), '/api/v1/tools/ip-regex/compile');
  assert.equal(normalizeLegacyApiPath('/api/alerts/checks'), '/api/v1/monitoring/strategies');
  assert.equal(normalizeLegacyApiPath('/api/monitoring/requests/{id}/approve'), '/api/v1/workorders/requests/{id}/approve');
  assert.equal(getEndpoint('search.global'), undefined);
});

test('probe lifecycle follows heartbeat and retirement rules', () => {
  assert.equal(probeLifecyclePolicy.heartbeatIntervalSeconds, 30);
  assert.equal(canTransitionProbe('registered', 'online'), true);
  assert.equal(canTransitionProbe('online', 'retired'), true);
  assert.equal(canTransitionProbe('retired', 'online'), false);
  assert.equal(classifyProbeStatus(10), 'online');
  assert.equal(classifyProbeStatus(60), 'degraded');
  assert.equal(classifyProbeStatus(301), 'offline');
  assert.equal(classifyProbeStatus(10, true), 'degraded');
});

test('domain events use the required envelope and known event types', () => {
  assert.deepEqual(domainEventTypes, [
    'asset.sync.started',
    'asset.sync.completed',
    'asset.sync.failed',
    'monitoring.strategy.enabled',
    'probe.result.received',
    'alert.event.created',
    'workorder.completed'
  ]);

  const event = {
    event_id: 'evt_001',
    trace_id: 'trc_001',
    event_type: 'probe.result.received',
    producer: 'probes',
    payload: { execution_id: 'exec_1' },
    created_at: '2026-05-26T09:30:00+08:00'
  };

  assert.deepEqual(validateDomainEvent(event).errors, []);
  assert.match(validateDomainEvent({ ...event, event_type: 'unknown.event', created_at: 'bad-time' }).errors.join('\n'), /event_type 不支持/);
});

test('migration contract keeps phased rollout and delayed target writes', () => {
  assert.equal(migrationPhases.length, 6);
  assert.equal(migrationPhases[0].writeMode, 'legacy');
  assert.equal(migrationPhases[4].writeMode, 'target');
  assert.match(migrationPhases[2].requiredGate, /断点续跑/);
  assert.match(migrationPhases[5].requiredGate, /迁移验收/);
});
