# Tasks: OneAll 智能运维平台 MVP

> 历史说明：本任务清单反映的是原始交付拆分，包含已删除模块、旧目录和旧测试文件路径。它不是当前仓库结构的权威来源，仅用于追溯最初计划。

**Input**: Design documents from `/specs/001-build-oneall-platform/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 针对关键接口与流程配置集成测试及端到端验证任务，确保每个用户故事可独立验收。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `frontend/src/...`
- **Backend**: `backend/src/...`
- **Backend Tests**: `backend/tests/...`
- **Probe Agent**: `probes/src/...`
- **Docs & Scripts**: `docs/...`, `scripts/...`

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 初始化 Django 项目骨架与依赖文件于 `backend/src/manage.py`
- [X] T002 生成 Django 应用目录结构于 `backend/src/apps/__init__.py`
- [X] T003 配置基础 settings（时区/语言/认证）于 `backend/src/core/settings/base.py`
- [X] T004 [P] 配置 Celery 与 Redis 基础连接于 `backend/src/core/celery.py`
- [X] T005 [P] 初始化 Vue 3 + Vite + Element Plus 工程于 `frontend/package.json`
- [X] T006 配置前端 ESLint + Prettier 规则于 `frontend/.eslintrc.cjs`
- [X] T007 创建探针代理仓库结构与依赖文件于 `probes/pyproject.toml`
- [X] T008 编写 Docker Compose 框架含 mysql/timescaledb/redis 于 `deploy/local/docker-compose.yml`
- [X] T009 [P] 配置根级别 Makefile/脚本封装常用命令于 `scripts/make_tasks.sh`
- [X] T010 撰写 CONTRIBUTING 与 README 扩展说明于 `docs/operations/README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T011 定义 MySQL 连接、环境变量与 secrets 模板于 `backend/src/core/settings/database.py`
- [X] T012 创建 TimescaleDB 连接与 Hypertable 初始化脚本于 `backend/src/core/settings/timescale.py`
- [X] T013 [P] 配置 Django ORM 基础模型（BaseModel、审计字段）于 `backend/src/apps/core/models/base.py`
- [X] T014 创建 User 与 Role 模型及迁移于 `backend/src/apps/core/models/user.py`
- [X] T015 实现 JWT 认证中间件与权限装饰器于 `backend/src/core/auth/jwt.py`
- [X] T016 [P] 建立统一结构化日志封装于 `backend/src/core/observability.py`
- [X] T017 配置 Celery worker/beat 与任务路由于 `backend/src/workers/config.py`
- [X] T018 [P] 设置前端路由、全局状态与 API 客户端于 `frontend/src/main.ts`
- [X] T019 建立前端认证守卫与会话持久化于 `frontend/src/stores/session.ts`
- [X] T020 配置探针代理与中心 HTTP/gRPC 客户端于 `probes/src/agent/http_client.py`
- [X] T021 [P] 编写基础单元测试脚手架（pytest、coverage）于 `backend/pytest.ini`
- [X] T022 补充基础 runbook：环境启动流程于 `docs/operations/runbooks/environment-bootstrap.md`
- [X] T120 创建 ProbeNode 模型与迁移于 `backend/src/apps/probes/models/probe_node.py`
- [X] T121 创建 ProxyMapping 模型与迁移于 `backend/src/apps/probes/models/proxy_mapping.py`（已在后续版本移除）
- [X] T122 实现探针管理 API（列表/创建/更新/心跳）于 `backend/src/apps/probes/api/probe_views.py`
- [X] T123 实现探针监控与告警服务于 `backend/src/apps/probes/services/probe_monitor_service.py`
- [X] T124 [P] 构建探针管理前端页面于 `frontend/src/pages/probes/ProbeManager.vue`
- [X] T125 [P] 构建 Proxy 映射管理组件于 `frontend/src/pages/probes/components/ProxyMappingTable.vue`（已在后续版本移除）
- [X] T126 [P] 编写探针管理集成测试于 `backend/tests/integration/test_probe_management.py`
- [X] T127 [P] 编写探针管理前端端到端测试于 `frontend/tests/e2e/probe-management.spec.ts`
- [X] T128 更新探针管理运维手册于 `docs/operations/runbooks/probe-management.md`

---

## Phase 3: 平台概览与系统设置（支撑性功能）

- [X] T129 设计概览 API 合约测试于 `backend/tests/contract/test_dashboard_openapi.py`
- [X] T130 [P] 编写概览页面端到端测试于 `frontend/tests/e2e/dashboard.spec.ts`
- [X] T131 [P] 设计系统设置 API 合约测试于 `backend/tests/contract/test_system_settings_openapi.py`
- [X] T132 [P] 编写系统设置端到端测试于 `frontend/tests/e2e/system-settings.spec.ts`
- [X] T133 实现概览数据聚合服务于 `backend/src/apps/dashboard/services/overview_service.py`
- [X] T134 暴露 `/dashboard/overview` 接口于 `backend/src/apps/dashboard/api/overview_view.py`
- [X] T135 构建概览页面与蜂窝图组件于 `frontend/src/pages/dashboard/HomeOverview.vue`
- [X] T136 [P] 实现概览图表组件于 `frontend/src/pages/dashboard/components/OverviewCharts.vue`
- [X] T137 配置概览指标刷新与缓存于 `backend/src/apps/dashboard/tasks/overview_refresh.py`
- [X] T138 创建系统设置模型与迁移于 `backend/src/apps/settings/models/system_settings.py`
- [X] T139 实现系统设置 API（用户/权限/日志/通知/主题）于 `backend/src/apps/settings/api/system_settings_view.py`
- [X] T140 构建系统设置管理页面于 `frontend/src/pages/settings/SystemSettings.vue`
- [X] T141 [P] 构建系统设置子组件（用户、通知、主题）于 `frontend/src/pages/settings/components/SettingsTabs.vue`
- [X] T142 整合系统日志与通知配置逻辑于 `backend/src/apps/settings/services/system_settings_service.py`
- [X] T143 更新系统设置运维手册于 `docs/operations/runbooks/system-settings.md`
- [X] T163 [US1] 实现告警摘要 API（最近告警列表与分级聚合）于 `backend/src/apps/dashboard/api/alerts_summary_view.py`
- [X] T164 [US1] 实现待办事项服务（ITSM 待审批与探针异常排查）于 `backend/src/apps/dashboard/services/todo_service.py`
- [X] T165 [US1] 构建前端告警摘要组件于 `frontend/src/pages/dashboard/components/AlertSummary.vue`
- [X] T166 [US1] 构建前端待办事项组件并集成首页于 `frontend/src/pages/dashboard/components/TodoList.vue`
- [X] T167 [US1] 扩展 dashboard 端到端测试覆盖告警/待办校验于 `frontend/tests/e2e/dashboard.spec.ts`
- [X] T168 [US2] 设计操作日志 API 合约测试于 `backend/tests/contract/test_audit_log_openapi.py`
- [X] T169 [US2] 实现操作日志查询/导出 API 于 `backend/src/apps/core/api/audit_log_view.py`
- [X] T170 [US2] 构建前端操作日志检索页面于 `frontend/src/pages/settings/AuditLogViewer.vue`
- [X] T171 [US2] 编写操作日志导出端到端测试于 `frontend/tests/e2e/audit-log.spec.ts`
- [X] T172 [US2] 更新系统设置运维手册新增日志导出流程于 `docs/operations/runbooks/system-settings.md`
- [X] T150 设计拨测历史 API 合约测试于 `backend/tests/contract/test_monitoring_history_openapi.py`
- [X] T151 [P] 编写拨测历史端到端测试于 `frontend/tests/e2e/monitoring-history.spec.ts`
- [X] T152 实现拨测历史查询仓储层于 `backend/src/apps/monitoring/repositories/monitoring_history_repository.py`
- [X] T153 暴露 `/monitoring/tasks/history` 接口于 `backend/src/apps/monitoring/api/monitoring_history_view.py`
- [X] T154 实现拨测历史数据聚合与过滤逻辑于 `backend/src/apps/monitoring/services/monitoring_history_service.py`
- [X] T155 [P] 构建拨测历史前端页面于 `frontend/src/pages/monitoring/MonitoringHistory.vue`
- [X] T156 [P] 构建历史筛选组件与详情抽屉于 `frontend/src/pages/monitoring/components/HistoryFilters.vue`
- [X] T157 编写拨测历史运维文档于 `docs/operations/runbooks/monitoring-history.md`
- [X] T158 制定全局 UI 设计规范与配色方案于 `design/ui/style-guide.fig`
- [X] T159 [P] 输出通用组件线框稿（卡片/图表/表格）于 `design/ui/component-wireframes.fig`
- [X] T160 [P] 实现前端主题变量与全局样式文件于 `frontend/src/styles/theme.scss`
- [X] T161 [P] 构建通用 KPI 卡片与状态标签组件于 `frontend/src/components/common/KpiCard.vue`
- [X] T162 编写 UI 设计规范说明文档于 `docs/operations/design/ui-style-guide.md`

---

## Phase 4: User Story 1 - 运维值班人员即时拨测 (Priority: P1) 🎯 MVP

**Goal**: 让值班人员能够从前端触发一次性拨测，查看响应信息、证书状态与日志追踪。

**Independent Test**: 使用前端表单对目标域名发起 HTTP/HTTPS 拨测，查看返回数据、证书信息与 TimescaleDB 中写入的指标记录。

### Tests for User Story 1 ⚠️

- [X] T023 [US1] 设计拨测 API 合约测试用例于 `backend/tests/contract/test_detection_openapi.py`
- [X] T024 [P] [US1] 编写拨测服务单元测试覆盖成功/失败/超时于 `backend/tests/unit/test_detection_service.py`
- [X] T025 [P] [US1] 编写探针执行端到端测试于 `probes/tests/integration/test_probe_execution.py`
- [X] T026 [P] [US1] 编写前端拨测页面 Cypress 测试于 `frontend/tests/e2e/detection.spec.ts`
- [X] T098 [P] [US1] 编写 CMDB 域名校验集成测试于 `backend/tests/integration/test_cmdb_validation.py`
- [X] T099 [P] [US1] 扩展前端拨测端到端脚本覆盖 CMDB 提示于 `frontend/tests/e2e/detection_cmdb.spec.ts`
- [X] T144 [P] [US1] 编写证书检测集成测试于 `backend/tests/integration/test_certificate_detection.py`
- [X] T145 [P] [US1] 编写证书探针单元测试于 `probes/tests/unit/test_certificate_probe.py`

### Implementation for User Story 1

- [X] T027 [US1] 定义 DetectionTask 模型与迁移于 `backend/src/apps/monitoring/models/detection_task.py`
- [X] T028 [US1] 实现检测请求序列化与验证逻辑于 `backend/src/apps/monitoring/serializers/detection_serializer.py`
- [X] T029 [US1] 实现拨测调度器服务（同步/异步）于 `backend/src/apps/monitoring/services/detection_service.py`
- [X] T030 [US1] 创建 Celery 任务处理一次性拨测于 `backend/src/apps/monitoring/tasks/execute_detection.py`
- [X] T031 [US1] 写入拨测结果与指标存储适配层于 `backend/src/apps/monitoring/repositories/detection_metrics.py`
- [X] T032 [US1] 暴露 POST `/detection/one-off` API 视图于 `backend/src/apps/monitoring/api/one_off_detection_view.py`
- [X] T033 [P] [US1] 暴露 GET `/detection/tasks/{id}` 查询接口于 `backend/src/apps/monitoring/api/detection_detail_view.py`
- [X] T034 [US1] 设计探针插件接口与注册机制于 `probes/src/plugins/base.py`
- [X] T035 [US1] 实现 HTTP(S)/Telnet/WSS 探针插件于 `probes/src/plugins/http_probe.py`
- [X] T036 [US1] 将探针执行结果上传至后端并处理日志于 `probes/src/agent/runner.py`
- [X] T037 [US1] 构建一次性拨测表单页面于 `frontend/src/pages/detection/OneOffDetection.vue`
- [X] T038 [P] [US1] 开发拨测结果详情组件于 `frontend/src/pages/detection/components/DetectionResultPanel.vue`
- [X] T039 [US1] 集成前端 API 客户端与状态管理于 `frontend/src/services/detectionApi.ts`
- [X] T040 [US1] 更新运行文档：一次性拨测操作指南于 `docs/operations/runbooks/oneoff-detection.md`
- [X] T146 [US1] 实现证书检测服务与链验证于 `backend/src/apps/monitoring/services/detection_certificate.py`
- [X] T147 [US1] 实现证书探针插件于 `probes/src/plugins/certificate_probe.py`
- [X] T148 [US1] 扩展拨测结果面板展示证书信息于 `frontend/src/pages/detection/components/DetectionResultPanel.vue`
- [X] T149 [US1] 在拨测文档中补充证书排障步骤于 `docs/operations/runbooks/oneoff-detection.md`
- [X] T100 [US1] 实现 CMDB 域名校验服务于 `backend/src/apps/monitoring/services/cmdb_checker.py`
- [X] T101 [US1] 集成 CMDB API 客户端与配置管理于 `backend/src/integrations/cmdb/client.py`
- [X] T102 [US1] 构建域名校验提示组件并接入拨测表单于 `frontend/src/pages/detection/components/DomainValidationBanner.vue`
- [X] T103 [US1] 在拨测流程中处理 CMDB 校验状态与错误提示于 `frontend/src/pages/detection/OneOffDetection.vue`
- [X] T183 [US1] 添加探针容量检测与排队提示于 `backend/src/apps/monitoring/services/detection_scheduler.py`

**Checkpoint**: 完成后，值班人员可独立运行一次拨测并查看返回数据、日志与指标。

---

## Phase 5: User Story 2 - 平台管理员建立持续拨测与集成 (Priority: P1)

**Goal**: 管理员可提交周期拨测申请、自动创建 ITSM 工单并在批准后生成任务，监控插件健康。

**Independent Test**: 通过前端提交周期拨测申请，ITSM 回调成功后自动创建 MonitoringJob，插件中心能展示集成源健康状态。

### Tests for User Story 2 ⚠️

- [X] T041 [US2] 设计拨测申请 API 合约测试于 `backend/tests/contract/test_monitoring_request_openapi.py`
- [X] T042 [P] [US2] 编写 ITSM 客户端回调模拟测试于 `backend/tests/integration/test_itsm_callback.py`
- [X] T043 [P] [US2] 编写插件健康检查服务单元测试于 `backend/tests/unit/test_plugin_health_service.py`
- [X] T044 [P] [US2] 编写前端审批流程端到端测试于 `frontend/tests/e2e/monitoring-request.spec.ts`
- [X] T104 [P] [US2] 编写 Zabbix 插件集成与回放测试于 `backend/tests/integration/test_zabbix_adapter.py`
- [X] T105 [P] [US2] 编写 Prometheus 插件集成与回放测试于 `backend/tests/integration/test_prometheus_adapter.py`

### Implementation for User Story 2
- [X] T045 [US2] 创建 MonitoringRequest 模型与迁移于 `backend/src/apps/monitoring/models/monitoring_request.py`
- [X] T046 [US2] 创建 MonitoringJob 模型与迁移于 `backend/src/apps/monitoring/models/monitoring_job.py`
- [X] T047 [US2] 实现拨测申请序列化与字段校验于 `backend/src/apps/monitoring/serializers/monitoring_request_serializer.py`
- [X] T048 [US2] 实现 `/monitoring/requests` 提交/查询 API 于 `backend/src/apps/monitoring/api/monitoring_request_view.py`
- [X] T049 [US2] 实现 ITSM REST 客户端与幂等回调于 `backend/src/integrations/itsm/client.py`
- [X] T050 [US2] 实现回调入口 `/monitoring/requests/{id}/status` 于 `backend/src/apps/monitoring/api/itsm_callback_view.py`
- [X] T051 [US2] 实现审批成功后创建 MonitoringJob 的服务逻辑于 `backend/src/apps/monitoring/services/monitoring_job_service.py`
- [X] T052 [US2] 实现监控任务调度 Celery 周期任务于 `backend/src/apps/monitoring/tasks/monitoring_job_runner.py`
- [X] T053 [US2] 实现插件配置模型与仓储于 `backend/src/apps/settings/models/plugin_config.py`
- [X] T054 [US2] 实现插件健康检查任务与告警策略于 `backend/src/apps/settings/tasks/plugin_health_check.py`
- [X] T055 [US2] 构建拨测申请前端表单页面于 `frontend/src/pages/monitoring/MonitoringRequestForm.vue`
- [X] T056 [P] [US2] 构建审批时间轴与状态卡片组件于 `frontend/src/pages/monitoring/components/RequestTimeline.vue`
- [X] T057 [P] [US2] 构建集成中心健康看板页面于 `frontend/src/pages/monitoring/MonitoringDashboard.vue`
- [X] T058 [US2] 编写 ITSM 集成与审批回调 Runbook 于 `docs/operations/runbooks/monitoring-approval.md`
- [X] T106 [US2] 实现 Zabbix 监控源适配器与数据入库于 `backend/src/apps/monitoring/integrations/zabbix_adapter.py`
- [X] T107 [US2] 实现 Prometheus 监控源适配器与指标拉取于 `backend/src/apps/monitoring/integrations/prometheus_adapter.py`
- [X] T108 [US2] 建立外部监控源数据同步任务与 TimescaleDB 写入于 `backend/src/apps/monitoring/tasks/monitoring_source_sync.py`
- [X] T109 [US2] 构建集成中心插件配置表单与凭据管理界面于 `frontend/src/pages/monitoring/components/PluginConfigForm.vue`
- [X] T110 [US2] 在集成中心看板中展示外部源状态与指标于 `frontend/src/pages/monitoring/MonitoringDashboard.vue`
- [X] T111 [US2] 编写外部监控源集成 Runbook 于 `docs/operations/runbooks/monitoring-sources.md`
- [X] T182 [US2] 实现 ITSM 回调失败重试与人工回退 API 于 `backend/src/apps/monitoring/services/itsm_retry_service.py`
- [X] T185 [US2] 插件故障告警 Webhook 与 Runbook 更新于 `docs/operations/runbooks/monitoring-sources.md`

**Checkpoint**: ITSM 回调后自动创建周期拨测任务并在前端看板展示。

---

## Phase 6: User Story 3 - 数据分析与资产管理人员聚合信息 (Priority: P2)

**Goal**: 聚合多来源资产数据，并提供拨测统计分析与导出能力。

**Independent Test**: 触发资产同步，看到来源区分与数据覆盖率；导出 30 天拨测报表并核对指标。

### Tests for User Story 3 ⚠️

- [X] T059 [US3] 设计资产同步 API 合约测试于 `backend/tests/contract/test_asset_openapi.py`
- [X] T060 [P] [US3] 编写资产同步服务集成测试于 `backend/tests/integration/test_asset_sync.py`
- [X] T061 [P] [US3] 编写统计报表导出服务测试于 `backend/tests/integration/test_report_export.py`
- [X] T062 [P] [US3] 编写前端资产页面端到端测试于 `frontend/tests/e2e/assets.spec.ts`

### Implementation for User Story 3

- [X] T063 [US3] 创建 AssetRecord 模型及历史版本支持于 `backend/src/apps/assets/models/asset_record.py`
- [X] T064 [US3] 为资产同步配置外部连接器（Zabbix/Prometheus/IPMP）于 `backend/src/apps/assets/integrations/__init__.py`
- [X] T065 [US3] 实现资产同步服务（全量/增量）于 `backend/src/apps/assets/services/sync_service.py`
- [X] T066 [US3] 实现同步日志与失败重试机制于 `backend/src/apps/assets/tasks/asset_sync_task.py`
- [X] T067 [US3] 实现 `/assets/records` 列表与筛选 API 于 `backend/src/apps/assets/api/asset_view.py`
- [X] T068 [US3] 实现 `/assets/sync` 触发接口于 `backend/src/apps/assets/api/asset_sync_view.py`
- [X] T069 [US3] 创建资产中心前端页面于 `frontend/src/pages/assets/AssetCenter.vue`
- [X] T070 [P] [US3] 创建资产来源过滤与同步日志组件于 `frontend/src/pages/assets/components/AssetFilters.vue`
- [X] T071 [US3] 创建统计报表查询服务于 `backend/src/apps/analytics/services/report_service.py`
- [X] T072 [US3] 实现报表导出任务队列于 `backend/src/apps/analytics/tasks/report_export_task.py`
- [X] T073 [P] [US3] 构建监控报表前端页面于 `frontend/src/pages/analytics/MonitoringReports.vue`
- [X] T074 [US3] 编写资产与报表 Runbook 于 `docs/operations/runbooks/assets-and-reports.md`
- [X] T184 [US3] 实现资产冲突比对与人工确认流程于 `backend/src/apps/assets/services/conflict_resolver.py`

**Checkpoint**: 资产中心展示多来源数据，报表可导出并符合验收场景。

---

## Phase 7: User Story 4 - 运维团队共享工具、脚本与知识 (Priority: P3)

**Goal**: 提供工具库与知识库，支持脚本执行、结果记录与知识沉淀。

**Independent Test**: 上传脚本并执行，查看执行结果回写与知识库条目检索能力。

### Tests for User Story 4 ⚠️

- [X] T075 [US4] 设计工具库与知识库 API 合约测试于 `backend/tests/contract/test_tools_knowledge_openapi.py`
- [X] T076 [P] [US4] 编写工具执行服务集成测试于 `backend/tests/integration/test_tool_execution.py`
- [X] T077 [P] [US4] 编写知识库搜索集成测试于 `backend/tests/integration/test_knowledge_search.py`
- [X] T078 [P] [US4] 编写前端工具与知识库端到端测试于 `frontend/tests/e2e/tools-knowledge.spec.ts`
- [X] T112 [P] [US4] 编写代码管理 API 合约测试于 `backend/tests/contract/test_code_repository_openapi.py`
- [X] T113 [P] [US4] 编写代码管理前端端到端测试于 `frontend/tests/e2e/code-repository.spec.ts`

### Implementation for User Story 4

- [X] T079 [US4] 创建 ToolDefinition 与 ScriptVersion 模型及迁移于 `backend/src/apps/tools/models/tool_definition.py`
- [X] T080 [US4] 实现脚本仓库同步服务于 `backend/src/apps/tools/services/script_repository.py`
- [X] T081 [US4] 搭建工具执行引擎与探针桥接于 `backend/src/apps/tools/services/tool_runner.py`
- [X] T082 [US4] 实现工具执行 Celery 任务与结果存档于 `backend/src/apps/tools/tasks/run_tool_task.py`
- [X] T083 [US4] 实现工具库 API（列表/创建/执行）于 `backend/src/apps/tools/api/tool_views.py`
- [X] T084 [US4] 创建 KnowledgeArticle 模型与基础检索能力于 `backend/src/apps/knowledge/models/knowledge_article.py`
- [X] T085 [US4] 实现知识库 API（搜索/创建/更新）于 `backend/src/apps/knowledge/api/knowledge_views.py`
- [X] T086 [US4] 构建工具库前端界面于 `frontend/src/pages/tools/ToolLibrary.vue`
- [X] T087 [P] [US4] 构建知识库前端界面于 `frontend/src/pages/knowledge/KnowledgeCenter.vue`
- [X] T088 [US4] 实现执行结果回写知识库逻辑于 `backend/src/apps/tools/services/tool_result_sync.py`
- [X] T089 [US4] 编写工具与知识库 Runbook 于 `docs/operations/runbooks/tools-knowledge.md`
- [X] T114 [US4] 创建代码仓库模型与版本实体于 `backend/src/apps/tools/models/script_repository.py`
- [X] T115 [US4] 实现代码管理 API（创建/上传/回滚）于 `backend/src/apps/tools/api/repository_views.py`
- [X] T116 [US4] 实现代码在线编辑与版本比较服务于 `backend/src/apps/tools/services/repository_editor.py`
- [X] T117 [US4] 构建代码管理前端界面于 `frontend/src/pages/tools/CodeRepository.vue`
- [X] T118 [US4] 集成代码管理审计日志记录于 `backend/src/apps/tools/services/repository_audit.py`
- [X] T119 [US4] 更新工具与知识库 Runbook 涵盖代码管理于 `docs/operations/runbooks/tools-knowledge.md`
- [X] T186 [US4] 审计敏感字段访问日志于 `backend/src/apps/tools/services/tool_audit.py`

**Checkpoint**: 工具执行可追踪、知识库可检索并与执行结果互通。

---

## Phase N: Polish & Cross-Cutting Concerns

- [X] T090 加强审计日志脱敏与合规校验于 `backend/src/apps/core/middleware/audit_middleware.py`
- [X] T091 [P] 完成前端 UI 无障碍与国际化检查于 `frontend/src/i18n/index.ts`
- [ ] T092 更新可观测性仪表盘与告警阈值文档（暂缓：未引入链路追踪与采集器）
- [X] T093 [P] 编写 MySQL/TimescaleDB 备份与恢复脚本于 `scripts/database/backup.sh`
- [X] T094 编写发布打包流程与 Git 标签脚本于 `scripts/release/prepare_release.sh`
- [X] T095 [P] 回顾 quickstart 实践并在 `specs/001-build-oneall-platform/quickstart.md` 留下校验记录
- [X] T096 整理运维知识库目录与手册索引于 `docs/operations/index.md`
- [X] T097 进行预发布清单与合规审查于 `docs/operations/checklists/pre-release.md`
- [X] T173 [All] 编写核心模块结构化日志埋点清单于 `backend/src/apps/*/logging.py`
- [X] T174 [All] 编写结构化日志字段验证单元测试于 `backend/tests/unit/test_structured_logging.py`
- [X] T175 配置拨测性能监控脚本（SC-001）于 `scripts/monitoring/detection_benchmark.sh`
- [X] T176 建立审批 SLA 报表任务（SC-002）于 `backend/src/apps/monitoring/tasks/itsm_sla_report.py`
- [X] T177 实现资产覆盖率仪表盘（SC-003）于 `backend/src/apps/assets/services/coverage_metrics.py`
- [X] T178 添加满意度调查问卷及数据汇总脚本（SC-004）于 `docs/operations/feedback/survey.md`
- [X] T179 报表性能基准测试脚本（SC-005）于 `scripts/monitoring/report_benchmark.sh`
- [X] T180 工具复用率统计任务（SC-006）于 `backend/src/apps/tools/tasks/tool_usage_metrics.py`
- [X] T181 维护窗口执行清单与度量记录（SC-007）于 `docs/operations/checklists/maintenance-window.md`

---

## Dependencies & Execution Order

- **Phase 1 → Phase 2**：完成共享基础后方可启动任何用户故事工作。
- **User Story 1 (P1)** 是 MVP，需先于其他故事完成以验证拨测链路。
- **User Story 2 (P1)** 可在 US1 中后期并行推进，但最终依赖 US1 的探针与拨测基础能力。
- **User Story 3 (P2)** 依赖 US1/US2 产生日志与拨测数据作为统计基础。
- **User Story 4 (P3)** 依赖前面故事提供的身份、审计与任务数据，建议最后完成。
- **Polish 阶段** 在所有故事完成后执行，确保上线所需文档与运维准备就绪。

## Parallel Opportunities

- `[P]` 标记的任务在文件与依赖隔离情况下可并行，例如：
  - Phase 1 内前后端脚手架、Celery 配置可穿插进行（T004、T005、T006）。
  - 各用户故事的测试任务（T023、T041、T059、T075 等）可在实现前先行编写，推动 TDD。
  - 前端页面（T037、T055、T069、T086 等）与后端 API 可在接口契约确定后同步开展。
  - 文档与脚本类任务（T040、T058、T074、T089）可并行于开发尾声执行。

## Parallel Example: User Story 1

```bash
# 并行推进服务与前端组件
Task: "T029 [US1] 实现拨测调度器服务于 backend/src/apps/monitoring/services/detection_service.py"
Task: "T035 [US1] 实现 HTTP(S)/Telnet/WSS 探针插件于 probes/src/plugins/http_probe.py"
Task: "T038 [P] [US1] 开发拨测结果详情组件于 frontend/src/pages/detection/components/DetectionResultPanel.vue"
Task: "T026 [P] [US1] 编写前端拨测页面 Cypress 测试于 frontend/tests/e2e/detection.spec.ts"
```

## Parallel Example: User Story 2

```bash
# 前端表单、后端 ITSM 客户端与健康看板并行
Task: "T055 [US2] 构建拨测申请前端表单页面于 frontend/src/pages/monitoring/MonitoringRequestForm.vue"
Task: "T049 [US2] 实现 ITSM REST 客户端于 backend/src/integrations/itsm/client.py"
Task: "T054 [US2] 实现插件健康检查任务于 backend/src/apps/settings/tasks/plugin_health_check.py"
Task: "T044 [P] [US2] 编写前端审批流程端到端测试于 frontend/tests/e2e/monitoring-request.spec.ts"
```

## Parallel Example: User Story 3

```bash
# 资产同步、统计服务与前端 UI 可在契约确认后同步推进
Task: "T065 [US3] 实现资产同步服务于 backend/src/apps/assets/services/sync_service.py"
Task: "T071 [US3] 创建统计报表查询服务于 backend/src/apps/analytics/services/report_service.py"
Task: "T073 [P] [US3] 构建监控报表前端页面于 frontend/src/pages/analytics/MonitoringReports.vue"
Task: "T062 [P] [US3] 编写前端资产页面端到端测试于 frontend/tests/e2e/assets.spec.ts"
```

## Parallel Example: User Story 4

```bash
# 工具执行与知识库分别推进
Task: "T081 [US4] 搭建工具执行引擎于 backend/src/apps/tools/services/tool_runner.py"
Task: "T085 [US4] 实现知识库 API 于 backend/src/apps/knowledge/api/knowledge_views.py"
Task: "T087 [P] [US4] 构建知识库前端界面于 frontend/src/pages/knowledge/KnowledgeCenter.vue"
Task: "T078 [P] [US4] 编写前端工具与知识库端到端测试于 frontend/tests/e2e/tools-knowledge.spec.ts"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1-2 基础设施与认证、日志、探针框架。
2. 聚焦 User Story 1，按测试→后端→探针→前端→文档顺序完成 T023-T040。
3. 验证一次性拨测场景，准备向值班团队演示。

### Incremental Delivery

1. 在 MVP 之上交付 User Story 2，形成持续拨测与 ITSM 闭环。
2. 进一步实现 User Story 3，提供资产与报表视图，为运营提供全局洞察。
3. 最后交付 User Story 4，完善工具与知识生态，提升响应效率。
4. 每个阶段完成后执行对应 runbook，确保独立可上线。

### Parallel Team Strategy

1. 完成基础设施后，按照角色与专业划分小组：
   - 小组 A：拨测核心与探针（US1）。
   - 小组 B：持续拨测、ITSM 与插件管理（US2）。
   - 小组 C：资产聚合与统计分析（US3）。
   - 小组 D：工具与知识库（US4）。
2. 充分利用 `[P]` 标记的任务并行推进，特别是前端/后端、测试/实现协同。
3. 每个用户故事结束后进行独立验收，再进入下一故事。
