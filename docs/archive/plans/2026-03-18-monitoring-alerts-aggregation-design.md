# Monitoring Alerts Aggregation Design (Window-Based)

**Date:** 2026-03-18

**Context**

OneAll v2 将告警作为独立领域，监控探针/任务只负责执行检测和记录结果。为了避免“每次失败都告警”的噪音，本设计定义一套简单的窗口聚合规则：在短时间窗口内连续失败达到一定次数时才触发告警事件，并通过现有的 `apps.alerts` 模块统一管理。

---

## Aggregation Rule

- 聚合维度：以“监控任务/探针”为主（即同一监控任务 ID 或探针 ID）。
- 时间窗口：最近 **3 分钟**。
- 失败阈值：窗口内失败次数 **≥ 2 次** 才触发告警。
- 触发时机：每次监控任务/探针执行完成写入监控历史之后，立即对该任务在窗口内的结果做一次统计。
- 窗口内去重：
  - 对于同一监控任务，在 3 分钟窗口内最多只生成 **1 条**告警事件。
  - 如果窗口内已经存在来源为 `monitoring` 且 `related_task_id` 为该任务的告警事件，则本次不再新建。

---

## Mapping to Alerts Domain

当某个监控任务/探针在 3 分钟窗口内失败次数达到阈值（≥ 2 次）时，在监控服务中构造一个 `CheckResult`，并调用 `apps.alerts.services.evaluate_and_raise(result)` 创建告警事件：

- `CheckResult` 字段约定：
  - `source`: `"monitoring"`
  - `event_type`: `"monitoring_check_failed_aggregated"`
  - `severity`: `"critical"`（第一版统一使用高等级，后续可以按规则细化）
  - `title`: 例如 `"监控任务连续失败告警"`
  - `message`: 例如：`"任务 <任务名称> 在过去 3 分钟内失败了 2 次（最近一次失败时间：<timestamp>）"`
  - `status`: 统一为 `"failed"`（表示聚合后的结果为失败）
  - `task_id`: 当前监控任务 ID
  - `asset_id` / `probe_id`: 若监控上下文中有对应 ID，则一并填入
  - `context`: 包含结构化信息：
    - `{"window_minutes": 3, "failure_threshold": 2, "failure_count": <int>, "last_failure_reason": "...", "target": "...", "last_failure_at": "..."}`

- `AlertEvent` 创建规则：
  - 使用以上 `CheckResult` 调用 `evaluate_and_raise`，生成一条 `AlertEvent`，初始状态为 `pending`。
  - 由 `apps.alerts.tasks.dispatch_alert_event` 异步任务完成后续状态更新（当前为 no-op，直接标记为 `sent`，后续可扩展为实际发送通道）。

---

## Placement in Monitoring Flow

1. 监控任务/探针执行完成后，按现有流程写入监控历史/结果表。
2. 在同一服务中，基于当前任务 ID：
   - 查询最近 3 分钟内该任务所有执行结果。
   - 统计失败次数（例如状态为 `failed` 的记录数）。
3. 若失败次数 `< 2`，则不触发任何告警，直接返回。
4. 若失败次数 `≥ 2`：
   - 查询 `AlertEvent` 表中最近 3 分钟内 `source="monitoring"` 且 `related_task_id=当前任务` 的事件。
   - 如果已经存在，则认为当前窗口已告警过，跳过创建。
   - 否则根据最新失败结果构造 `CheckResult` 并调用 `evaluate_and_raise` 创建事件。
   - 可选：立即调用 `dispatch_alert_event.delay(str(event.id))` 将事件送入告警分发任务。

---

## Future Extensions

- 规则配置化：
  - 将窗口大小（分钟）和失败阈值从硬编码提升为可配置项（例如按任务/探针级别配置，或通过 `AlertRule` 进行管理）。
- 多维度聚合：
  - 除按任务聚合外，支持按资产、按探针类型等维度定义规则。
- 告警抑制与恢复通知：
  - 增加“恢复”事件类型，在任务从多次失败恢复为连续成功后，发送恢复告警。
  - 支持静默期（snooze），避免同一问题短时间内重复告警。

