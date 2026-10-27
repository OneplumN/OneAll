# JEECG Skills 到 OneAll 设计的映射

## 1. 使用原则

本次不是把 OneAll 改成 JeecgBoot，也不是直接调用 JeecgBoot 后端 API。

我们使用 skills 的方式是：

```text
借鉴成熟产品/低代码平台的信息架构和交互模式
→ 转译为 OneAll 自己的 React + Ant Design 前端设计
```

## 2. jeecg-onlform

用于资产模型和字段配置。

映射到 OneAll：

- 资产模型 = 元数据驱动表单
- 字段配置 = Online 表单字段配置
- 字段类型 = 控件类型
- 字段映射 = 外部数据源字段到 OneAll 字段
- 动态表格 = 按模型字段渲染资产列表

落地页面：

- 资产中心
- 字段配置 Drawer
- 同步数据 Modal

## 3. jimubi-dashboard

用于监控总览。

映射到 OneAll：

- 统计卡片
- 告警趋势
- 探针健康
- 策略健康
- 最近事件表格

落地页面：

- 监控总览 `/monitoring/overview`

## 4. jeecg-bpmn

用于工单申请和审批流。

映射到 OneAll：

- 工单状态流转
- 审批人
- 审批记录
- 执行记录
- 操作日志

落地页面：

- 工单列表
- 工单详情
- 审批弹窗
- 执行记录 Tab

## 5. frontend-design

用于最终视觉和前端代码生成。

要求：

- 使用 React + Ant Design
- 控制台风格，克制、清晰、可扫描
- 不做营销页
- 不做过度装饰
- 表格、抽屉、弹窗、状态标签统一

