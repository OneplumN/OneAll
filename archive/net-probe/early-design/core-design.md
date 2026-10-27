# 历史来源

原仓库：[OneplumN/One_All_In_Ai](https://github.com/OneplumN/One_All_In_Ai)

原文件：`docs/core-design.md`

归档时文件 SHA：`613de72febd4ab8ec2ea45746a450de477140205`

以下保留原设计草案，不代表功能已实现。

---

# One_All_In_Ai 核心设计（草案）

## 1. 平台定位

- 多机房 / 多探针的拨测 & 证书监控平台  
- 核心能力：
  - 探针与机房拓扑管理
  - 多元探测任务（HTTP / TCP / ICMP / 证书）
  - 告警策略与通知（支持多机房判定规则）

资产、知识库、运维工具、第三方集成都只做辅助，围绕上述三条主线服务。

---

## 2. 核心数据流（Task → Result → Alert）

1. 用户创建探测目标 `Target`（URL / IP / Domain 等）并打标签（系统、负责人、环境…）。
2. 用户为 Target 创建探测任务 `CheckTask`：
   - 协议类型（HTTP / TCP / ICMP / SSL_CERT …）
   - 频率 / 超时 / 重试策略
   - 探针范围（选中一个或多个 Region / ProbeNode）
3. 调度引擎周期性将 `CheckTask` 展开为 `CheckExecution`：
   - 某任务 + 某探针 + 某时间点。
4. 各机房探针 `ProbeNode` 拉取任务，执行检测并上报 `CheckResult`：
   - 状态（成功 / 失败）、耗时、错误信息、证书详情等。
5. 告警引擎按 `AlertPolicy` 对 `CheckResult` 做聚合判断：
   - 支持连续 N 次失败、至少 X 个 Region 同时失败、延迟超阈值等。
   - 生成 `AlertEvent`（触发 / 恢复）。
6. 告警路由 `AlertRoute` 将 `AlertEvent` 推送到 `NotificationChannel`：
   - 飞书、企业微信、邮件、自定义 Webhook 等，并记录 `NotificationLog`。

---

## 3. 后端模块划分（Django apps）

### 3.1 `accounts`

- 用户、角色、权限、（预留）租户/组织字段。  
- 提供：
  - 登录 / 认证 API（可先用 Session/JWT，后续考虑 SSO）
  - 简单角色模型：管理员 / 只读用户 / 运维值班等。

> TODO（后端专家）：  
> - 确认是否一版就支持多租户，还是先单租户预留字段。  
> - 确认认证方式（Session / JWT / SSO 规划）。

### 3.2 `probes`

- 模型：
  - `Region`：机房 / 区域（名称、代码、描述、标签：IDC/City/ISP 等）。
  - `ProbeNode`：所属 Region、状态（online/offline）、版本、最近心跳、标签、密钥/Token。
- API：
  - Region CRUD / 列表。
  - ProbeNode 注册 / 认证（探针首次接入）。
  - 心跳上报接口。
  - 节点查询接口（供前端展示）。

- 探针协议（最小版）：
  - `GET /api/probes/{id}/tasks`：探针拉取待执行任务。
  - `POST /api/probes/{id}/results`：探针上报执行结果。
  - `POST /api/probes/{id}/heartbeat`：心跳。

> TODO（后端专家）：  
> - 决定一版是否使用 gRPC，还是先全部走 HTTP。  
> - 决定探针认证机制（Token / TLS 证书等）。

### 3.3 `monitoring`

- 模型：
  - `Target`：探测对象（URL/IP/Domain）+ 标签（系统、负责人、环境）。
  - `CheckTask`：任务定义（协议类型、频率、超时、重试、绑定 Target、选中 Region/Probe 列表）。
  - `CheckExecution`：具体执行实例（任务 + ProbeNode + 计划时间 + 状态）。
  - `CheckResult`：执行结果（时间、耗时、状态码/错误、证书信息等）。

- 调度：
  - Celery Beat 周期性扫描 `CheckTask`，生成未来一段时间的 `CheckExecution`。
  - 执行任务派发给对应 Region/ProbeNode，由探针拉取。

- 证书监控：
  - 建议作为 `CheckTask.protocol = SSL_CERT` 的一种特殊类型，使用同一框架；
  - `CheckResult` 中扩展证书字段（过期时间、颁发者、链路完整性等）。

> TODO（后端专家）：  
> - 决定 `Target` 与 `CheckTask` 的关系（一个目标多任务、多种协议）。  
> - 决定 CheckResult 是否落 TimescaleDB / 先用 MySQL。

### 3.4 `alerts`

- 模型：
  - `AlertPolicy`：绑定一组 CheckTask / Target / 标签，定义触发条件：
    - 连续 N 次失败
    - 至少 X 个 Region 同时失败
    - 延迟大于阈值
  - `AlertEvent`：实际告警事件（状态、级别、受影响 Target/Probe/Region、首次/最近时间）。
  - `NotificationChannel`：告警通道配置（飞书、企业微信、邮件、Webhook）。
  - `AlertRoute`：将不同事件路由到不同 Channel（按 Target/标签/级别）。
  - `NotificationLog`：记录通知历史。

- 告警引擎：
  - 消费 `CheckResult` 或聚合后的指标流。
  - 根据 `AlertPolicy` 生成 / 更新 `AlertEvent`。
  - 调用 `NotificationChannel` 实际发送通知。

> TODO（后端专家）：  
> - 决定告警是否走异步流（Redis stream / Kafka），一版可先用 DB 轮询。  
> - 设计多 Region 判定逻辑的数据结构（避免 O(N²)）。

### 3.5 `extensions`（轻量扩展）

- 统一管理非核心扩展点：
  - 运维动作（对 Target/Probe 执行的 HTTP 调用 / 脚本触发）。
  - 自定义 Webhook 集成。
- 约束：
  - 所有扩展必须通过标准接口注册，不允许直接改核心 app。

> TODO（后端专家）：  
> - 定义最小的扩展点类型集合。  
> - 决定一版是否开放给用户自定义。

---

## 4. 前端模块划分（Vue 3）

### 4.1 `auth`

- 登录页（表单 + 错误提示）。  
- 登录成功后的 Session 存储 + 路由守卫。  
- 预留 SSO 按钮/入口（后续对接时使用）。

> TODO（前端专家）：  
> - 确认是否引入统一 UI 库（Element Plus）+ 设计规范。  
> - 确认认证状态管理方案（Pinia / localStorage 等）。

### 4.2 `probes`

- Region 列表页：
  - 卡片视图：各机房 Region 的在线节点数、状态、标签。
- ProbeNode 列表页：
  - 可按 Region、状态、标签过滤；支持搜索。  
- Probe 详情：
  - 单节点信息：状态、最近心跳、版本、所属 Region。  
  - 最近执行任务概览（失败/成功数量）。

> TODO（前端专家）：  
> - 确认是否需要「拓扑/地图」视图，还是先用表格 + 简单图表。

### 4.3 `monitoring`

- Target 列表：
  - 列出所有探测对象（URL/IP/Domain），支持按标签过滤。  
- CheckTask 列表：
  - 名称、协议、频率、绑定 Target、Region 数量、启用状态。  
- 创建/编辑任务向导：
  1. 选择/创建 Target  
  2. 配置协议参数  
  3. 选择 Region/ProbeNodes  
  4. 设置频率与基础阈值（失败次数）  

- 任务详情页：
  - 最近结果表格（时间 x ProbeNode）。  
  - 多 Region 状态视图（如矩阵/地图）。  

- 证书视图：
  - 专门的列表：目标域名、剩余天数、颁发者、状态（正常/即将过期/已过期）。

> TODO（前端专家）：  
> - 选定图表库（ECharts / Chart.js / AntV 等）。  
> - 决定目标详情页是否合并任务视图，避免过多页面。

### 4.4 `alerts`

- 告警事件流：
  - 时间线视图 + 列表视图；过滤：状态/级别/Target/Region。  
- 告警详情：
  - 事件时间线、受影响 Region/Probe、关联任务/Target、历史告警记录。  
- 策略管理：
  - 列表 + 编辑器（可视化配置触发条件和通知通道）。  
- 通知通道配置：
  - 飞书/企业微信/Email/Webhook 表单，对接后端 `NotificationChannel`。

> TODO（前端专家）：  
> - 决定策略编辑 UI 的复杂度：先用简单表单，还是一版就做可视化规则构建器。

### 4.5 `settings`

- 基础配置（系统名称、Logo 等）。  
- 用户/角色管理（如有需要）。  

---

## 5. 实施阶段建议

- 阶段 1：打通「探针管理 + 最简单的探测任务 + 结果展示」  
- 阶段 2：补上证书监控与基础告警策略  
- 阶段 3：扩展告警路由、通知通道、扩展点（extensions）

