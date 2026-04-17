# OneAll 模块级开发说明（后端 / 前端 / 探针）

> 历史说明：本模块指南覆盖的是早期完整范围，仍包含 `frontend/` 目录、`analytics`、`knowledge`、旧集成中心等历史内容。当前仓库中这些内容已部分移除或重构，因此本文件默认仅作历史参考，不作为当前模块边界的权威说明。

更新日期：2026-02-09

本文基于当前代码结构梳理模块职责、关键数据模型、主要 API 入口与前端/探针映射，供后续开发、联调与排查使用。

---

## 统一约定

- HTTP API 前缀：`/api/`（详见 `backend/src/core/urls.py`）
- 认证方式：JWT（`/api/auth/login` 获取 `Bearer` Token）
- 前端 API 基础地址：默认 `http://<host>:8000/api`，见 `frontend/src/services/apiClient.ts`
- 探针通信：gRPC（`grpc_gateway`），REST 已移除

---

## 模块概览（后端 → 前端 → 探针）

| 模块 | 后端 App | 前端页面 | 主要职责 |
| --- | --- | --- | --- |
| 核心 / 认证 | `apps.core` | `pages/auth`, `pages/profile` | 用户、角色、权限、审计、登录/改密 |
| 探针管理 | `apps.probes` | `pages/probes` | 探针注册、调度、执行记录、运行指标 |
| 拨测 / 监控 | `apps.monitoring` | `pages/detection`, `pages/monitoring` | 一次性拨测、监控申请/审批、检测历史 |
| 资产管理 | `apps.assets` | `pages/assets` | 资产记录、同步、导入、代理映射 |
| 统计分析 | `apps.analytics` | `pages/analytics` | 拨测报表、资产治理统计 |
| 工具库 | `apps.tools` | `pages/tools` | 脚本工具、代码仓库、执行记录 |
| 知识库 | `apps.knowledge` | `pages/knowledge` | 文档、分类、版本 |
| 系统设置 | `apps.settings` | `pages/settings` | 系统参数、告警通道、插件配置、角色 |
| 仪表盘 | `apps.dashboard` | `pages/dashboard`, `pages/Home.vue` | 概览、告警摘要、待办 |
| 外部集成 | `apps.monitoring.integrations`, `integrations/*` | `pages/integrations` | Zabbix/Prometheus/CMDB/ITSM 等对接 |
| 探针 Agent | Go 探针 | - | 探针执行、心跳、任务拉取、指标采集 |

---

## 后端模块详解

### 1) 核心 / 认证（`apps.core`）

**职责**：用户、角色、权限、审计日志、认证入口。

**关键模型**
- `core.User`：扩展用户（`display_name/phone/auth_source/roles`）
- `core.Role`：权限集合（JSON）
- `core.AuditLog`：操作审计

**主要 API**
- `POST /api/auth/login`
- `GET /api/auth/me`、`PATCH /api/auth/me`
- `POST /api/auth/change-password`
- `GET /api/audit/logs`

**前端映射**
- `frontend/src/services/profileApi.ts`、`frontend/src/services/session.ts`

---

### 2) 探针管理（`apps.probes`）

**职责**：探针节点管理、配置下发、调度与执行记录、运行指标统计。

**关键模型**
- `ProbeNode`：探针节点（token、心跳、运行指标）
- `ProbeSchedule`：探针调度（支持来源：手工 / 监控申请）
- `ProbeScheduleExecution`：调度执行结果
- `ProbeConfigRefreshRequest`：探针配置刷新请求

**主要 API**
- `GET/POST /api/probes/nodes/`
- `GET/PATCH/DELETE /api/probes/nodes/{id}/`
- `GET /api/probes/nodes/{id}/runtime/`
- `GET /api/probes/nodes/{id}/metrics/history/`
- `GET /api/probes/nodes/{id}/results/stats/`
- `GET/PUT /api/probes/nodes/{id}/config/`
- `GET /api/probes/alerts/recent/`
- `GET/POST /api/probes/schedules/`
- `GET/PATCH/DELETE /api/probes/schedules/{id}/`
- `POST /api/probes/schedules/{id}/pause`、`/resume`、`/archive`
- `GET /api/probes/schedules/{id}/executions/`
- `GET /api/probes/schedule-executions/`、`GET /api/probes/schedule-executions/{id}/`

**后台任务**
- `apps.probes.tasks.health_checks.ping`（健康检查）

**前端映射**
- `frontend/src/services/probeNodeApi.ts`
- `frontend/src/services/probeScheduleApi.ts`
- `frontend/src/services/probeScheduleExecutionApi.ts`
- `frontend/src/services/probeMetricsApi.ts`
- `frontend/src/services/probeAlertApi.ts`

---

### 3) 拨测 / 监控（`apps.monitoring`）

**职责**：一次性拨测、监控申请/审批/重提、历史记录、监控源同步。

**关键模型**
- `DetectionTask`：一次性拨测任务
- `MonitoringRequest`：监控申请（支持审批状态）
- `MonitoringJob`：审批通过后的调度任务

**主要 API**
- `POST /api/detection/one-off`
- `GET /api/detection/tasks/{id}`
- `GET /api/detection/cmdb/validate`
- `GET/POST /api/monitoring/requests`
- `GET/PATCH /api/monitoring/requests/{id}`
- `POST /api/monitoring/requests/{id}/approve`
- `POST /api/monitoring/requests/{id}/reject`
- `POST /api/monitoring/requests/{id}/resubmit`
- `GET /api/monitoring/tasks/history`
- `GET /api/integrations/zabbix/dashboard`
- `GET /api/integrations/zabbix/test`
- `POST /api/integrations/zabbix/sync`

**后台任务**
- `apps.monitoring.tasks.execute_detection`（执行检测 + Timescale 写入）
- `apps.monitoring.tasks.monitoring_source_sync`（同步 Zabbix/Prometheus 状态）
- `apps.monitoring.tasks.zabbix_dashboard_refresh`（刷新仪表盘缓存）

**前端映射**
- `frontend/src/services/detectionApi.ts`
- `frontend/src/services/monitoringApi.ts`
- `frontend/src/services/zabbixApi.ts`

---

### 4) 资产管理（`apps.assets`）

**职责**：资产记录、数据同步、批量导入、代理映射维护。

**关键模型**
- `AssetRecord`：资产记录（多来源合并）
- `AssetSyncRun` / `AssetSyncChange`：同步运行与变更
- `ProxyMapping`：Proxy 映射（Zabbix 代理名映射）

**主要 API**
- `GET/POST /api/assets/records`
- `GET /api/assets/records/query`
- `PATCH /api/assets/records/{id}`
- `POST /api/assets/import`
- `POST /api/assets/sync`
- `GET /api/assets/sync/runs`
- `GET /api/assets/sync/runs/{id}`
- `GET/PUT/POST /api/assets/proxy-mappings`

**后台任务**
- `apps.assets.tasks.sync_assets`（资产同步）

**前端映射**
- `frontend/src/services/assetsApi.ts`
- `frontend/src/services/proxyMappingApi.ts`

---

### 5) 统计分析（`apps.analytics`）

**职责**：拨测报表、资产治理统计。

**主要 API**
- `GET /api/analytics/reports/detection`
- `GET /api/analytics/assets/overview`
- `GET /api/analytics/assets/proxy-hosts`

**后台任务**
- `apps.analytics.tasks.export_detection_report`

**前端映射**
- `frontend/src/services/reportApi.ts`
- `frontend/src/services/assetGovernanceApi.ts`

---

### 6) 工具库（`apps.tools`）

**职责**：脚本工具定义、版本管理、执行记录、代码仓库、脚本插件。

**关键模型**
- `ToolDefinition` / `ScriptVersion` / `ToolExecution`
- `CodeDirectory` / `CodeRepository` / `CodeRepositoryVersion`
- `ScriptPlugin`

**主要 API**
- `GET/POST /api/tools/definitions`
- `POST /api/tools/definitions/{id}/versions`
- `POST /api/tools/definitions/{id}/execute`
- `GET /api/tools/executions`
- `POST /api/tools/repository/upload`
- `POST /api/tools/repository/rollback`
- `GET/POST /api/code/directories`
- `PUT /api/code/directories/{key}`
- `DELETE /api/code/directories/{key}`
- `GET/POST /api/tools/repositories`
- `GET/PUT/DELETE /api/tools/repositories/{id}`
- `GET/POST /api/tools/repositories/{id}/versions`
- `POST /api/tools/repositories/{id}/versions/{version_id}/rollback`
- `POST /api/tools/repositories/{id}/execute`
- `POST /api/tools/ip-regex/compile`、`/expand`
- `GET /api/tools/script-plugins`
- `GET /api/tools/script-plugins/{slug}`
- `PATCH /api/tools/script-plugins/{slug}`
- `POST /api/tools/script-plugins/{slug}/execute`

**后台任务**
- `apps.tools.tasks.run_tool`（脚本执行）
- `apps.tools.tasks.tool_usage_metrics`（统计）

**前端映射**
- `frontend/src/services/toolsApi.ts`
- `frontend/src/services/scriptExecutor.ts`
- `frontend/src/services/codeRepositoryApi.ts`

---

### 7) 知识库（`apps.knowledge`）

**职责**：知识文章、分类、版本历史。

**关键模型**
- `KnowledgeArticle` / `KnowledgeArticleVersion`
- `KnowledgeCategory`

**主要 API**
- `GET/POST /api/knowledge/articles`
- `GET/PUT/DELETE /api/knowledge/articles/{slug}`
- `GET /api/knowledge/articles/{slug}/versions`
- `GET/POST /api/knowledge/categories`
- `GET/PUT/DELETE /api/knowledge/categories/{key}`
- `POST /api/knowledge/categories/order`

**前端映射**
- `frontend/src/services/knowledgeApi.ts`

---

### 8) 系统设置（`apps.settings`）

**职责**：系统参数、告警通道/模板、插件配置、角色与权限。

**关键模型**
- `SystemSettings`
- `AlertChannel` / `AlertTemplate`
- `PluginConfig`

**主要 API**
- `GET /api/public/branding`
- `GET/PUT /api/settings/system`
- `GET /api/settings/permissions/catalog`
- `GET /api/settings/users`
- `DELETE /api/settings/users/{user_id}`
- `POST /api/settings/users/{user_id}/roles`
- `POST /api/settings/users/sync-ldap`
- `GET/POST /api/settings/alerts/templates`
- `GET/PATCH/DELETE /api/settings/alerts/templates/{id}`
- `GET/POST /api/settings/plugins/`
- `GET/PATCH/DELETE /api/settings/plugins/{id}/`
- `GET /api/settings/alerts/channels`
- `PUT /api/settings/alerts/channels/{channel_type}`
- `POST /api/settings/alerts/channels/{channel_type}/test`
- `GET/POST /api/settings/roles/`
- `GET/PATCH/DELETE /api/settings/roles/{id}/`

**后台任务**
- `apps.settings.tasks.plugin_health_check`

**前端映射**
- `frontend/src/services/settingsApi.ts`
- `frontend/src/services/probeAlertApi.ts`（告警展示）
- `frontend/src/stores/pluginConfigs.ts`

---

### 9) 仪表盘（`apps.dashboard`）

**职责**：平台概览、告警摘要、待办、证书与检测面板聚合。

**主要 API**
- `GET /api/dashboard/overview/`
- `GET /api/dashboard/alerts-summary/`
- `GET /api/dashboard/todos/`
- `GET /api/dashboard/detection-grid/`
- `GET /api/dashboard/certificate-alerts/`

**后台任务**
- `apps.dashboard.tasks.overview_refresh.refresh_metrics`

**前端映射**
- `frontend/src/services/dashboardApi.ts`

---

### 10) 外部集成（`integrations/*` 与 `apps.monitoring.integrations`）

**职责**：CMDB/ITSM/资产源/Zabbix/Prometheus 等适配。

**代码位置**
- `backend/src/integrations/cmdb/client.py`
- `backend/src/integrations/itsm/client.py`
- `backend/src/integrations/assets_sync/sources/*`
- `backend/src/apps/monitoring/integrations/zabbix_adapter.py`
- `backend/src/apps/monitoring/integrations/prometheus_adapter.py`

**关联模块**
- 资产同步（`apps.assets`）
- 监控源健康（`apps.monitoring`）

---

## 前端模块映射

**页面目录**：`frontend/src/pages/`
- `dashboard/`：仪表盘
- `detection/`：一次性拨测
- `monitoring/`：监控申请 / 历史
- `probes/`：探针与调度
- `assets/`：资产管理
- `analytics/`：统计报表
- `tools/`：工具库 / 脚本执行
- `knowledge/`：知识库
- `settings/`：系统设置
- `integrations/`：外部集成
- `auth/`、`profile/`、`errors/`

**API 服务层**：`frontend/src/services/`（与后端 API 1:1 映射）

**状态管理**：`frontend/src/stores/`
- `session.ts`：登录态
- `branding.ts`：品牌配置
- `pluginConfigs.ts`：插件配置
- `codeDirectories.ts` / `scriptPlugins.ts`：工具库

---

## 探针（Go Agent）模块说明

**入口**：`probes/cmd/probe/main.go`

**核心结构**（`probes/internal/`）：
- `agent/`：主循环（任务拉取、执行、上报）
- `transport/`：gRPC 通信
- `plugins/`：协议插件（HTTP/TCP/WSS/证书）
- `scheduler/`：任务与调度数据管理
- `metrics/`：本地指标采集与导出
- `control/`：配置同步
- `storage/`：本地缓存（结果/调度）
- `updater/`：自更新

**运行流程简述**
1. 读取配置 → 初始化 API Client / 插件注册
2. gRPC 连接网关 → 启动主循环
3. 拉取调度 → 执行插件 → 上报结果
4. 记录本地指标 / 缓存结果

---

## 关键数据流梳理

### 一次性拨测
1. 前端 `detectionApi.requestOneOffDetection`
2. 后端 `OneOffDetectionView` 创建 `DetectionTask`
3. Celery `execute_detection` 执行并写 Timescale
4. 前端轮询 `fetchDetectionTask`

### 监控申请 → 调度
1. `monitoring/requests` 提交申请
2. 审批通过后生成 `MonitoringJob` 与 `ProbeSchedule`
3. 探针拉取调度执行
4. 执行记录写 `ProbeScheduleExecution` 与 Timescale

### 资产同步
1. `assets/sync` 触发同步
2. Celery `run_asset_sync`
3. 各 Source（CMDB/Zabbix/IPMP/工单）拉取数据
4. 写入 `AssetRecord` + `AssetSyncRun` + `AssetSyncChange`

### 工具执行
1. `tools/definitions/{id}/execute` 创建 `ToolExecution`
2. Celery `run_tool` 执行脚本
3. 输出与结果写回 `ToolExecution.output`

### 知识库版本
1. 文章更新时生成 `KnowledgeArticleVersion`
2. `knowledge/articles/{slug}/versions` 查询历史

---

## TimescaleDB 使用点

- `probe_runtime_metrics`：探针运行指标
- `probe_detection_results`：拨测结果历史

代码入口：
- `apps.probes.repositories.runtime_metrics`
- `apps.monitoring.repositories.detection_metrics`

---

## 可扩展点建议

- 新协议插件：在 `probes/internal/plugins/` 注册
- 新监控源：在 `apps.monitoring.integrations/` 增加适配器
- 新资产源：在 `integrations/assets_sync/sources/` 增加同步器
- 新工具类型：扩展 `apps.tools` + 前端 `tools` 页面
