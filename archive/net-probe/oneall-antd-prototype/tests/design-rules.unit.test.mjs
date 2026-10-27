import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const productDoc = readFileSync(new URL('../../oneall-redesign/01-product-redesign.md', import.meta.url), 'utf8');
const domainDoc = readFileSync(new URL('../../oneall-redesign/03-domain-and-refactor-boundaries.md', import.meta.url), 'utf8');
const archiveDoc = readFileSync(new URL('../../oneall-redesign/07-archive-boundaries.md', import.meta.url), 'utf8');
const tasklistDoc = readFileSync(new URL('../../oneall-redesign/05-tasklist.md', import.meta.url), 'utf8');

test('asset center records user-created model decision', () => {
  assert.match(productDoc, /首版默认提供四个业务模型/);
  assert.match(productDoc, /CMDB 域名/);
  assert.match(productDoc, /Zabbix 主机/);
  assert.match(domainDoc, /模型驱动/);
  assert.match(domainDoc, /工单纳管主机信息/);
});

test('asset center IA keeps fixed asset models out of navigation', () => {
  const ia = productDoc.match(/## 5\. 资产中心设计[\s\S]*?## 6\./)?.[0] ?? '';

  assert.match(ia, /模型资产/);
  assert.match(ia, /新建模型/);
  assert.match(ia, /同步任务/);
  assert.match(ia, /只展示当前模型的实例数据/);
  assert.match(ia, /不恢复“全部资产、域名资产、主机资产、应用资产”等固定资产菜单/);
  assert.doesNotMatch(ia, /导入导出记录/);
  assert.doesNotMatch(ia, /├─ 全部资产|├─ 域名资产|├─ 主机资产|├─ 应用资产/);
});

test('IP regex helper is documented as a light tool instead of a primary module', () => {
  assert.match(productDoc, /运维工具不作为业务重模块保留/);
  assert.match(productDoc, /首版只保留独立“工具”分组/);
  assert.match(domainDoc, /IP 正则助手/);
});

test('legacy Vue prototypes are archived outside the redesign mainline', () => {
  assert.match(archiveDoc, /React \+ Ant Design 原型/);
  assert.match(archiveDoc, /不作为下一版设计基准/);
  assert.match(archiveDoc, /oneall-frontend-prototype/);
  assert.match(tasklistDoc, /- \[x\] 清理或归档误做的 Vue \+ Element Plus 原型/);
});

test('asset model data loop is recorded as completed', () => {
  assert.match(tasklistDoc, /- \[x\] 模型资产闭环：按模型加载实例、查看详情、字段搜索、空状态、禁止在数据页配置/);
  assert.match(tasklistDoc, /- \[x\] 资产同步闭环：目标模型选择、字段映射、预览、执行、历史、写回模型资产页/);
});

test('legacy business loops are recorded as completed for the prototype', () => {
  for (const item of [
    '资产同步失败恢复',
    '监控策略闭环',
    '告警事件闭环',
    '一次性检验闭环',
    '工单管理闭环',
    '探针节点闭环',
    '系统设置闭环'
  ]) {
    assert.equal(tasklistDoc.includes(`- [x] ${item}`), true);
  }
});
