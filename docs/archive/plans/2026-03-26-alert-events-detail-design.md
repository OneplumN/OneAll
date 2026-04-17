# Alert Events Detail Design

**Date:** 2026-03-26

**Context**

当前告警事件页已经具备列表与详情能力，但详情页仍然直接暴露 `context` 快照和原始上下文 JSON，更接近调试页，而不是面向值班人员的处理页。与此同时，后端 `AlertEvent.status` 的真实语义是“通知状态”，不是未来可能扩展的“告警处理状态”，前台文案需要与真实语义对齐。

---

## Product Definition

- 告警事件 = 某条监控策略触发的一次告警记录。
- 告警事件详情页 = 面向值班处理的结果页，不是后台日志页。
- `context` 继续在后端落库，作为内部快照和排障依据，但不直接暴露给前台用户。

---

## List View

列表页展示字段统一为：

- 告警级别
- 告警标题
- 监控策略
- 目标
- 通知状态
- 告警时间

交互规则：

- 点击整行进入详情页。
- 筛选项仅保留：
  - 告警级别
  - 通知状态
  - 关键词搜索
- 去掉来源筛选，弱化内部系统来源语义。

字段来源：

- 监控策略：优先取 `event.context.schedule_name`，缺失时展示 `未关联策略`
- 目标：优先取 `event.context.target`，缺失时展示 `未提供目标`
- 通知状态：直接使用 `AlertEvent.status`，前端文案统一解释为通知状态

---

## Detail View

详情页顶部只保留：

- 页面标题：`告警事件`
- 右上按钮：`返回列表`

不再显示：

- 原始上下文
- 响应耗时
- 调度时间
- 完成时间
- 事件类型
- 来源
- “主信息 / 内容信息”等额外分区标题

详情页内容按以下顺序展示：

1. 告警标题：`event.title`
2. 告警内容：`event.message`
3. 目标：`context.target`
4. 状态码：`context.status_code` 或 `context.response_status`
5. 监控策略：`context.schedule_name`
6. 关联探针：`context.probe_name`
7. 告警级别：`event.severity`
8. 通知状态：`event.status`
9. 连续失败次数：`context.threshold`，缺失时默认 `1`
10. 告警时间：`event.created_at`
11. 通知对象：`context.alert_contacts`
12. 通知发送时间：`event.sent_at`

布局规则：

- 告警标题、告警内容单独成行
- 其余字段使用“字段名：字段值”的双列文本布局
- 页面整体保持克制，不使用技术型 JSON 区块

---

## Semantic Rules

- `AlertEvent.status` 在前台统一命名为 `通知状态`
- 不再使用“状态”或“告警状态”来指代该字段，避免与未来的处置状态冲突
- 缺省值展示规则：
  - 监控策略：`未关联策略`
  - 目标：`未提供目标`
  - 关联探针：`未关联探针`
  - 通知对象：`未配置`
  - 状态码：`-`
  - 连续失败次数：`1`
  - 通知发送时间：`-`

---

## Future Follow-Up

- 为详情页补真正的单条接口 `GET /api/alerts/events/:id`
- 将“通知状态”和未来的“告警处理状态”拆成两个独立字段
- 如后续需要，可在后台管理或审计页中继续保留原始 `context` 快照查看能力
