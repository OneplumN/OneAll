# Monitoring Overview System Aggregation Design

**Date:** 2026-03-27

**Context**

当前“拨测可视化”希望展示的是“系统级健康态势”，而不是零散的单域名结果。现有后端 `AlertCheck` 只保存 `target`，并没有“所属系统”字段；资产中心的 `CMDB 域名` 资产则已经具备 `domain` 与 `system_name`。如果继续让用户在监控策略里手工填写系统名称，会造成资产中心与监控策略两套系统归属，后续维护和告警联动都会漂移。

因此，这一轮设计的核心是：**资产中心继续作为系统归属的唯一来源，监控策略只负责保存目标与解析后的归属快照，拨测可视化按系统聚合展示。**

---

## Product Definition

- 监控策略：定义对某个目标执行何种监控检查，以及告警条件和通知方式。
- 域名资产：资产中心中 `cmdb-domain` 类型的资产，包含 `domain` 和 `system_name`。
- 拨测可视化：以“系统”为粒度的蜂窝态势图，每个六边形代表一个系统，不代表一个域名。
- 系统状态：由该系统下所有已关联策略的最新执行结果聚合得到。

---

## Source Of Truth

系统归属只认资产中心的 `CMDB 域名` 资产。

规则如下：

- 监控策略保存 `target`，不新增手工输入的 `system_name` 字段。
- 后端从 `target` 中解析出规范化域名。
- 用规范化域名去匹配资产中心中 `asset_type = cmdb-domain` 的资产记录。
- 匹配成功时，取资产的 `system_name` 作为监控策略的系统归属。

这样做的原因：

- 避免用户在资产中心和监控策略两处重复维护系统归属。
- 告警事件、拨测可视化、策略详情可以共用同一套解析结果。
- 后续如果要做“系统 -> 域名 -> 策略 -> 告警”的关联链路，不需要再做人工修正。

---

## Resolution Snapshot

为避免每次打开页面都去做运行时 join，监控策略需要保存一组解析快照字段：

- `resolved_domain`
- `resolved_system_name`
- `asset_record_id`
- `asset_match_status`

其中 `asset_match_status` 建议使用明确枚举：

- `matched`：已匹配资产，且拿到了 `system_name`
- `missing_system`：匹配到资产，但 `system_name` 为空
- `unmanaged`：未匹配到资产
- `invalid_target`：目标无法解析为域名

这些字段是“派生字段”，不能由前端直接手工编辑；它们由后端在策略创建、编辑、克隆、同步修复时自动计算。

---

## Target Parsing Rules

目标解析的目标不是做全协议治理，而是先稳定支持当前拨测场景。

本轮范围：

- 对 `HTTP` / `HTTPS` / `WS` / `WSS` / `CERTIFICATE` 类型目标，优先按 URL 解析 host。
- 对裸域名目标，直接按域名处理。
- 对 IP 或无法识别的字符串，标记为 `invalid_target`，不尝试关联系统。

规范化规则：

- 全部转小写
- 去掉 scheme
- 去掉 path / query / fragment
- 去掉尾部 `/`
- 如存在端口，仅保留 host 部分用于资产匹配

---

## Fallback Buckets

用户已确认，可视化不能因为资产不完善而“消失”数据，因此保留两个兜底桶：

- `未配置系统`：匹配到了域名资产，但 `system_name` 为空
- `未纳管域名`：监控策略目标无法匹配到域名资产

`invalid_target` 本轮也归入 `未纳管域名` 展示，但在详情里保留原始目标，方便排查策略配置问题。

---

## Aggregation Rules

蜂窝图按系统聚合，每个系统单元格展示该系统的最新拨测状态。

系统聚合规则：

- 只要该系统下任一域名的最新结果为异常，系统状态为红色
- 当该系统下所有域名的最新结果都正常时，系统状态为绿色
- 当该系统下没有可用最新结果时，系统状态为灰色

本轮不引入历史窗口，不计算趋势，不展示最近 5 分钟或 1 小时内的统计波动，统一按“当前最新状态”展示。

---

## Detail Interaction

主视图：

- 使用蜂窝 / 六边形布局
- 每个单元格展示：
  - 系统名称
  - 域名数量 / 异常数量摘要
  - 当前聚合状态颜色

点击某个系统后，在下方展示系统详情面板。

系统详情面板展示：

- 系统名称
- 总域名数
- 异常域名数
- 最近更新时间
- 域名明细表

域名明细表字段：

- 域名
- 监控策略
- 最新状态
- 状态码
- 响应时间
- 最近检测时间
- 最新错误
- 操作：详情

---

## API Design

后端新增一个聚合接口，直接返回蜂窝图所需结构，避免前端自行拼装：

- `GET /api/alerts/checks/system-overview`

建议返回结构：

- `systems`
  - `system_name`
  - `status`
  - `domain_count`
  - `abnormal_count`
  - `last_checked_at`
  - `matched_strategy_count`
- `items`
  - `system_name`
  - `resolved_domain`
  - `check_id`
  - `check_name`
  - `protocol`
  - `latest_status`
  - `status_code`
  - `response_time_ms`
  - `last_checked_at`
  - `latest_error`
  - `asset_match_status`

是否按系统拆成两级接口，本轮不强制；如果数据量不大，首版可以一个接口同时返回聚合和明细。

---

## Backend Update Triggers

解析快照需要在以下时机自动刷新：

- 新建监控策略
- 编辑监控策略目标
- 克隆监控策略
- 历史策略补数据脚本

如果资产中心中的域名资产后续被修改了 `system_name`，本轮不做实时反向联动；通过“批量重算解析快照”的管理命令或后台任务进行修复即可。

---

## Error Handling

- 无法解析目标：策略保存成功，但 `asset_match_status = invalid_target`
- 找不到资产：策略保存成功，但 `asset_match_status = unmanaged`
- 找到资产无系统：策略保存成功，但 `asset_match_status = missing_system`
- 聚合接口中若某策略没有执行记录，按灰色状态参与系统聚合

这几类情况都不是“策略配置失败”，因此不阻断策略保存，只影响系统归属与态势展示。

---

## Testing Scope

本轮测试重点：

- 域名解析与规范化
- 资产匹配命中 / 未命中 / 无系统名
- 系统状态聚合规则
- 聚合接口返回结构
- 前端蜂窝图与下钻详情交互

本轮不做：

- 资产变更后的实时反向刷新
- 历史趋势图
- 多维筛选和高级统计面板

---

## Deferred Follow-Up

- 资产变更后自动反向刷新监控策略归属
- 系统级时间窗口趋势
- 系统级 SLA / 成功率指标
- 从告警事件反查系统视图并联动定位
