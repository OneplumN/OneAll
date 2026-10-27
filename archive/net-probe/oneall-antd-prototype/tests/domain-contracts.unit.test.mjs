import assert from 'node:assert/strict';
import test from 'node:test';

import {
  canTransitionWorkorder,
  evaluateAlertCondition,
  getWorkorderTabs,
  hasPermission,
  previewAlertRule,
  validateAlertRuleDsl,
  workorderStatusMeta
} from '../src/domainContracts.ts';

const validRule = {
  scope: {
    asset_model: 'pay_domain_service',
    asset_filter: { environment: 'prod' }
  },
  signal: {
    metric: 'http_status',
    source: 'probe_result'
  },
  condition: {
    operator: 'not_in',
    value: [200, 301, 302],
    duration: '3m',
    consecutive: 3
  },
  severity: 'critical',
  recovery: {
    operator: 'in',
    value: [200, 301, 302],
    consecutive: 2
  },
  actions: {
    notify_channels: ['site', 'webhook'],
    create_workorder: false
  }
};

test('permission matrix follows role action boundaries', () => {
  assert.equal(hasPermission('PlatformAdmin', 'usersAndRoles', 'update'), true);
  assert.equal(hasPermission('OpsEngineer', 'usersAndRoles', 'update'), false);
  assert.equal(hasPermission('OpsAdmin', 'assetCenter', 'sync'), true);
  assert.equal(hasPermission('OpsEngineer', 'workorders', 'read'), true);
  assert.equal(hasPermission('OpsEngineer', 'oneOffDetection', 'read'), true);
  assert.equal(hasPermission('Viewer', 'credentials', 'read'), false);
});

test('workorder status machine allows only documented transitions', () => {
  assert.equal(canTransitionWorkorder('submitted', 'approved'), true);
  assert.equal(canTransitionWorkorder('submitted', 'rejected'), true);
  assert.equal(canTransitionWorkorder('submitted', 'completed'), false);
  assert.equal(canTransitionWorkorder('approved', 'canceled'), true);
  assert.deepEqual(workorderStatusMeta.executing.actions, ['更新进度', '标记失败', '完成']);
  assert.deepEqual(getWorkorderTabs(), ['全部', '我的申请', '我的审批', '工单详情']);
});

test('alert DSL validates required shape and supported operators', () => {
  assert.deepEqual(validateAlertRuleDsl(validRule).errors, []);

  const invalid = validateAlertRuleDsl({
    ...validRule,
    condition: { operator: 'between', value: [1, 2], duration: 'soon', consecutive: 0 },
    severity: 'fatal'
  });

  assert.equal(invalid.valid, false);
  assert.match(invalid.errors.join('\n'), /condition\.operator 不支持/);
  assert.match(invalid.errors.join('\n'), /condition\.duration/);
  assert.match(invalid.errors.join('\n'), /severity/);
});

test('alert DSL preview evaluates sample signals', () => {
  assert.equal(evaluateAlertCondition(500, validRule.condition), true);
  assert.equal(evaluateAlertCondition(200, validRule.condition), false);
  assert.deepEqual(previewAlertRule(validRule, { http_status: 500 }), {
    triggered: true,
    recovered: false,
    errors: []
  });
});
