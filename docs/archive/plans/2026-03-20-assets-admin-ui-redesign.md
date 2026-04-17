# 资产中心管理页（模型管理 + 字段管理）实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重设计「资产模型管理」和「字段管理」两个页面的前端 UI，使其与资产中心主列表页风格一致，同时符合当前的业务约束和交互要求。

**Architecture:** 仅在前端层面调整 `AssetModelAdmin.vue` 与 `AssetFieldAdmin.vue` 的布局、文案和样式，不引入新的后端 API。尽量复用现有的 `RepositoryPageShell` 布局和 `AssetCenter.vue` 中的通用样式结构（filters + table + footer）。

**Tech Stack:** Vue 3 + TypeScript + Element Plus，现有的 OneAll 前端组件与样式体系。

---

### Task 1: 对齐模型管理页 Shell 与顶部工具区

**Files:**
- Modify: `frontend/src/pages/assets/AssetModelAdmin.vue`

**Steps:**
1. 将 `RepositoryPageShell` 的 `root-title` 修改为「资产中心」，`section-title` 修改为「模型管理」。
2. 在 `#actions` 插槽中保留「新建模型」和「刷新」两个按钮，其中「新建模型」为 primary，「刷新」为 plain，去掉当前 header 内部重复的刷新按钮区域，避免两处刷新入口。
3. 在 `section.panel` 内顶部增加一块类似 `asset-filters` 的区域：左侧显示标题和描述，右侧预留搜索框和分类筛选的占位（如果暂时不实现过滤逻辑，可以先只加搜索输入并在脚本中添加对应的 `ref` 和简单的前端过滤）。

### Task 2: 调整模型列表表格与操作列

**Files:**
- Modify: `frontend/src/pages/assets/AssetModelAdmin.vue`

**Steps:**
1. 为模型列表外层增加与资产列表相同的容器结构，例如使用类名 `asset-table` 和 `asset-table__card` 包裹 `el-table`，以获得一致的留白和阴影效果。
2. 确认表格列为：模型名称（label）、标识（key）、分类（category）、字段数（fields.length）、唯一键（unique_key，展示为用 ` / ` 拼接的字符串，未配置时显示“未配置”）、脚本状态（已绑定 / 未绑定）。
3. 重构「操作」列：保留 `编辑模型` 和 `同步资产` 两个主要按钮；将「下载当前脚本」「下载模板」「上传脚本」三个动作收敛到一个 `脚本` 下拉菜单（`el-dropdown`）中，避免一整排文本按钮造成视觉噪音。
4. 确保相关的点击事件仍然调用当前已有的 `openEditModelDialog`、`triggerModelSync`、`downloadCurrentScript`、`downloadScriptTemplate`、`triggerScriptUpload`，只是调整触发方式。

### Task 3: 微整理模型编辑对话框的排版和文案

**Files:**
- Modify: `frontend/src/pages/assets/AssetModelAdmin.vue`

**Steps:**
1. 保持当前字段结构不变：标识、名称、分类 + 字段定义（表格）+ 唯一键字段选择器。
2. 对对话框标题进行规范：
   - 创建时为「新建资产模型」。
   - 编辑时为「编辑资产模型 · {label 或 key}」。
3. 在「唯一键字段」下方保留提示文案，但强调“只能从本模型字段中选择，用于避免资产重复同步”，无需更改逻辑。
4. 检查字段表格的输入控件（Key、名称、类型）是否与资产模型的后端定义一致，不调整 payload 结构，仅在 placeholder 和 label 上微调文案。

### Task 4: 对齐字段管理页 Shell 与列表区域

**Files:**
- Modify: `frontend/src/pages/assets/AssetFieldAdmin.vue`

**Steps:**
1. 将 `RepositoryPageShell` 的 `root-title` 确认/调整为「资产中心」，`section-title` 为「字段管理」。
2. 为当前的 `section.panel` 增加与资产列表类似的顶部说明区域：标题「资产字段配置」，说明文案保持现有语义。
3. 确认主表格外层使用统一的 panel 样式和适当的 margin，使其与模型管理页和资产列表的卡片观感一致（若需要，可复用 `AssetModelAdmin.vue` 中的 panel 样式类）。
4. 在表格列中，将「字段管理」列的列名改为「管理字段」，保持按钮文案为「编辑」，并在右侧保留“X 个字段”的提示。

### Task 5: 重命名“扩展字段”为“管理字段”并保持内置字段只读

**Files:**
- Modify: `frontend/src/pages/assets/AssetFieldAdmin.vue`

**Steps:**
1. 在字段管理对话框中，将提醒文案和标题中的「扩展字段」统一改为「管理字段」，包括：
   - 顶部 `el-alert` 提示文案。
   - 右侧表格标题从「扩展字段」改为「管理字段」。
2. 保持左侧表格标题为「内置字段（只读）」以及现有逻辑：从 `assetTypes` 中读取字段列表，仅做展示。
3. 确认右侧字段编辑表格仍然支持：字段 Key、显示名称、类型（string/number/boolean/enum）、枚举选项、必填、列表展示、删除操作；不变更现有的数据结构，只调整 label 文案。
4. 暂时不打通实际的保存 API，保留当前的 TODO 提示，但文案改为“管理字段保存暂时未完全打通，此处仅做前端演示”，以与“管理字段”命名保持一致。

### Task 6: 轻量前端自检与构建检查

**Files:**
- No file modifications; run commands.

**Steps:**
1. 在 `frontend` 目录下运行 `npm run lint` 或 `npm run build`（若项目存在已知构建问题，可至少运行 `npm run type-check` 或 `npm run test:unit`）以检查是否有明显的语法错误。
2. 启动前端开发服务器 `npm run dev`，手动访问：
   - `/assets/admin/models`（模型管理）。
   - `/assets/admin/fields`（字段管理）。
3. 在浏览器中验证：
   - 两个页面的整体布局与资产列表页在视觉上保持一致。
   - 模型管理操作列收敛，脚本相关操作通过下拉菜单触发。
   - 字段管理对话框中的「管理字段」命名和行为符合预期，内置字段只读，右侧管理字段可编辑。
