# 技术架构决策

## 1. 后端框架

新版本后端目标采用 Go + Gin 承接 `/api/v1` 业务 API。

目标服务骨架位于 `oneall-go-api`，当前状态：

- 已建立 `go.mod`、Gin router、配置入口和 `/api/v1` 路由注册。
- 路由 key 与 `oneall-antd-prototype/src/platformContracts.ts` 保持一致。
- 因当前开发环境没有 Go toolchain，业务处理仍由 `oneall-api` Node 参考服务承接。
- Go 服务已迁入前端 `/api/v1` 契约中的内存版 handler：权限目录、资产模型/记录、资产同步、告警策略 DSL、一次性检测、探针心跳/领取/回传、告警生成、自动工单、通知、审计、CMDB 校验、探针注册/运行态、批量动作、搜索、登录、总览、Webhook 测试和 IP 正则工具。
- Go HTTP 层已改为依赖 `store.Store` 接口，启动时通过 `DATABASE_URL` 选择运行时 store；当前 `PostgresStore` 已建立 pgxpool 接入骨架和 schema 映射合同。
- `PostgresStore` 已落地主业务链 SQL 写读路径：资产模型列表/创建/更新、资产记录批量写入/查询、告警策略列表/创建、检测任务创建/列表/领取/结果回传、失败探针生成告警、自动/手动工单创建、工单状态流转、通知、审计日志和事件 outbox。
- Go 工具链和本地 PostgreSQL 已完成实跑验收：`go test ./...` 通过；共享业务 E2E 已分别打通 Go 内存模式和 `DATABASE_URL` PostgreSQL 模式。
- Go API 已加入开发联调用 CORS 中间件，允许 Vite 前端携带 `x-oneall-role` 访问 `/api/v1`；浏览器截图已验证前端资产页能读取 Go + PostgreSQL 中的用户自建模型数据。
- 后续需要继续把辅助兼容流和批量管理流替换为 PostgreSQL schema、outbox、Redis Streams 和正式鉴权中间件；主业务闭环已经具备可运行验收证据。

迁移原则：

- 第一阶段先稳定产品边界、API 契约和前端体验。
- 不在第一阶段强行重建所有数据表。
- 存量 `/api/` 只作为兼容入口，新接口统一进入 `/api/v1/`。

## 2. 数据库

主业务库采用 PostgreSQL。

- 资产记录动态字段使用 JSONB。
- 字段映射转换规则使用 JSONB。
- 跨领域事件 payload 使用 JSONB。
- 高频查询字段再补索引，不提前做复杂拓扑或宽表。

首版目标 schema 记录在 `oneall-api/db/migrations/001_initial_schema.sql`，覆盖：

- 用户、资产模型、资产记录、资产同步记录
- 告警策略、检测任务、告警事件、工单
- 探针节点、通知、审计日志、事件 outbox

其中 `asset_records.fields`、`monitoring_strategies.rule`、`notifications.payload`、`audit_logs.payload`、`event_outbox.payload` 等使用 JSONB；`environment`、`business_line`、`status`、`assignee` 等常用筛选字段保留为显式列，服务于权限数据范围和列表查询。

TimescaleDB 仅作为可选时序扩展，用于探针指标、检测耗时趋势和高频执行结果聚合，不承载资产模型、权限矩阵和工单状态机。

## 3. 鉴权

业务 API 使用 JWT。企业用户通过 LDAP 同步，权限使用角色 + 动作矩阵。

页面权限和 API 权限必须使用同一套动作：`read`、`create`、`update`、`delete`、`execute`、`approve`、`close`、`manage`。

## 4. 事件投递

跨领域事件采用 outbox/event_log + Redis Streams。

- 业务数据库中的 outbox/event_log 是事实来源。
- Redis Streams 只作为轻量异步投递、重试和削峰通道。
- 事件必须携带 `event_id`、`trace_id`、`event_type`、`producer`、`payload`、`created_at`。
- 消费者必须幂等，使用 `event_id` 或业务唯一键防重复。

## 5. Redis 边界

Redis 可以用于：

- 事件投递缓冲
- 短期锁
- 限流计数
- 探针任务领取窗口

Redis 不可以用于：

- 业务事实数据唯一存储
- 长期审计日志
- 资产记录主存储

## 6. 探针通信协议

首版探针通信使用 HTTPS + JSON。仓库内置真实本地探针 agent：`oneall-go-api/cmd/oneall-probe-agent`。

探针注册后获得节点 token，后续心跳、领取任务、回传结果均携带 token。agent 通过 `Authorization: Bearer <token>` 和 `x-oneall-probe-id` 绑定身份，并为每次请求附带 `x-oneall-trace-id` 方便串联排障。

关键接口：

- `POST /api/v1/probes/register`
- `POST /api/v1/probes/nodes/{id}/heartbeat`
- `POST /api/v1/probes/tasks/claim`
- `POST /api/v1/probes/tasks/{task_id}/result`

agent 当前支持 HTTP/HTTPS、TCP、DNS、CERTIFICATE 检测。CMDB 校验属于平台 API 能力，不由探针 agent 执行。

真实链路可通过 `oneall-go-api/scripts/real-probe-smoke.mjs` 自动验证：脚本会启动 Go API、注册探针、创建一次性检测、运行 agent 一轮并校验任务完成、运行态和审计记录。

通信可靠性规则：

- agent 无法连接 API 时使用指数退避，不持续打满后端。
- agent 执行完成但结果回传失败时，把结果写入本地 spool 文件，下一轮心跳成功后优先补发。
- 结果回传携带 `result_id`，后端对已完成任务直接返回当前结果，不重复生成告警或工单。
- 后端领取任务前会回收超时的 `running` 任务，避免探针断线导致任务永久卡住。
- 后端根据 `heartbeat_at` 推导探针状态：超过 90 秒降级，超过 5 分钟离线。
