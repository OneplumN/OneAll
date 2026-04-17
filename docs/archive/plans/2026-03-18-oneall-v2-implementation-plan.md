# OneAll v2 域重构 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Incrementally refactor OneAll into a leaner v2 by first deleting obsolete modules (analytics, knowledge, external monitoring integrations, heavy settings) and then introducing a clean domain structure centered on probes, monitoring, assets, tools, and alerts.

**Architecture:** Start by removing unused/legacy Django apps and frontend routes to reduce surface area and risk, then add a dedicated `alerts` domain, refactor `monitoring/assets/tools/settings` into the new boundaries defined in the v2 design, and finally adjust data flows so probes/monitoring emit events that alerts evaluates and notifies on. Keep the gRPC probe protocol stable and prefer small, verifiable changes with tests at each step.

**Tech Stack:** Django + DRF (backend), Celery + Redis (jobs), MySQL (primary DB), Go (probes), Vue 3 + Vite + Element Plus (frontend), Docker/docker-compose (dev/deploy).

---

## Part 1: 删除老模块与重集成能力（瘦身优先）

### Task 1: 后端移除 analytics 应用

**Files:**
- Modify: `backend/src/core/settings.py`（或等价 Django settings，更新 `INSTALLED_APPS`）
- Modify: `backend/src/core/urls.py`（如有 `analytics` 路由）
- Inspect/Modify: `backend/src/apps/analytics/*`
- Modify: `backend/src/apps/__init__.py`（如有集中 app 注册）
- Modify: `backend/pytest.ini` / `backend/tests` 中引用 analytics 的部分
- Create: `backend/src/apps/analytics/migrations/9999_drop_analytics_tables.py`（one-off migration，用于删除表，后续可删除整个目录）

**Step 1: 找出所有 analytics 引用**
- Run: `cd backend && rg "analytics" -n`
- 记录：settings、urls、Celery、tests 中出现的位置。

**Step 2: 从 INSTALLED_APPS 中移除 analytics**
- 编辑 Django settings（例如 `backend/src/core/settings.py`）：
  - 删除 `apps.analytics`（或等价路径）条目。

**Step 3: 从 URL 路由中移除 analytics API**
- 编辑 `backend/src/core/urls.py`（或 API 路由聚合文件）：
  - 删除 `analytics` 相关的 `include`/`router.register` 条目。

**Step 4: 清理 Celery 任务与信号注册**
- 在 `backend/src/apps/analytics/tasks.py`、`apps.py` 中确认无跨 app 信号依赖；
- 如有在其他 app 中引用 analytics.tasks 的地方，先注释/删除这些调用。

**Step 5: 添加 drop tables migration（可选保守路径）**
- 在 `backend/src/apps/analytics/migrations/` 新建一个 migration 文件：
  - 使用 `migrations.RunSQL` 来 drop analytics 相关表；
  - 或使用 Django `DeleteModel` 等操作删除模型。
- 确认 migration 只影响 analytics 相关表。

**Step 6: 运行后端测试与迁移**
- Run: `cd backend && pytest`（或最小范围 `pytest tests/apps/analytics` 确认不会被执行）
- Run: `cd backend/src && python manage.py makemigrations`（确认无意外变更）；
- Run: `cd backend/src && python manage.py migrate`。

**Step 7: 清理代码目录**
- 在确认迁移已在目标环境执行后：
  - 删除 `backend/src/apps/analytics` 目录（代码与 migrations）；
  - 再次运行 `rg "analytics"` 确认无残留引用。

**Step 8: 更新文档**
- 修改 `[README.md](/mnt/d/workspace/OneAll/README.md)` 中的功能模块列表，移除独立“统计分析”模块描述或说明其已合并为轻量统计。

---

### Task 2: 后端移除 knowledge 知识库应用

**Files:**
- Modify: `backend/src/core/settings.py`（INSTALLED_APPS）
- Modify: `backend/src/core/urls.py`（knowledge API 路由）
- Inspect/Modify: `backend/src/apps/knowledge/*`
- Modify: `backend/pytest.ini` / `backend/tests` 中引用 knowledge 的部分
- Create: `backend/src/apps/knowledge/migrations/9999_drop_knowledge_tables.py`（用于删除表）

**Step 1: 搜索 knowledge 引用**
- Run: `cd backend && rg "knowledge" -n`
- 记录 app、urls、tests、权限/菜单配置中的使用点。

**Step 2: 从 INSTALLED_APPS 中移除 knowledge**
- 删除 settings 中的 `apps.knowledge` 条目。

**Step 3: 从 URL 路由中移除 knowledge**
- 删除 core urls 中的 `knowledge` 子路由/Router 注册。

**Step 4: 移除管理后台与权限中相关引用**
- 如有 Django admin 注册 knowledge models，删除对应 admin 注册；
- 如权限/菜单在 settings 或 core 中有硬编码（如 `knowledge_*`），移除/标注废弃。

**Step 5: 添加 drop tables migration**
- 在 `backend/src/apps/knowledge/migrations/` 下新增 migration：
  - 删除知识库相关模型或直接 drop 表；
  - 确保不影响其他 app。

**Step 6: 运行迁移与测试**
- Run: `cd backend/src && python manage.py makemigrations`
- Run: `cd backend/src && python manage.py migrate`
- Run: `cd backend && pytest`（至少跑核心测试集）。

**Step 7: 删除 knowledge 代码目录**
- 删除 `backend/src/apps/knowledge` 目录；
- Run: `cd backend && rg "knowledge" -n` 确认无残留引用。

**Step 8: 更新文档与菜单配置**
- 在 README 的功能模块表中移除“知识库”模块；
- 前端菜单/权限配置中移除知识库入口（见 Task 5）。

---

### Task 3: 移除 monitoring.integrations 外部监控集成（Zabbix/Prometheus）

**Files:**
- Inspect/Modify: `backend/src/apps/monitoring/integrations/*`
- Modify: `backend/src/apps/monitoring/api/*`（移除相关 API）
- Modify: `backend/src/apps/monitoring/models/*`（删除仅服务于外部集成的模型）
- Modify: `backend/src/apps/monitoring/services/*`（移除 Zabbix/Prometheus 逻辑）
- Modify: `backend/src/apps/monitoring/tasks.py`
- Modify: 任何引用 `monitoring.integrations` 的其他文件

**Step 1: 梳理 integrations 的功能边界**
- 阅读 `backend/src/apps/monitoring/integrations` 目录结构；
- 记录：
  - 哪些 models 仅用于外部监控；
  - 哪些 API endpoint 只为 Zabbix/Prometheus 提供数据；
  - 哪些 Celery 任务是同步外部监控的。

**Step 2: 删除/注释 integrations 目录及引用**
- 删除 `monitoring/integrations` 子目录；
- 在 `monitoring/api`、`services`、`tasks` 中删除对 integrations 的导入与调用；
- 确认监控任务内部逻辑（拨测任务）不依赖这些代码。

**Step 3: 清理外部监控相关模型和迁移**
- 对仅服务外部集成的 models：
  - 添加删除这些 models 的 migration；
  - 或通过 RunSQL drop 对应表。

**Step 4: 清理 API 路由**
- 删除用于查询 Zabbix/Prometheus 数据的 API endpoint；
- 更新 swagger/openapi 描述（如有）。

**Step 5: 测试监控核心流程**
- Run: `cd backend && pytest tests/apps/monitoring`（聚焦监控任务相关用例）；
- 如有端到端测试，运行一次完整拨测流程测试。

---

### Task 4: 精简 settings 应用中的外部集成配置

**Files:**
- Inspect/Modify: `backend/src/apps/settings/models.py`
- Inspect/Modify: `backend/src/apps/settings/services.py`
- Inspect/Modify: `backend/src/apps/settings/tasks.py`
- Inspect/Modify: `backend/src/apps/settings/api/*`
- Inspect/Modify: `backend/src/apps/settings/data/*`（预置数据）
- Inspect/Modify: `backend/src/apps/settings/utils.py`

**Step 1: 识别外部集成相关模型与 API**
- 搜索 ITSM/Zabbix/Prometheus/LDAP 等关键词：
  - Run: `cd backend && rg "Zabbix" -n`
  - Run: `cd backend && rg "Prometheus" -n`
  - Run: `cd backend && rg "ITSM" -n`
  - Run: `cd backend && rg "LDAP" -n`

**Step 2: 标记待删除模型与字段**
- 在 models 中标注哪些只为外部集成服务；
- 规划迁移：
  - 删除不再需要的 models；
  - 或在 v2 中保留少量通用「外部系统配置」模型但不对外暴露。

**Step 3: 删除/废弃 API 与服务逻辑**
- 删除提供外部监控/ITSM/LDAP 专用的 API；
- 清理 services/tasks 中关联逻辑；
- 确保不会影响基础系统设置（用户/角色/平台信息）。

**Step 4: 添加 migration 并执行**
- 编写 migrations 删除对应模型/字段；
- Run: `cd backend/src && python manage.py makemigrations && python manage.py migrate`。

**Step 5: 更新 README 与配置文档**
- 在 README 的配置部分移除对这些外部集成的描述；
- 在 docs（如 `specs` 或 `dream.md`）中可以新增一小段说明「v2 不再内置这些集成，改为通过可扩展机制支持」。

---

### Task 5: 前端移除 analytics/knowledge/integrations 页面与导航

**Files:**
- Modify: `frontend/src/router` 或路由定义文件（根据项目结构）
- Modify: `frontend/src/pages/analytics/*`
- Modify: `frontend/src/pages/knowledge/*`
- Modify: `frontend/src/pages/integrations/*`
- Modify: 主导航/菜单组件（通常在 `frontend/src/layout` 或类似位置）
- Modify: 相关的 i18n/菜单配置文件（如有）

**Step 1: 删除路由定义**
- 在路由配置文件中：
  - 删除 `analytics`、`knowledge`、`integrations` 相关 route；
  - 确保没有 lazy-load 导入这些页面。

**Step 2: 删除菜单项**
- 在侧边栏/顶部导航组件中移除对应菜单项；
- 确保菜单高亮逻辑不依赖这些 route 名称。

**Step 3: 清理页面组件**
- 删除 `frontend/src/pages/analytics`、`knowledge`、`integrations` 目录；
- Run: `cd frontend && rg "analytics" -n` / `"knowledge"` / `"integrations"` 确认无残留引用。

**Step 4: 更新 Dashboard/Monitoring 页面**
- 删除其中对 Zabbix/Prometheus 或知识库的跳转入口；
- 暂时保留简单占位区域，待后续 Task 中重构 Dashboard。

**Step 5: 运行前端测试**
- Run: `cd frontend && pnpm test`（或 `pnpm test:unit` / `pnpm test:e2e`）
- 手动运行开发环境（如 `pnpm dev`），快速点一遍导航确保无 404/报错。

---

### Task 6: 清理文档、菜单配置与 CI 配置中对老模块的引用

**Files:**
- Modify: `[README.md](/mnt/d/workspace/OneAll/README.md)`
- Modify: `[dream.md](/mnt/d/workspace/OneAll/dream.md)`
- Modify: `specs/*`（如有引用 analytics/knowledge/integrations）
- Modify: CI 配置、docker-compose 相关描述（例如 probes/monitoring/analytics 容器）

**Step 1: 搜索关键字**
- Run: `cd /mnt/d/workspace/OneAll && rg "知识库" -n`
- Run: `cd /mnt/d/workspace/OneAll && rg "统计分析" -n`
- Run: `cd /mnt/d/workspace/OneAll && rg "Zabbix" -n`
- 相应定位在文档和配置中的段落。

**Step 2: 更新 README 和 dream.md**
- 在 README 功能模块表中：
  - 移除知识库、统计分析、外部监控集成；
  - 或简单标注为「已从 v2 中移除」；
- 在 dream.md 中：
  - 将知识库/代码管理/外部监控集成标记为「迁出/后续可选扩展」。

**Step 3: 调整 CI 与 docker-compose 描述**
- 确认 docker-compose 中没有专门为 analytics/knowledge/external-monitoring 提供的服务；
- 如有，删除对应 service/volume/config。

---

## Part 2: 引入新域与重构（alerts + monitoring/assets/tools/settings）

### Task 7: 新增 alerts 应用骨架（后端）

**Files:**
- Create: `backend/src/apps/alerts/__init__.py`
- Create: `backend/src/apps/alerts/apps.py`
- Create: `backend/src/apps/alerts/models.py`
- Create: `backend/src/apps/alerts/services.py`
- Create: `backend/src/apps/alerts/tasks.py`
- Create: `backend/src/apps/alerts/api/*`
- Modify: `backend/src/core/settings.py`（INSTALLED_APPS 添加 alerts）
- Modify: `backend/src/core/urls.py`（注册 alerts API）

**Step 1: 创建基础 app 结构**
- 使用 Django app 模板或手动创建上述文件；
- 在 `apps.py` 中注册 `AlertsConfig`。

**Step 2: 定义核心模型**
- 在 `models.py` 中定义：
  - `AlertChannel`
  - `AlertRule`
  - `AlertEvent`
- 添加合理字段和索引，符合 v2 设计文档。

**Step 3: 注册 app 与迁移**
- 在 settings 中加入 `apps.alerts`；
- Run: `cd backend/src && python manage.py makemigrations alerts && python manage.py migrate`.

**Step 4: skeleton 服务与任务**
- 在 `services.py` 中定义占位函数：
  - `evaluate_and_raise(check_result)`（暂时只记录日志或创建空事件）；
- 在 `tasks.py` 中定义 Celery 任务：
  - `send_alert_event(alert_event_id)`。

**Step 5: 创建基础 API**
- 新建简单 API 端点：
  - 列表/查看 AlertEvent；
  - 后续可扩展 rule/channel 管理接口。

**Step 6: 添加最小测试**
- 在 `backend/tests/apps/alerts` 下：
  - 为模型和基础服务写少量单元测试；
  - 确认 migrations + 基本 CRUD 正常。

---

### Task 8: 让 monitoring 使用 alerts 域（事件驱动告警）

**Files:**
- Modify: `backend/src/apps/monitoring/services/*.py`
- Modify: `backend/src/apps/monitoring/tasks.py`
- Modify: `backend/src/apps/monitoring/models.py`（如有嵌入告警字段）
- Modify: `backend/src/apps/alerts/services.py`

**Step 1: 识别现有告警逻辑**
- 搜索监控任务执行完成后哪里在发送告警或拼通知内容；
- 记录这些逻辑片段。

**Step 2: 抽象出 CheckCompleted 事件对象**
- 定义一个内部数据结构（可放在 monitoring.services 或单独 module）：
  - 包含任务 ID、探针 ID、资产 ID、结果状态、响应时间等。

**Step 3: 替换直接通知为调用 alerts**
- 在监控执行完成路径中：
  - 构造 CheckCompleted 事件；
  - 调用 `alerts.services.evaluate_and_raise(event)`；
  - 移除原有直接发送通知的代码。

**Step 4: 扩展 alerts.evaluate_and_raise 实现**
- 根据 event 内容：
  - 匹配简单规则（例如连续失败 N 次）；
  - 创建 AlertEvent 并调度 `send_alert_event` 任务。

**Step 5: 测试 end-to-end**
- 写一个集成测试：
  - 模拟一个监控任务连续失败；
  - 断言创建了 AlertEvent 且 send 任务被调度。

---

### Task 9: 重构 assets 为「可扩展资产中心」

**Files:**
- Modify: `backend/src/apps/assets/models/*`
- Modify: `backend/src/apps/assets/services/*`
- Modify: `backend/src/apps/assets/api/*`
- Modify: `backend/src/apps/assets/tasks.py`
- Modify: 相关 migrations

**Step 1: 划清内置模型与外部源模型**
- 确定本地资产模型（如域名资产）：
  - 留在主模型文件中；
- 将外部源特有模型迁移到新的 AssetSource 抽象下或标记为将来扩展。

**Step 2: 定义 AssetSource 和 AssetSyncTask 抽象**
- 在 models 中新增：
  - `AssetSource`：标识外部资产源；
  - `AssetSyncTask`：记录每次同步执行。

**Step 3: v2 保留最小实现**
- 不在 services/tasks 中实现具体的 Zabbix/IPMP 同步过程；
- 保留接口签名和 place-holder 实现（例如抛出 “未启用” 错误）。

**Step 4: 更新 API 与前端**
- API：仅暴露本地资产管理接口；
- 前端：资产中心页面只展示本地资产管理与「外部资产源不可用」占位说明（见 Task 11）。

**Step 5: 测试与迁移**
- 更新 tests 中相关用例；
- 运行迁移验证模型结构正确。

---

### Task 10: 重构 tools 为「可扩展工具库」，移除代码管理

**Files:**
- Modify: `backend/src/apps/tools/models/*`
- Modify: `backend/src/apps/tools/services/*`
- Modify: `backend/src/apps/tools/api/*`
- Modify: `backend/src/apps/tools/tasks.py`
- Modify: `frontend/src/pages/tools/*`

**Step 1: 识别代码管理相关功能**
- 搜索工具库中是否有「脚本仓库/在线编辑/版本控制」等功能；
- 标记对应 models/API/前端页面。

**Step 2: 调整工具模型**
- 定义 `Tool` 与 `ToolExecution`；
- 删除或废弃与脚本仓库直接相关的模型字段/表。

**Step 3: 精简服务层**
- 保留工具执行的核心流程（依据类型调用执行引擎）；
- 移除与代码管理耦合的逻辑。

**Step 4: 对齐前端页面**
- 修改工具列表页与详情页：
  - 只展示工具配置与执行记录；
  - 移除脚本编辑器 UI。

**Step 5: 增补测试**
- 更新/新增工具执行相关的单元与集成测试。

---

### Task 11: 精简前端 Dashboard / Monitoring / Settings，增加 Alerts 页面

**Files:**
- Modify: `frontend/src/pages/dashboard/*`
- Modify: `frontend/src/pages/monitoring/*`
- Modify: `frontend/src/pages/settings/*`
- Create: `frontend/src/pages/alerts/*`
- Modify: 路由与导航配置

**Step 1: 重新设计 Dashboard**
- 将 Dashboard 调整为：
  - 探针在线数量/状态；
  - 监控任务数量、简单成功率；
  - 未处理告警数量；
- 删除所有外部监控/Zabbix/Prometheus 图表。

**Step 2: 精简 Monitoring 页面**
- 确保 Monitoring 只展示 OneAll 自身拨测任务；
- 增强任务详情页的轻量统计展示。

**Step 3: 精简 Settings 页面**
- 保留：用户/角色、基础系统信息；
- 将告警通道/规则配置挪到新的 Alerts 页面（或从 Settings 内部跳转）。

**Step 4: 新增 Alerts 页面**
- 创建告警事件列表页面；
- 创建简单的告警规则与通道配置表单；
- 对接后端 alerts API。

**Step 5: 前端测试**
- 更新/添加对应页面的单元测试和 e2e 测试；
- 跑一遍导航与核心流程验证。

---

### Task 12: 端到端回归与收尾

**Files:**
- 更新必要的测试文件与文档

**Step 1: 后端完整测试**
- Run: `cd backend && pytest`；
- 如有更长时间的 e2e 测试管线，运行一遍。

**Step 2: 前端完整测试**
- Run: `cd frontend && pnpm test`；
- 使用本地 docker-compose 启动一套最小环境，手动验证关键路径：
  - 探针节点注册；
  - 一次性拨测；
  - 持续监控任务创建与执行；
  - 告警触发与查看。

**Step 3: 文档收尾**
- 根据最终实现结果更新 `README.md` 和 `docs/plans/2026-03-18-oneall-v2-domain-refactor-design.md` 中的细节（如字段名、API 路径的微调）。

