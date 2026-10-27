import assert from 'node:assert/strict';
import test from 'node:test';

import {
  getNavParentKey,
  getRouteByKey,
  isPageKey,
  navigationGroups,
  primaryModuleOrder,
  routeRegistry
} from '../src/navigationContract.ts';

test('navigation contract keeps business modules and a separate tools group', () => {
  assert.deepEqual(primaryModuleOrder, ['监控与告警', '资产中心', '一次性检验', '工单管理', '系统设置', '工具']);
  assert.deepEqual(navigationGroups.map((group) => group.title), primaryModuleOrder);
});

test('navigation contract exposes stable secondary pages', () => {
  const labelsByModule = Object.fromEntries(
    navigationGroups.map((group) => [group.title, group.items.map((item) => item.label)])
  );

  assert.deepEqual(labelsByModule['监控与告警'], ['监控总览', '告警事件', '监控策略', '探针节点', '执行日志']);
  assert.deepEqual(labelsByModule['资产中心'], ['模型资产', '模型管理', '同步任务']);
  assert.deepEqual(labelsByModule['一次性检验'], ['域名拨测', '证书检测', 'CMDB 域名校验', '检测记录']);
  assert.deepEqual(labelsByModule['工单管理'], ['申请工单', '我的申请', '我的审批']);
  assert.deepEqual(labelsByModule['系统设置'], ['平台参数', '用户与角色', '权限矩阵', '凭据管理', '数据源管理', '通知通道', '通知模板', '出站 Webhook', '审计日志', '数据保留策略']);
  assert.deepEqual(labelsByModule['工具'], ['IP 正则助手']);
});

test('route contract keeps IP regex under the tools group', () => {
  const ipRegex = getRouteByKey('ip-regex');

  assert.equal(ipRegex?.path, '/tools/ip-regex');
  assert.equal(ipRegex?.module, '工具');
  assert.equal(ipRegex?.nav, true);
  assert.equal(navigationGroups.find((group) => group.title === '工具')?.items.some((item) => item.key === 'ip-regex'), true);
});

test('route contract resolves known keys and detail parent navigation', () => {
  assert.equal(isPageKey('asset-detail'), true);
  assert.equal(isPageKey('unknown-page'), false);
  assert.equal(getNavParentKey('alert-detail'), 'alerts');
  assert.equal(getNavParentKey('asset-fields'), 'asset-detail');
  assert.equal(getRouteByKey('asset-model-management')?.path, '/assets/model-management');
  assert.equal(routeRegistry.some((route) => route.path === '/assets/models/:modelId/fields'), true);
});
