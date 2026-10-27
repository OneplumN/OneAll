import assert from 'node:assert/strict';
import test from 'node:test';

import {
  canUseRedisFor,
  mustPersistInDatabase,
  shouldUseTimescaleFor,
  technicalArchitectureDecision,
  validateProbeRequestHeaders
} from '../src/technicalArchitecture.ts';

test('technical architecture confirms Go Gin target with staged migration', () => {
  assert.equal(technicalArchitectureDecision.backend.framework, 'go-gin');
  assert.match(technicalArchitectureDecision.backend.reason, /\/api\/v1/);
  assert.match(technicalArchitectureDecision.backend.migration, /不第一阶段/);
});

test('database and Timescale boundaries are explicit', () => {
  assert.equal(technicalArchitectureDecision.database.primary, 'postgresql');
  assert.match(technicalArchitectureDecision.database.jsonFields, /JSONB/);
  assert.equal(shouldUseTimescaleFor('探针指标历史'), true);
  assert.equal(shouldUseTimescaleFor('权限矩阵'), false);
});

test('Redis is bounded to coordination and delivery not source of truth', () => {
  assert.equal(canUseRedisFor('事件投递缓冲'), true);
  assert.equal(canUseRedisFor('资产记录主存储'), false);
  assert.equal(mustPersistInDatabase('资产记录主存储'), true);
  assert.equal(mustPersistInDatabase('长期审计日志'), true);
});

test('probe protocol requires identity token and trace header', () => {
  assert.deepEqual(validateProbeRequestHeaders({
    'x-oneall-probe-id': 'probe-sh-01',
    authorization: 'Bearer token',
    'x-oneall-trace-id': 'trc_001'
  }), { valid: true, errors: [] });

  const invalid = validateProbeRequestHeaders({ authorization: 'token' });
  assert.equal(invalid.valid, false);
  assert.match(invalid.errors.join('\n'), /x-oneall-probe-id/);
  assert.match(invalid.errors.join('\n'), /Bearer token/);
  assert.match(invalid.errors.join('\n'), /x-oneall-trace-id/);
});
