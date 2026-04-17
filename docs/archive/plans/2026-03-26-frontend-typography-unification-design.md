# Frontend Typography Unification Design

**Date:** 2026-03-26

## Context

当前前端已经存在一套全局主题变量，但字体体系没有真正落到页面层。

已确认的问题：

- 全局字体来源重复且不一致：
  - `frontend/src/styles/theme.scss` 定义了 `--oa-font-base`、`--oa-font-heading`、`--oa-font-table-header` 与 `--oa-font-family`
  - `frontend/src/App.vue` 再次定义了 `:root` 字体族
  - `frontend/src/assets/main.css` 再次定义了 `body` 字体族和字号
- 页面级组件大量硬编码 `font-size`
  - 统计结果显示 `12px`、`13px`、`14px` 是最高频写法，且分布在资产、告警、探针、设置等核心页面
- 字体 token 几乎没有在业务页面中复用
  - `var(--oa-font-base|heading|table-header)` 实际只在主题文件自身被使用

这意味着当前系统是“有 token，但没有形成设计系统约束”，页面观感会随着单页修改逐步漂移。

---

## Design Goal

建立一套统一、克制、可复用的后台字体层级，覆盖：

- 页面标题
- 分区标题
- 表格正文
- 表格辅助文本
- 表单标签
- 表单值
- 描述类详情页

目标不是追求“每个地方同一个字号”，而是统一成一套固定层级，所有页面都只能在层级内取值。

---

## Typography Principles

### 1. 基础规则

- 默认正文字号固定为 `14px`
- 元信息、辅助说明、标签提示固定收敛到 `12px`
- 次级说明、筛选提示、表格副文本统一使用 `13px`
- 详情页正文、重点值、表单内容允许使用 `14px` 或 `16px`
- 分区标题使用 `16px`
- 页面标题使用 `18px` 或 `20px`

### 2. 使用约束

- 业务页面禁止继续直接写裸 `12px/13px/14px/16px/18px/20px`
- 新页面优先使用 token 或语义 class，不再在单页组件里重复定义
- 特殊字体只允许存在于代码编辑器、日志块、脚本预览这类 monospace 场景

### 3. 风格方向

- 企业后台风格
- 信息层级清晰，但不过度放大标题
- 标签和辅助文字应醒目可读，但不使用过重字重

---

## Proposed Type Scale

建议新增并统一使用以下 token：

- `--oa-font-size-xs: 12px`
- `--oa-font-size-sm: 13px`
- `--oa-font-size-md: 14px`
- `--oa-font-size-lg: 16px`
- `--oa-font-size-xl: 18px`
- `--oa-font-size-2xl: 20px`

同时保留语义别名，减少业务层直接依赖尺寸名：

- `--oa-font-base: var(--oa-font-size-md)`
- `--oa-font-heading: var(--oa-font-size-xl)`
- `--oa-font-table-header: var(--oa-font-size-sm)`
- `--oa-font-meta: var(--oa-font-size-xs)`
- `--oa-font-section-title: var(--oa-font-size-lg)`
- `--oa-font-detail-value: var(--oa-font-size-lg)`

---

## Page Mapping Rules

### Global Shell

- 顶部主标题：`18px`
- 子标题 / breadcrumb 辅助文本：`13px`
- 全局默认正文：`14px`

### Table Pages

- 表头：`13px`
- 表格正文：`14px`
- 单元格辅助信息：`12px`
- 操作列：`13px` 或与表格正文保持 `14px`，二选一后全站统一

### Form Pages

- 表单标签：`13px`
- 表单输入值：`14px`
- 帮助文案：`12px`
- 分组标题：`16px`

### Detail Pages

- 页面标题：`18px`
- 分组标题：`16px`
- 字段标签：`14px`
- 字段值：`14px`
- 重点字段值：`16px`
- 说明性长文本：`14px`

---

## Source of Truth

统一后的单一来源如下：

- 主题 token：`frontend/src/styles/theme.scss`
- 全局基础样式：`frontend/src/assets/main.css`

需要清理或收敛的重复来源：

- `frontend/src/App.vue` 中的 `:root` 字体定义
- 各页面 scoped style 中重复出现的裸字号

原则上，`App.vue` 不再承担字体体系定义职责，只保留根节点结构与少量全局行为。

---

## Rollout Strategy

按影响面和当前需求顺序推进：

1. 先收口基础 token 与全局入口
2. 再收口资产中心相关页面
3. 再收口告警域页面
4. 最后收口探针域页面

这样可以先解决当前用户最常查看的资产与告警页面，再处理探针页面中更多历史样式。

---

## Risk Assessment

### Low Risk

- 主题 token 扩充
- 清理重复 font-family 定义
- 辅助文字与标签字号统一

### Medium Risk

- 表格行高、标签列宽、详情页段落密度会随字号收口发生轻微变化
- 某些页面使用 Element Plus 默认行高，字号统一后可能需要微调 padding

### Not Included in This Round

- 字重系统统一
- 行高系统统一
- 间距系统统一
- 中文与英文字体栈重做

本轮只处理字体族和字号层级，不扩展到整个设计系统。

---

## Acceptance Criteria

- 全局字体入口只保留一套来源，不再出现 `App.vue`、`main.css`、`theme.scss` 三处并行定义
- 资产、告警、探针、设置四个主域的核心页面不再新增裸字号
- 详情页、列表页、表单页都能映射到固定字号层级
- 任意两个同类页面的标题、表格正文、辅助文本字号保持一致
