# 前端架构重构阶段收官

日期：2026-04-16

## 收官结论

本轮前端架构重构可以按“阶段完成”收官。

原因不是“所有文件都已经完美”，而是：

- 主结构已经稳定为 `src/app + src/features + src/shared`
- 旧 `pages / stores / components` 已退出运行链
- 主要业务域的大页面已经完成一轮有效收口
- 质量门保持绿色
- 剩余问题已收敛到少数热点页和少数偏大的工具/映射文件，不再属于全局架构失序

因此，后续不应继续把“全局前端架构重构”当作主任务，而应转为“按需精修”。

## 本阶段已完成范围

### 结构迁移

- 路由主链已直接指向 `features/*` 真实实现
- `src/pages` 已退出运行链
- `src/stores` 已退出运行链
- `src/components` 已退出运行链
- `shared` 只保留真正跨域能力

### shared 收口

当前保留在 `shared` 的内容是合理的：

- `PageLoader`
- `PageWrapper`
- `RepositoryPageShell`
- `ScriptSelectorDialog`
- `clipboard`

图表组件、代码编辑器等单域能力已经下沉回对应 feature。

### 重点业务域收口

已经完成一轮有效收口的页面：

- `assets`
  - `AssetCenterPage.vue`
  - `AssetModelCenterPage.vue`
- `settings`
  - `AlertTemplates.vue`
  - `Users.vue`
  - `PermissionRoleDetail.vue`
  - `AuditLogViewer.vue`
  - `AlertChannelDetail.vue`
- `detection`
  - `OneOffDetectionPage.vue`
  - `CertificateDetectionPage.vue`
- `dashboard`
  - `HomeOverviewPage.vue`
- `profile`
  - `UserProfilePage.vue`
- `probes`
  - `ProbeManagerPage.vue`
- `tools`
  - `AccountSyncPage.vue`
  - `GrafanaSyncPage.vue`
  - `CodeRepositoryPage.vue`

这些页面现在已经大多转成：

- 页面壳
- feature 组件
- composable
- api / mapper / utils

## 当前可接受状态

### 可以视为稳定的边界

- `app`：全局 API client、session/theme/branding/app store
- `features`：按业务域组织，已经形成稳定主结构
- `shared`：只保留跨域布局、加载、脚本选择与复制工具

### 当前质量门

截至本次收官，以下验证通过：

- `pnpm lint`
- `pnpm test:unit`
- `pnpm build`

### 运行状态

当前本地开发环境可直接访问：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`

可用管理员账号：

- `admin / Admin#2025!`
- `demo-admin / Demo@1234`

## 剩余结构债

这些问题仍然存在，但不构成继续维持“全局架构重构模式”的理由。

### 仍偏大的页面

- `src/features/assets/pages/AssetModelAdminPage.vue`
- `src/features/assets/pages/AssetFieldAdminPage.vue`
- `src/features/alerts/pages/AlertCheckDetail.vue`
- `src/features/alerts/pages/AlertEventDetail.vue`
- `src/features/tools/pages/ToolLibraryPage.vue`
- `src/features/monitoring/pages/MonitoringRequestFormPage.vue`

### 仍偏大的纯逻辑 / 配置文件

- `src/features/assets/composables/useAssetModelCenterPage.ts`
- `src/features/assets/mappers/assetViewDefinitions.ts`
- `src/features/assets/utils/assetHelpers.ts`
- `src/features/settings/components/AlertTemplateEditorDialog.vue`
- `src/features/dashboard/components/DetectionHoneycomb.vue`
- `src/features/tools/composables/useAccountSyncPage.ts`
- `src/features/tools/composables/useGrafanaSyncPage.ts`
- `src/features/settings/composables/usePermissionRoleDetailPage.ts`
- `src/features/detection/mappers/detectionUtils.ts`
- `src/features/tools/components/ToolExecutionPanel.vue`

### 分层一致性还可继续提升

仍有少量 composable 直接请求 `apiClient`，没有完全走 feature API 层：

- `src/features/monitoring/composables/useMonitoringRequestPage.ts`
- `src/features/detection/composables/useProbeNodes.ts`

### 局部实现仍偏工程化而非抽象化

- `AlertTemplateEditorDialog.vue` 使用 `document.querySelector`
- `useUserProfilePage.ts` 使用 `window.setTimeout` 做校验节流
- `CmdbDomainCheckPage.vue` 直接使用 `navigator.clipboard`

这些问题是“可优化”，不是“必须继续大拆”的问题。

## 后续工作方式

从现在开始，建议采用以下规则：

### 不再做的事

- 不再继续做目录级大迁移
- 不再继续做全局壳层清场
- 不再继续为了“形式更整齐”重写稳定模块

### 继续做的事

- 只在真实业务改动触达某模块时，顺手精修该模块
- 对少数仍偏大的热点页做按需拆分
- 对超大的映射/工具文件做局部拆分

### 推荐优先级

如果后续继续做结构精修，建议顺序：

1. `alerts`
2. `assets admin`
3. `monitoring`
4. 大型工具 / 映射文件

## 最终判断

这轮前端架构整理已经完成了“把系统从历史混合态拉回清晰结构态”的目标。

后续还有优化空间，但已经不需要再以“架构整治项目”的方式推进。

从这一刻开始，前端可以按正常产品开发节奏继续演进。 
