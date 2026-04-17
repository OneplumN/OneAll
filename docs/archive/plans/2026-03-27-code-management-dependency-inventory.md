# 代码管理依赖清单

日期：2026-03-27

## 结论

当前“代码管理”不能按无关联页面直接删除。

知识库链路已经基本移除，只剩历史文档和旧测试/旧命名；代码管理则仍然承担脚本仓库、脚本选择、脚本执行三类底座能力，已经被资产同步、告警渠道、插件配置和主布局导航直接依赖。

因此，后续应区分两件事：

1. 可以继续清理“知识库”残留。
2. 代码管理如果要下线，应先完成“页面/导航弱化”和“能力层保留或迁移”，不能直接删除接口与脚本执行链路。

## 知识库残留

以下内容属于知识库尾巴，可继续清理：

- 前端已删除页面：
  - `frontend/src/pages/knowledge/KnowledgeCenter.vue`
  - `frontend/src/pages/knowledge/KnowledgeArticleView.vue`
- 前端已删除服务：
  - `frontend/src/services/knowledgeApi.ts`
- 后端已删除应用：
  - `backend/src/apps/knowledge/*`
- 旧测试：
  - `frontend/tests/e2e/tools-knowledge.spec.ts`
- 旧命名：
  - `backend/src/apps/core/management/commands/seed_demo_data.py`
    - `_ensure_tools_and_knowledge` 这类命名需要去知识库化

## 代码管理当前依赖

### 1. 路由与导航

- 路由仍存在：
  - `frontend/src/router/index.ts`
    - `/code/repository/:directoryKey?`
- 主布局动态注入目录导航：
  - `frontend/src/layouts/MainLayout.vue`
- 国际化标题仍保留：
  - `frontend/src/i18n/index.ts`

### 2. 页面与接口

- 页面：
  - `frontend/src/pages/tools/CodeRepository.vue`
- 前端接口：
  - `frontend/src/services/codeRepositoryApi.ts`
- 后端接口：
  - `backend/src/apps/tools/api/urls.py`
    - `tools/repositories`
    - `tools/repositories/<uuid:repository_id>`
    - `tools/repositories/<uuid:repository_id>/versions`
    - `tools/repositories/<uuid:repository_id>/execute`
    - `code/directories`

### 3. 资产中心依赖

- 资产同步执行器：
  - `frontend/src/services/scriptExecutor.ts`
- 资产中心直接调用脚本执行：
  - `frontend/src/pages/assets/AssetCenter.vue`

影响：
- 如果删除代码管理接口，资产模型的同步脚本执行会中断。

### 4. 告警与插件配置依赖

- 告警渠道脚本仓库绑定：
  - `frontend/src/pages/settings/AlertChannelDetail.vue`
- 脚本选择弹窗：
  - `frontend/src/components/ScriptSelectorDialog.vue`
- 插件配置表单：
  - `frontend/src/pages/monitoring/components/PluginConfigForm.vue`

影响：
- 如果删除脚本仓库能力，通知脚本和插件脚本选择链路会失效。

### 5. 工具能力依赖

- 目录 store：
  - `frontend/src/stores/codeDirectories.ts`
- 工具脚本执行：
  - `backend/src/apps/tools/services/repository_execution_service.py`
- IP 正则功能依赖脚本仓库：
  - `backend/src/apps/tools/services/ip_regex_runner.py`

影响：
- 工具模块中的脚本型能力会失效。

## 建议拆分方式

如果产品上不再保留“代码管理”独立模块，建议按两阶段处理：

### 阶段 A：先下线页面，不删能力

- 从导航中移除代码管理入口。
- 保留：
  - 脚本仓库 API
  - 脚本执行 API
  - 目录 API
  - 脚本选择弹窗
  - 资产/告警/工具对脚本仓库的调用

### 阶段 B：再迁移能力归属

- 资产同步脚本迁移到“资产模型管理”域。
- 通知脚本迁移到“告警渠道”域。
- 工具脚本迁移到“运维工具”域。
- 仅当以上链路全部完成去耦后，再删除：
  - `CodeRepository.vue`
  - `codeRepositoryApi.ts`
  - 对应后端仓库接口

## 当前建议

当前阶段建议：

1. 继续清理知识库所有残留。
2. 不要直接删除代码管理页面与接口。
3. 如果要瘦身代码管理，优先做“隐藏导航 + 保留脚本底座”。
