# Frontend Architecture Refactor Design

**Date:** 2026-04-14  
**Scope:** OneAll 前端全局架构整理（不改变现有路由、API 形状和主要交互）

## Goal

把当前以前端技术层为主的结构，渐进式演进为 `app + features + shared` 的领域化结构；把所有大型页面纳入统一拆分规则，降低页面复杂度、依赖耦合和后续维护成本。

## Non-Goals

- 不改现有 URL 路由
- 不改后端 API 形状
- 不做视觉重设计
- 不在本轮引入新的状态管理框架
- 不做“大搬家后再修引用”的一次性激进迁移

## Current Problem

当前前端主要问题不是单点 bug，而是结构失衡：

- 大型页面职责过载，页面同时承担模板、请求、映射、导入、图表、状态编排
- 目录以 `pages / services / stores / components` 为主，业务域边界不清晰
- 外部依赖虽已收口一部分，但领域能力尚未收口
- 共用组件和领域组件混放，导致复用边界模糊

## Page Inventory

本次“大型页面”统一按 **300 行以上页面/页面级组件** 纳管，按领域归组如下：

### Assets

- `src/pages/assets/AssetCenter.vue` 2770
- `src/pages/assets/AssetModelCenter.vue` 1157
- `src/pages/assets/AssetModelAdmin.vue` 597
- `src/pages/assets/AssetFieldAdmin.vue` 493

### Tools

- `src/pages/tools/CodeRepository.vue` 2194
- `src/pages/tools/AccountSync.vue` 739
- `src/pages/tools/GrafanaSync.vue` 694
- `src/pages/tools/ToolLibrary.vue` 446
- `src/pages/tools/IpRegexHelper.vue` 349

### Probes

- `src/pages/probes/ProbeManager.vue` 813

### Detection

- `src/pages/detection/OneOffDetection.vue` 645
- `src/pages/detection/CertificateDetection.vue` 636
- `src/pages/detection/CmdbDomainCheck.vue` 378
- `src/pages/detection/utils/detectionUtils.ts` 392
- `src/pages/detection/components/ProbeNodeSelector.vue` 294

### Monitoring

- `src/pages/monitoring/MonitoringRequestForm.vue` 610
- `src/pages/monitoring/MonitoringHistory.vue` 447
- `src/pages/monitoring/components/PluginConfigForm.vue` 301

### Settings

- `src/pages/settings/AlertTemplates.vue` 681
- `src/pages/settings/PermissionRoleDetail.vue` 587
- `src/pages/settings/AlertChannelDetail.vue` 549
- `src/pages/settings/Users.vue` 527
- `src/pages/settings/AuditLogViewer.vue` 371
- `src/pages/settings/Alerts.vue` 270
- `src/pages/settings/SystemSettings.vue` 263
- `src/pages/settings/AuthIntegration.vue` 260

### Alerts

- `src/pages/alerts/AlertCheckDetail.vue` 609
- `src/pages/alerts/AlertEventDetail.vue` 486
- `src/pages/alerts/AlertEvents.vue` 368
- `src/pages/alerts/AlertChecks.vue` 288

### Dashboard / Account

- `src/pages/dashboard/HomeOverview.vue` 530
- `src/pages/dashboard/components/DetectionHoneycomb.vue` 393
- `src/pages/profile/UserProfile.vue` 505
- `src/pages/auth/Login.vue` 384

## Target Architecture

采用三层顶级结构：

```text
src/
├── app/
│   ├── router/
│   ├── stores/
│   ├── api/
│   └── providers/
├── features/
│   ├── assets/
│   ├── probes/
│   ├── monitoring/
│   ├── detection/
│   ├── tools/
│   ├── settings/
│   ├── alerts/
│   ├── dashboard/
│   ├── auth/
│   └── profile/
└── shared/
    ├── components/
    ├── composables/
    ├── utils/
    ├── types/
    └── styles/
```

### app

只放应用级能力：

- 路由
- 会话与品牌等跨域 store
- 全局 API 客户端
- 应用启动与 provider 装配

### features

每个业务域内部统一为：

```text
features/<domain>/
├── pages/
├── components/
├── composables/
├── api/
├── mappers/
└── types/
```

说明：

- `pages/` 只放该域的真实页面实现
- `components/` 只放该域内部复用组件
- `composables/` 负责编排页面状态和交互
- `api/` 只放该域请求封装和 DTO
- `mappers/` 放视图模型转换、表格列配置、导入映射、图表 option 生成
- `types/` 放该域专属类型

### shared

只放真正跨域复用的东西：

- `RepositoryPageShell`
- `PageWrapper`
- `PageLoader`
- `KpiCard`
- `BaseChart`
- `CodeEditor`
- `ScriptSelectorDialog`
- 通用格式化、日期、导入、图表适配、纯工具函数

## Migration Strategy

采用**渐进式领域化重构**，不做一次性迁移。

### Rule 1: Route Stability

当前 `src/pages/*` 路由入口先保留，但逐步变成薄包装层。

示意：

- 现状：`src/pages/assets/AssetCenter.vue` 直接承载全部实现
- 目标：`src/pages/assets/AssetCenter.vue` 只引入 `src/features/assets/pages/AssetCenterPage.vue`

### Rule 2: Service Bridge

`src/services/*` 不在第一天删除，而是先变成桥接层。

示意：

- 新实现：`src/features/assets/api/assetsApi.ts`
- 兼容导出：`src/services/assetsApi.ts`

这样可以降低一次性改 import 的风险。

### Rule 3: Store Ownership

store 分两类：

- 应用级 store：保留到 `src/app/stores/`
  - `session`
  - `branding`
  - `app`
  - `theme`
- 领域级 store：迁入对应 feature
  - `assetModels`
  - `codeDirectories`
  - `scriptPlugins`
  - `pluginConfigs`（若继续保留）

### Rule 4: Page Decomposition

大型页面统一拆成五层：

- page shell
- feature components
- composable orchestrator
- api adapter
- mappers / pure utils

禁止继续出现“一个页面文件同时负责模板、请求、导入、格式化、图表组装”的模式。

## Domain-Specific Split Rules

### Assets

重点拆分：

- 列表与筛选
- 导入流程
- 资产类型与表单配置
- 同步运行日志
- 纯数据映射函数

### Probes

重点拆分：

- 节点列表
- 运行时抽屉
- 指标拉取
- 图表 option 生成

### Tools

重点拆分：

- 仓库版本管理
- 代码编辑器区域
- 脚本执行区域
- 外部集成配置表单

### Detection / Monitoring

重点拆分：

- 配置输入
- 结果展示
- 批量轮询
- 历史筛选
- 申请表单编排

### Settings / Alerts

重点拆分：

- 表格页
- 详情页
- 表单状态
- 权限/模板/渠道映射

## Execution Batches

### Batch 1

- assets
- probes

原因：页面最大、职责最混杂、最适合作为结构样板

### Batch 2

- tools
- monitoring
- detection

原因：与 Batch 1 在共享壳和导入/执行流程上有明显关联

### Batch 3

- settings
- alerts
- dashboard
- profile
- auth

原因：适合在前两批规范稳定后统一收口

## Acceptance Criteria

重构完成后应满足：

- `src/pages/*` 只保留薄入口或轻量页面
- 所有大型页面真实实现进入 `src/features/*`
- `src/services/*` 不再承载领域主逻辑
- `src/components/*` 中仅保留跨域共享组件或过渡导出
- 每个 feature 有清晰的 `pages/components/composables/api/mappers/types`
- 单页文件不再超过约 300~400 行，超出者必须拆分

## Risks

- 过渡期会出现新旧目录并存
- 批次间可能出现共享组件归属不清
- 若没有桥接层，import 修改面会过大

## Risk Controls

- 保留 `pages/services/components` 过渡层，逐步变薄
- 每批结束后再进入下一批
- 每批必须跑单测和构建
- 不在同一批中同时改路由、API 形状和页面结构
