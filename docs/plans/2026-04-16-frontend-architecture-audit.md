# 前端架构审计

日期：2026-04-16

## 结论

当前前端已经完成了从旧结构到 `src/app + src/features + src/shared` 的主迁移。

可以视为稳定的部分：

- 旧 `src/pages`、`src/stores`、`src/components` 已退出运行链。
- 路由主链已经直接落到 `features/*` 真实实现。
- `shared` 只保留了真正跨域的能力：
  - `PageLoader`
  - `PageWrapper`
  - `RepositoryPageShell`
  - `ScriptSelectorDialog`
  - `clipboard`
- `assets` 域和 `settings` 域的主要大页已经完成一轮深拆，结构明显清晰。

当前不建议继续做大规模目录搬运。后续工作应该转为“热点页精修”和“边界一致性审计”。

## 已稳定模块

### app

- `src/app/api/apiClient.ts`
- `src/app/stores/*`

这一层边界已经清晰，没有明显结构债。

### shared

- `src/shared/components/feedback/PageLoader.vue`
- `src/shared/components/layout/PageWrapper.vue`
- `src/shared/components/layout/RepositoryPageShell.vue`
- `src/shared/components/scripts/ScriptSelectorDialog.vue`
- `src/shared/utils/clipboard.ts`

这些能力当前被多个域复用，继续留在 `shared` 是合理的。

### assets

已经完成多轮收口：

- `AssetCenterPage.vue` 已压到 381 行
- `AssetModelCenterPage.vue` 已压到 390 行
- 抽出的组件与 composable 已覆盖表单、详情、导入、冲突详情、同步历史、表格、筛选栏

当前 `assets` 域已经从“大页堆逻辑”转成“页面壳 + 组件 + composable”。

### settings

已经完成多轮收口：

- `AlertTemplates.vue` 已压到 273 行
- `Users.vue` 已压到 324 行
- `PermissionRoleDetail.vue` 已压到 386 行
- `AuditLogViewer.vue` 已压到 250 行
- `AlertChannelDetail.vue` 已压到 222 行

当前 `settings` 域已经具备清晰的页面壳结构。

### detection

已经完成页面状态下沉：

- `OneOffDetectionPage.vue` 已压到 483 行
- `CertificateDetectionPage.vue` 已压到 485 行

两页已转成“页面壳 + composable”结构，但结果区和详情抽屉仍有继续细拆空间。

### dashboard

- `HomeOverviewPage.vue` 已压到 165 行

页面状态与系统明细展示已拆开，`dashboard` 主入口已经稳定。

### probes

- `ProbeManagerPage.vue` 已压到 240 行

节点表格与运行时抽屉已组件化，页面主体已经清晰。

### profile

- `UserProfilePage.vue` 已压到 214 行

资料侧栏、密码卡和页面状态已拆开，可视为稳定模块。

### tools

工具域里最重的两个同步页已经完成一轮有效收口：

- `AccountSyncPage.vue` 已压到 136 行
- `GrafanaSyncPage.vue` 已压到 136 行

它们的执行中心和配置卡已经组件化，但配套 composable 仍偏大。

## 剩余结构债

### P1：仍然偏大的页面

这些页面仍是当前最值得继续关注的热点，但多数已经完成一轮有效收口：

- `src/features/assets/pages/AssetModelAdminPage.vue` 664 行
- `src/features/alerts/pages/AlertCheckDetail.vue` 659 行
- `src/features/assets/pages/AssetFieldAdminPage.vue` 583 行
- `src/features/detection/pages/CertificateDetectionPage.vue` 485 行
- `src/features/detection/pages/OneOffDetectionPage.vue` 483 行
- `src/features/alerts/pages/AlertEventDetail.vue` 492 行
- `src/features/tools/pages/ToolLibraryPage.vue` 403 行
- `src/features/monitoring/pages/MonitoringRequestFormPage.vue` 401 行

建议优先顺序：

1. `alerts`
2. `assets` 中的 admin 页
3. `monitoring`
4. `detection` 的二次精修

### P1：仍然偏大的纯逻辑文件

这些文件不是页面，但已经达到需要再次拆分的程度：

- `src/features/assets/composables/useAssetModelCenterPage.ts` 524 行
- `src/features/assets/mappers/assetViewDefinitions.ts` 505 行
- `src/features/assets/utils/assetHelpers.ts` 441 行
- `src/features/settings/components/AlertTemplateEditorDialog.vue` 430 行
- `src/features/dashboard/components/DetectionHoneycomb.vue` 428 行
- `src/features/tools/composables/useAccountSyncPage.ts` 404 行
- `src/features/settings/composables/usePermissionRoleDetailPage.ts` 399 行
- `src/features/detection/mappers/detectionUtils.ts` 392 行
- `src/features/tools/composables/useGrafanaSyncPage.ts` 381 行
- `src/features/tools/components/ToolExecutionPanel.vue` 368 行

其中最需要注意的是：

- `assetViewDefinitions.ts`
  这已经接近“配置仓库”体量，后面应按资产类型再拆文件。
- `assetHelpers.ts`
  同时承担格式化、排序、错误处理、状态映射，职责偏杂。
- `AlertTemplateEditorDialog.vue`
  弹窗虽然已抽出，但自身已经变成一个小型页面。

### P1：分层一致性还不完全统一

仍有少量 composable 直接请求 `apiClient`，没有走 feature API 层：

- `src/features/monitoring/composables/useMonitoringRequestPage.ts`
- `src/features/detection/composables/useProbeNodes.ts`

这不会立刻造成问题，但会让“页面/组合逻辑只依赖 feature API”的约束变松。

建议后续统一成：

- 页面/组件 -> composable
- composable -> `features/<domain>/api/*`
- `api/*` -> `app/api/apiClient`

### P2：存在局部 DOM 级实现

这些地方仍然使用直接 DOM 或浏览器 API，属于可接受但不够理想的实现：

- `src/features/settings/components/AlertTemplateEditorDialog.vue`
  使用 `document.querySelector` 进行变量插入
- `src/features/profile/composables/useUserProfilePage.ts`
  使用 `window.setTimeout` 做确认密码校验节流
- `src/features/detection/pages/CmdbDomainCheckPage.vue`
  直接使用 `navigator.clipboard`

这类问题优先级不高，但在做精修时可以逐步抽成更稳定的工具或 composable。

## 架构判断

### 现在可以停止的大动作

- 不再继续搬目录
- 不再继续清理旧目录壳层
- 不再继续重构 `shared` 的大边界

这些工作已经完成，再继续做收益会快速下降。

### 现在最值得做的事

1. 选 1 个域做热点页精修
2. 统一剩余层次不一致的调用关系
3. 对体量异常的工具/映射文件做二次拆分

## 建议的下一阶段顺序

### 阶段 1

- `alerts`
  - `AlertCheckDetail.vue`
  - `AlertEventDetail.vue`
  - `AlertEvents.vue`

原因：

- 仍然是当前最大的页面组之一
- 结构模式接近，适合共用列表/详情块

### 阶段 2

- `assets`
  - `AssetModelAdminPage.vue`
  - `AssetFieldAdminPage.vue`

原因：

- 仍然偏大
- 与现有 `assets` 域组件体系贴近，继续拆成本低

### 阶段 3

- `monitoring`
  - `MonitoringRequestFormPage.vue`
  - `MonitoringHistoryPage.vue`

原因：

- 还有一部分页面状态和 API 直接调用未完全收干净

## 当前状态结论

前端重构已经从“目录迁移阶段”进入“结构精修和收尾评估阶段”。

如果只问一句现在是否已经达到“合理”：

答案是：已经达到。

如果问是否已经达到“彻底稳定、没有明显结构债”：

答案是：还没有，但剩余问题已经高度收敛，主要集中在少数热点页和少数大工具文件，不再是全局架构混乱。
