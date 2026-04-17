# 资产中心交互与体验改造计划（主视图 + 扩展模型）

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不破坏后端 API 与现有业务逻辑的前提下，系统性优化资产中心主视图（AssetCenter.vue）和扩展模型视图（AssetModelCenter.vue）的交互与体验：过滤器布局改进、导入交互统一、权限行为对齐、扩展模型表单类型化等，一次性落地。

**Architecture:** 仅修改前端 Vue 代码与样式，不调整后端接口。保持「配置驱动视图」的整体结构（ASSET_VIEW_DEFINITIONS + AssetModel），在此基础上调整模板结构与少量交互逻辑。

**Tech Stack:** Vue 3 + TypeScript + Element Plus，现有 OneAll 前端组件与样式系统。

---

### Task 1: 资产中心 filters 区布局改造（平行布局）

**Files:**
- Modify: `frontend/src/pages/assets/AssetCenter.vue`
- Modify: `frontend/src/pages/assets/AssetModelCenter.vue`

**Steps:**
1. 在 `AssetCenter.vue` 中，将 `.filters-right` 的布局从 column 改为 row，使资产类型提示、筛选器和搜索框在同一水平行内以 flex 方式平铺：
   - `flex-direction: row; align-items: center; flex-wrap: wrap; margin-left: auto; gap` 适当调整。
2. 保持 `filters-left` 仍为水平排列的操作按钮区域。
3. 在 `AssetModelCenter.vue` 中同样调整 `.filters-right` 的样式，使扩展模型视图的 filters 区与主视图保持一致的平行布局。

---

### Task 2: 主筛选 + 更多筛选（Zabbix 视图）

**Files:**
- Modify: `frontend/src/pages/assets/AssetCenter.vue`

**Steps:**
1. 在模板的 `filters-right` 内，将 `showInterfaceAvailableFilter` 对应的「接口可用性」筛选器从主行移除，改为收纳在「更多筛选」弹出层中，仅在 `viewKey === 'zabbix-host'` 时显示：
   - 新增一个 `el-popover`，reference 是一个「更多筛选」按钮。
   - popover 内容中渲染 `interfaceAvailableFilter` 的 `el-select`。
2. 保留其他筛选器在主行：
   - 域名：网络类型 + 搜索。
   - Zabbix：Proxy + 搜索 + 「更多筛选」。
   - 工单：在线状态 + Proxy + 搜索。
   - IPMP：应用状态 + 搜索。
3. 不改变任何过滤逻辑，仅调整渲染位置和 UI 结构。

---

### Task 3: 资产详情弹窗信息分区（轻量视觉改造）

**Files:**
- Modify: `frontend/src/pages/assets/AssetCenter.vue`

**Steps:**
1. 在资产详情对话框中，将「模型字段」区块用一个更明确的标题区隔，例如将 `el-divider` 的文案调整为「模型字段」或「业务字段」。
2. 保持现有「基础信息」部分（名称/来源/External ID/资产状态/创建时间/修改时间），暂不大改字段顺序，避免引入回归。
3. 为后续「审计信息」/生命周期扩展预留结构（例如在模板中添加注释或预留空的 `el-descriptions` 容器），不在本轮中填充新的字段。

---

### Task 4: 导入交互微调（主视图与扩展模型统一）

**Files:**
- Modify: `frontend/src/pages/assets/AssetCenter.vue`
- Modify: `frontend/src/pages/assets/AssetModelCenter.vue`

**Steps:**
1. 在两个页面的导入对话框中，在表格/空状态之前增加一段简要导入状态文案：
   - 当有预览行时：显示「已解析 X 条记录，准备导入」。
   - 当存在错误时：在错误列表前增加一句「共 Y 条错误，已显示前 N 条」（如果有截断）。
2. 在 `AssetModelCenter.vue` 中，将导入失败时的错误展示逻辑从 `JSON.stringify(errors)` 改为使用与主视图一致的格式化逻辑：
   - 实现一个局部的 `formatImportServerErrors` 方法，接收 `ImportAssetsResponse.errors`，输出「第 n 条：xxx」形式的数组。
   - 使用该函数替换现有的 `serverErrors` 构造逻辑。
3. 保持后端返回 `200 + errors` 时的处理逻辑与主视图相同：导入完成但部分失败时，toast 提示「成功 X 条，失败 Y 条」，并在对话框中列出具体错误。

---

### Task 5: 扩展模型表单行为与权限对齐

**Files:**
- Modify: `frontend/src/pages/assets/AssetModelCenter.vue`

**Steps:**
1. 已完成但需确认的行为：
   - 确认 `canCreate` 计算属性存在，并在模板中禁用「新增 / 批量导入」按钮；在 `openCreateDialog` / `openImportDialog` 中添加「暂无新增权限」提示。
   - 确保 `canManage` 仍然只控制「同步资产」按钮。
2. 将扩展模型 filters-right 的搜索行为与主视图对齐：
   - 保留 `@keyup.enter="reloadAssets"` 和 `@clear="handleKeywordClear"` 的交互。
3. 为扩展模型导入模板下载逻辑增加一行注释（如使用 `#` 开头说清首行含义），如果当前 CSV 模板处理允许安全忽略这类注释行；否则只在导入弹窗 UI 中增加说明，不改模板内容。

---

### Task 6: 路由切换与模型切换体验确认（扩展模型）

**Files:**
- Confirm: `frontend/src/pages/assets/AssetModelCenter.vue`
- Confirm: `frontend/src/layouts/MainLayout.vue`

**Steps:**
1. 确认之前新增的 watch 逻辑在路由 `modelKey` 变化时能够：
   - 在必要时重新加载模型列表；
   - 根据 `model.key` 设置新的 `activeModelId`；
   - 重置分页到第一页并调用 `reloadAssets()`。
2. 手动在浏览器中测试侧边导航中不同扩展模型之间切换，验证：
   - 顶部「当前模型」名称与唯一键提示同步更新；
   - 表头字段、列表数据跟随变化，不再停留在旧模型。

---

### Task 7: 局部 lint 自检与手动验证

**Files:**
- No new files; run commands.

**Steps:**
1. 在 `frontend` 目录下针对改动文件运行 ESLint：
   - `npx eslint src/pages/assets/AssetCenter.vue src/pages/assets/AssetModelCenter.vue`.
2. 启动前端开发服务器：
   - `npm run dev`。
3. 在浏览器中手动验证：
   - 「资产中心 -> 域名/Zabbix/IPMP/工单」视图：
     - filters 区的布局为水平平铺，Zabbix 视图出现「更多筛选」按钮，接口可用性筛选位于弹出层内；
     - 导入对话框展示解析记录数和错误统计。
   - 「资产中心 -> 扩展模型」视图：
     - filters 区与主视图布局一致，新增/导入按钮遵守权限控制；
     - 导入错误展示格式与主视图相同；  
     - 切换不同扩展模型左侧菜单时，内容正确刷新。
