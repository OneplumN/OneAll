# 资产中心导航与模型管理改造 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构前端导航与资产模型配置入口，将资产相关配置从全局设置迁移到资产中心域，并按“资产管理 / 内置模型 / 扩展模型”三个一级导航组织资产功能。

**Architecture:** 保持现有前端路由与权限体系不变，主要通过调整 `NAV_GROUPS` 与路由 `meta.navGroup`/`navLabel` 来重组导航；资产模型管理仍复用现有 API，但从 `/settings/system` 抽出到新的“资产管理”页面。扩展模型菜单项通过调用后端 `/api/assets/models` 动态生成，统一路由到通用资产视图组件。

**Tech Stack:** Vue 3 + Vue Router, TypeScript, Element Plus, 现有 `assetsApi` 服务与后端 Django REST API。

---

### Task 1: 调整前端导航分组结构

**Files:**
- Modify: `frontend/src/router/index.ts`

**Step 1: 定义新顶层导航分组**

- 在 `NAV_GROUPS` 中新增三个组：
  - `assets-admin`（label: `资产管理`，permission 复用 `assets.module.access`）
  - `assets-core`（label: `内置模型`）
  - `assets-ext`（label: `扩展模型`）
- 将原有 `assets` 组保留一段时间（用于过渡），之后可以移除或改名为 `assets-core`，本次改造中直接将原有 `assets` 组拆解为上述三个新组。

**Step 2: 将现有资产路由挂到新分组**

- 更新以下资产路由的 `meta.navGroup`/`navLabel`：
  - `/assets/domain`、`/assets/zabbix` → `navGroup: 'assets-core'`，`navLabel` 为对应中文名称。
  - `/assets/ipmp`、`/assets/workorder-hosts` 以及 `/assets/custom` 或新的扩展模型路由 → `navGroup: 'assets-ext'`。
- 新增一个“资产管理”入口路由（下一 Task 里实现页面），如 `/assets/admin/models`，`meta.navGroup: 'assets-admin'`，`navLabel: '模型管理'`。

**Step 3: 运行前端类型检查和构建**

- 在 `frontend` 目录运行：
  - `npm run lint`（如果项目使用）
  - `npm run build` 或 `npm run test`（至少保证路由文件编译通过）。

### Task 2: 迁移资产模型管理 UI 到“资产管理”域

**Files:**
- Modify: `frontend/src/pages/settings/SystemSettings.vue`
- Modify: `frontend/src/pages/settings/components/SettingsTabs.vue`
- Create: `frontend/src/pages/assets/AssetModelAdmin.vue`（新建页面组件）
- Modify: `frontend/src/router/index.ts`（为新页面添加路由）

**Step 1: 梳理现有资产模型相关 UI 和数据**

- 在 `SystemSettings.vue`/`SettingsTabs.vue` 中查找与 `assetTypes`、`AssetTypeSummary`、`integrations.assets` 相关的逻辑：
  - 表单字段 `integrations.assets.types`。
  - 从 `assetsApi` 加载资产类型列表的逻辑（`fetchAssetTypes`）。
- 确定哪些是“全局资产规则”（如旧的 unique_fields 配置），哪些是“模型管理”本身（与 `AssetModel` 概念重叠）。

**Step 2: 新建资产模型管理页面**

- 新建 `AssetModelAdmin.vue`，内容可以复用当前 SystemSettings 中“资产相关”那一部分 UI，但：
  - 页面外壳使用现有的 Layout 组件（类似 AssetCenter 或其他主页面），而不是 SystemSettings 的 Shell。
  - 只保留与资产模型配置和脚本管理、同步相关的区域。
  - 通过 `assetsApi` 使用已有的模型管理接口，而不是 `integrations.assets.types`。

**Step 3: 在“资产管理”组添加路由和导航项**

- 在 `router/index.ts` 中添加：
  - 路由 `/assets/admin/models` → 组件 `AssetModelAdmin.vue`。
  - 对应 `NAV_GROUPS` 中 `assets-admin` 组下的菜单项 `{ label: '模型管理', path: '/assets/admin/models', permission: 'assets.records.manage' }`。

**Step 4: 将 SystemSettings 中资产配置改为指向新页面（可选/过渡）**

- 在 `SettingsTabs.vue` 中：
  - 保留原有资产卡片，但改成提示文字 + 按钮 “前往资产管理中心”，点击跳转到 `/assets/admin/models`。
  - 或直接移除资产相关 Tab（如果你确认不再需要从“全局设置”入口配置资产）。

**Step 5: 手动回归测试**

- 启动后端和前端：
  - 后端：`python manage.py runserver 0.0.0.0:8000`。
  - 前端：`npm run dev`。
- 验证：
  - 新的“资产管理 / 模型管理”入口可见，权限控制正常。
  - 在新页面创建/更新模型、上传脚本、触发同步后，后端日志和数据与之前 SystemSettings 中的行为一致。

### Task 3: 为扩展模型生成动态菜单项

**Files:**
- Modify: `frontend/src/router/index.ts`（或导航构建相关文件）
- Modify: `frontend/src/services/assetsApi.ts`（如需导出 `fetchAssetModels` 给导航使用）

**Step 1: 确定导航渲染位置**

- 找到负责渲染侧边导航的组件（例如 `src/components/layout/AppSideNav.vue` 或类似）。
- 查看它如何消费 `NAV_GROUPS`（静态）并渲染菜单。

**Step 2: 为扩展模型增加动态子项**

- 方案：保持 `NAV_GROUPS` 静态定义，但允许某个组（`assets-ext`）的 `items` 在运行时通过 store/组合式函数注入“扩展模型”菜单。
- 实现思路：
  - 在应用启动时（或首次访问资产侧边栏时）调用 `fetchAssetModels()`。
  - 过滤出 `is_active` 的模型，构造菜单项：
    - `label: model.label || model.key`
    - `path: '/assets/model/' + model.key`
    - `permission: 'assets.records.view'`（或根据模型级权限扩展）。
  - 将这些菜单项挂到 `assets-ext` 组下，与 IPMP/工单菜单并列。

**Step 3: 定义通用扩展模型路由**

- 在 `routes` 中添加：

```ts
{
  path: '/assets/model/:modelKey',
  name: 'assets-model-generic',
  component: () => import('../pages/assets/AssetModelCenter.vue'),
  meta: {
    ...authMeta('assets-ext', '扩展模型'),
    permission: 'assets.records.view',
    layoutFlat: true
  }
}
```

- 在 `AssetModelCenter.vue` 中优先读取 `route.params.modelKey`，如果存在，则直接选中对应模型并加载资产列表；如果不存在，则保留原有“从左侧模型列表选择”的交互作为兜底。

**Step 4: 手动测试扩展模型导航**

- 新建一个模型（如 `ali-account`），绑定脚本并成功同步至少一条数据。
- 确认在“扩展模型”组下出现 `阿里云账号资产`（或模型 label），点击后：
  - 路由跳转到 `/assets/model/ali-account`。
  - 页面直接展示该模型的数据列表。

### Task 4: 基础回归与文档更新

**Files:**
- Modify: `README.md` 或 `docs/` 下已有架构说明文档（如有）
- Modify: `frontend` 下可能存在的导航/资产相关说明文档

**Step 1: 快速回归导航与权限**

- 随机检查以下入口：
  - 监控、一次性检验、告警、探针等组菜单仍然正常显示/跳转。
  - 未授权用户访问资产相关菜单时，仍然按既有逻辑返回 403 或提示无权限。

**Step 2: 更新文档**

- 在 `README.md` 或专门的 `docs` 中添加一小节：
  - 描述资产中心的新导航结构（资产管理 / 内置模型 / 扩展模型）。
  - 标明资产模型管理的入口：“资产管理 -> 模型管理”，不再从“系统设置 -> 全局设置”里配置。

**Step 3: 评估是否可以删除旧逻辑（后续任务）**

- 标记出仍然在使用的旧 `integrations.assets` 配置以及“自定义资产”旧入口 `/assets/custom`，后续可以在单独任务里做彻底清理，避免双通路配置。

