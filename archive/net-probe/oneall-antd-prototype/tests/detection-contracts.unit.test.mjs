import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildDetectionRequest,
  extractTargetHost,
  normalizeProbeCapabilities,
  presentDetectionStatus,
  validateDetectionInput,
  validateProbeRegistration
} from '../src/detectionContracts.ts';

test('extracts target host from URLs and plain domains', () => {
  assert.equal(extractTargetHost('https://api.oneall.internal/health'), 'api.oneall.internal');
  assert.equal(extractTargetHost('www.oneall.internal:443'), 'www.oneall.internal');
});

test('validates probe registration fields', () => {
  assert.deepEqual(validateProbeRegistration({ name: '', region: '', networkType: '', ipAddress: '999.1.1.1', capabilities: [] }), [
    '探针名称必填',
    '区域必填',
    '网络类型必填',
    '至少选择一种探针能力',
    'IP 地址格式不合法'
  ]);
  assert.deepEqual(normalizeProbeCapabilities(['http', 'HTTP', ' dns ']), ['DNS', 'HTTP']);
});

test('validates detection input by detection kind', () => {
  assert.deepEqual(validateDetectionInput({ kind: 'http', target: 'api.oneall.internal', protocol: 'HTTPS', probes: [], timeoutSeconds: 10 }), ['请至少选择一个探针节点']);
  assert.deepEqual(validateDetectionInput({ kind: 'cmdb', target: 'api.oneall.internal' }), []);
  assert.deepEqual(validateDetectionInput({ kind: 'certificate', target: 'www.oneall.internal', probes: ['probe-sh-01'], port: 443, timeoutSeconds: 15 }), []);
});

test('builds normalized detection requests', () => {
  const request = buildDetectionRequest({ kind: 'certificate', target: 'https://www.oneall.internal', probes: ['probe-sh-01'], probe: 'probe-sh-01', port: 443, timeoutSeconds: 15 });

  assert.equal(request.type, 'certificate');
  assert.equal(request.protocol, 'CERTIFICATE');
  assert.equal(request.related_asset, 'www.oneall.internal');
  assert.equal(request.probe, 'probe-sh-01');
  assert.equal(presentDetectionStatus('success'), '成功');
});
