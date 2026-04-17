# Frontend Architecture Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不改变现有路由、API 形状和主要交互的前提下，把 OneAll 前端从技术层结构渐进式演进为 `app + features + shared` 架构，并把所有大型页面纳入统一拆分规则。

**Architecture:** 采用“保留旧入口、迁入新实现、桥接兼容导出”的渐进方案。`src/pages/*` 与 `src/services/*` 在过渡期继续存在，但逐步变成薄入口和桥接层；真实实现按业务域迁入 `src/features/*`，跨域复用能力收敛到 `src/shared/*`。

**Tech Stack:** Vue 3, TypeScript, Vue Router, Pinia, Element Plus, Vitest, Vite

---

## Scope Baseline

本计划覆盖以下大型页面和页面级实现：

- Assets:
  - `src/pages/assets/AssetCenter.vue`
  - `src/pages/assets/AssetModelCenter.vue`
  - `src/pages/assets/AssetModelAdmin.vue`
  - `src/pages/assets/AssetFieldAdmin.vue`
- Probes:
  - `src/pages/probes/ProbeManager.vue`
- Tools:
  - `src/pages/tools/CodeRepository.vue`
  - `src/pages/tools/AccountSync.vue`
  - `src/pages/tools/GrafanaSync.vue`
  - `src/pages/tools/ToolLibrary.vue`
  - `src/pages/tools/IpRegexHelper.vue`
- Detection:
  - `src/pages/detection/OneOffDetection.vue`
  - `src/pages/detection/CertificateDetection.vue`
  - `src/pages/detection/CmdbDomainCheck.vue`
  - `src/pages/detection/utils/detectionUtils.ts`
- Monitoring:
  - `src/pages/monitoring/MonitoringRequestForm.vue`
  - `src/pages/monitoring/MonitoringHistory.vue`
  - `src/pages/monitoring/components/PluginConfigForm.vue`
- Settings:
  - `src/pages/settings/AlertTemplates.vue`
  - `src/pages/settings/PermissionRoleDetail.vue`
  - `src/pages/settings/AlertChannelDetail.vue`
  - `src/pages/settings/Users.vue`
  - `src/pages/settings/AuditLogViewer.vue`
  - `src/pages/settings/Alerts.vue`
  - `src/pages/settings/SystemSettings.vue`
  - `src/pages/settings/AuthIntegration.vue`
- Alerts:
  - `src/pages/alerts/AlertCheckDetail.vue`
  - `src/pages/alerts/AlertEventDetail.vue`
  - `src/pages/alerts/AlertEvents.vue`
  - `src/pages/alerts/AlertChecks.vue`
- Dashboard / Account:
  - `src/pages/dashboard/HomeOverview.vue`
  - `src/pages/dashboard/components/DetectionHoneycomb.vue`
  - `src/pages/profile/UserProfile.vue`
  - `src/pages/auth/Login.vue`

---

### Task 1: Establish Top-Level Architecture Boundaries

**Files:**
- Create: `src/app/`
- Create: `src/features/`
- Create: `src/shared/`
- Modify: `src/main.ts`
- Modify: `src/router/index.ts`
- Modify: `tsconfig.json`
- Test: `pnpm test:unit`

**Step 1: Create the target directory skeleton**

Create:

- `src/app/router/`
- `src/app/stores/`
- `src/app/api/`
- `src/shared/components/`
- `src/shared/composables/`
- `src/shared/utils/`
- `src/shared/types/`
- `src/features/assets/`
- `src/features/probes/`
- `src/features/tools/`
- `src/features/monitoring/`
- `src/features/detection/`
- `src/features/settings/`
- `src/features/alerts/`
- `src/features/dashboard/`
- `src/features/profile/`
- `src/features/auth/`

**Step 2: Keep router imports stable**

Do not change route paths. Keep current route definitions, but prepare them to import feature pages through thin wrappers.

**Step 3: Move app-level stores only**

Target:

- `src/stores/session.ts` -> `src/app/stores/session.ts`
- `src/stores/branding.ts` -> `src/app/stores/branding.ts`
- `src/stores/app.ts` -> `src/app/stores/app.ts`
- `src/stores/theme.ts` -> `src/app/stores/theme.ts`

Leave bridge exports in old paths during transition.

**Step 4: Move global API client**

Target:

- `src/services/apiClient.ts` -> `src/app/api/apiClient.ts`

Keep `src/services/apiClient.ts` as a bridge export until all imports are migrated.

**Step 5: Verify**

Run:

```bash
pnpm test:unit
pnpm build
```

Expected:

- tests pass
- build passes
- no route path changes

---

### Task 2: Extract Shared UI and Utility Layer

**Files:**
- Modify: `src/components/RepositoryPageShell.vue`
- Modify: `src/components/PageWrapper.vue`
- Modify: `src/components/common/PageLoader.vue`
- Modify: `src/components/common/KpiCard.vue`
- Modify: `src/components/CodeEditor.vue`
- Modify: `src/components/ScriptSelectorDialog.vue`
- Modify: `src/components/BaseChart.vue`
- Modify: `src/utils/echarts.ts`

**Step 1: Create shared destinations**

Create:

- `src/shared/components/layout/RepositoryPageShell.vue`
- `src/shared/components/layout/PageWrapper.vue`
- `src/shared/components/feedback/PageLoader.vue`
- `src/shared/components/data/KpiCard.vue`
- `src/shared/components/code/CodeEditor.vue`
- `src/shared/components/scripts/ScriptSelectorDialog.vue`
- `src/shared/components/charts/BaseChart.vue`

**Step 2: Convert old component paths into bridge exports or wrappers**

Keep existing imports working while features migrate.

**Step 3: Centralize chart adapter**

Keep `echarts` registration and runtime adapter in:

- `src/utils/echarts.ts`

Only shared chart component may depend on it directly.

**Step 4: Verify**

Run:

```bash
pnpm test:unit
pnpm build
```

---

### Task 3: Refactor Assets Domain

**Files:**
- Modify: `src/pages/assets/AssetCenter.vue`
- Modify: `src/pages/assets/AssetModelCenter.vue`
- Modify: `src/pages/assets/AssetModelAdmin.vue`
- Modify: `src/pages/assets/AssetFieldAdmin.vue`
- Modify: `src/services/assetsApi.ts`
- Modify: `src/stores/assetModels.ts`
- Create: `src/features/assets/pages/AssetCenterPage.vue`
- Create: `src/features/assets/pages/AssetModelCenterPage.vue`
- Create: `src/features/assets/pages/AssetModelAdminPage.vue`
- Create: `src/features/assets/pages/AssetFieldAdminPage.vue`
- Create: `src/features/assets/components/`
- Create: `src/features/assets/composables/`
- Create: `src/features/assets/api/assetsApi.ts`
- Create: `src/features/assets/mappers/`
- Create: `src/features/assets/types/`

**Step 1: Split AssetCenter by responsibility**

Extract at minimum:

- table/list section
- filters and toolbar
- import flow
- import parsers and row mappers
- sync run drawer / history section
- asset form config and view config

**Step 2: Move assets API into feature**

Target:

- `src/services/assetsApi.ts` becomes bridge
- real implementation moves to `src/features/assets/api/assetsApi.ts`

**Step 3: Move assets store into feature**

Target:

- `src/stores/assetModels.ts` -> `src/features/assets/composables` or `src/features/assets/types` as appropriate

**Step 4: Thin page wrappers**

Each legacy page under `src/pages/assets/*` becomes a thin wrapper around feature page implementation.

**Step 5: Verify**

Run:

```bash
pnpm test:unit
pnpm build
```

---

### Task 4: Refactor Probes Domain

**Files:**
- Modify: `src/pages/probes/ProbeManager.vue`
- Modify: `src/services/probeNodeApi.ts`
- Modify: `src/services/probeMetricsApi.ts`
- Modify: `src/services/probeScheduleExecutionApi.ts`
- Create: `src/features/probes/pages/ProbeManagerPage.vue`
- Create: `src/features/probes/components/`
- Create: `src/features/probes/composables/`
- Create: `src/features/probes/api/`
- Create: `src/features/probes/mappers/`
- Create: `src/features/probes/types/`

**Step 1: Split ProbeManager**

Extract at minimum:

- node list panel
- runtime drawer
- health summary section
- metrics loading composable
- chart option builders

**Step 2: Keep chart rendering isolated**

Page code may build chart options, but actual chart runtime stays in shared chart adapter layer.

**Step 3: Thin wrapper**

- `src/pages/probes/ProbeManager.vue` becomes a wrapper

**Step 4: Verify**

Run:

```bash
pnpm test:unit
pnpm build
```

---

### Task 5: Refactor Tools Domain

**Files:**
- Modify: `src/pages/tools/CodeRepository.vue`
- Modify: `src/pages/tools/AccountSync.vue`
- Modify: `src/pages/tools/GrafanaSync.vue`
- Modify: `src/pages/tools/ToolLibrary.vue`
- Modify: `src/pages/tools/IpRegexHelper.vue`
- Modify: `src/services/toolsApi.ts`
- Modify: `src/services/codeRepositoryApi.ts`
- Modify: `src/services/scriptExecutor.ts`
- Modify: `src/stores/codeDirectories.ts`
- Modify: `src/stores/scriptPlugins.ts`
- Create: `src/features/tools/pages/`
- Create: `src/features/tools/components/`
- Create: `src/features/tools/composables/`
- Create: `src/features/tools/api/`
- Create: `src/features/tools/mappers/`
- Create: `src/features/tools/types/`

**Step 1: Split CodeRepository into feature modules**

Extract at minimum:

- repository list / filters
- version upload workflow
- editor/preview surface
- execution panel
- formatting/highlight helpers

**Step 2: Split integration-heavy tool pages**

Extract config forms and submission logic from:

- `AccountSync.vue`
- `GrafanaSync.vue`

**Step 3: Make `ToolLibrary.vue` a page shell**

List rendering, plugin metadata mapping and action handlers must not live in one file.

**Step 4: Verify**

Run:

```bash
pnpm test:unit
pnpm build
```

---

### Task 6: Refactor Monitoring and Detection Domains

**Files:**
- Modify: `src/pages/monitoring/MonitoringRequestForm.vue`
- Modify: `src/pages/monitoring/MonitoringHistory.vue`
- Modify: `src/pages/monitoring/components/PluginConfigForm.vue`
- Modify: `src/pages/monitoring/components/HistoryFilters.vue`
- Modify: `src/pages/monitoring/components/RequestTimeline.vue`
- Modify: `src/pages/detection/OneOffDetection.vue`
- Modify: `src/pages/detection/CertificateDetection.vue`
- Modify: `src/pages/detection/CmdbDomainCheck.vue`
- Modify: `src/pages/detection/utils/detectionUtils.ts`
- Modify: `src/services/monitoringApi.ts`
- Modify: `src/services/detectionApi.ts`
- Create: `src/features/monitoring/pages/`
- Create: `src/features/monitoring/components/`
- Create: `src/features/monitoring/composables/`
- Create: `src/features/monitoring/api/`
- Create: `src/features/monitoring/mappers/`
- Create: `src/features/detection/pages/`
- Create: `src/features/detection/components/`
- Create: `src/features/detection/composables/`
- Create: `src/features/detection/api/`
- Create: `src/features/detection/mappers/`

**Step 1: MonitoringRequestForm split**

Separate:

- form state orchestration
- request payload mapping
- approval / timeline display
- plugin config editing blocks

**Step 2: MonitoringHistory split**

Separate:

- filter state
- result table
- detail drawer
- query parameter mapping

**Step 3: Detection pages split**

Consolidate reusable detection pieces already present under feature-local structure. Move generic result/config logic out of page files.

**Step 4: Keep page wrappers stable**

Legacy `src/pages/monitoring/*` and `src/pages/detection/*` remain route entry wrappers.

**Step 5: Verify**

Run:

```bash
pnpm test:unit
pnpm build
```

---

### Task 7: Refactor Settings, Alerts, Dashboard, Profile, and Auth

**Files:**
- Modify: `src/pages/settings/*.vue`
- Modify: `src/pages/alerts/*.vue`
- Modify: `src/pages/dashboard/HomeOverview.vue`
- Modify: `src/pages/dashboard/components/DetectionHoneycomb.vue`
- Modify: `src/pages/profile/UserProfile.vue`
- Modify: `src/pages/auth/Login.vue`
- Modify: `src/services/settingsApi.ts`
- Modify: `src/services/alertsApi.ts`
- Modify: `src/services/dashboardApi.ts`
- Modify: `src/services/profileApi.ts`
- Modify: `src/stores/pluginConfigs.ts`
- Create: `src/features/settings/`
- Create: `src/features/alerts/`
- Create: `src/features/dashboard/`
- Create: `src/features/profile/`
- Create: `src/features/auth/`

**Step 1: Settings split**

Each settings page must become:

- page shell
- table/detail/form components
- per-page composable
- settings API adapters

**Step 2: Alerts split**

Extract:

- list page logic
- detail page logic
- event/check mappers

**Step 3: Dashboard split**

Move page-specific aggregations and chart/honeycomb transforms into feature-local mappers/composables.

**Step 4: Account pages cleanup**

Refactor `UserProfile.vue` and `Login.vue` into smaller page + form patterns for consistency.

**Step 5: Verify**

Run:

```bash
pnpm test:unit
pnpm build
```

---

### Task 8: Converge and Remove Transitional Debt

**Files:**
- Modify: `src/pages/**`
- Modify: `src/services/**`
- Modify: `src/stores/**`
- Modify: `src/components/**`
- Review: `src/router/index.ts`
- Review: `src/main.ts`

**Step 1: Audit old entry layers**

Identify which old files are now only wrappers or bridge exports.

**Step 2: Keep only intentional wrappers**

Allowed in legacy directories:

- route entry wrappers
- bridge exports needed for staged migration

Not allowed:

- duplicated business logic
- domain-specific data mapping
- domain-specific request payload assembly

**Step 3: Remove dead bridges**

After all imports are migrated, remove transitional bridge files in batches.

**Step 4: Final verification**

Run:

```bash
pnpm test:unit
pnpm build
```

Expected:

- tests pass
- build passes
- all large-page implementations live in `src/features/*`
- `src/pages/*` is thin
- `src/services/*` is either bridge or removed
- `src/components/*` contains only cross-domain shared components or bridge exports
