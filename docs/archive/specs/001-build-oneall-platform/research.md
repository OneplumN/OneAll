# Research Notes: OneAll 智能运维平台 MVP

> 历史说明：本研究记录服务于原始方案决策，包含部分已放弃的模块和集成方向。保留它是为了追踪背景，不代表这些结论仍是当前实现目标。

## 决策 1：Web 前端技术栈
- **Decision**: 使用 Vue 3（Composition API）+ TypeScript + Vite + Element Plus 构建单页前端，并集成 Pinia 状态管理与 Vue Router。
- **Rationale**: 原始需求草案指定框架；Vue 3 + Vite 具备插件体系、较小首屏体积与组件化优势，Element Plus 提供企业级组件满足监控、表格、仪表等 UI 需求。
- **Alternatives considered**: React + Ant Design（与文档要求不符）；Angular（学习成本高且缺乏与 Element 体系兼容性）。

## 决策 2：后端框架与接口层
- **Decision**: 采用 Python 3.11 + Django 4.2 + Django REST Framework 构建 API；通过 Celery 5.x 处理拨测调度与后台任务，Redis 作为消息中间件。
- **Rationale**: Django 提供成熟的 ORM、认证与管理后台；Celery 与 Django 配合度高，满足拨测任务、同步作业的异步执行需求。原始需求草案已指定 Python + Django。
- **Alternatives considered**: FastAPI（异步性能好但与现有 Django 生态不符）；Flask（需自建大量基础能力）。

## 决策 3：数据存储与检索方案
- **Decision**: 采用 MySQL 8.0 作为事务、配置与资产数据存储；TimescaleDB 2.x 专职拨测时序与历史任务指标；Redis 7 作为缓存与任务队列。
- **Rationale**: 用户要求将 PostgreSQL 换成 MySQL，同时仍保留 Timescale 对时序数据的优势；通过双数据库分工兼顾事务一致性与时序性能；Redis 为异步与缓存基础设施。
- **Alternatives considered**: 单一 MySQL 储存全部数据（时序查询性能与压缩能力不足）；PostgreSQL + TimescaleDB（不符合最新数据库约束）。

## 决策 4：监控与可观测性
- **Decision**: 后台记录结构化日志（stdout），并通过 Prometheus 抓取后端/探针指标；链路追踪能力暂不启用。
- **Rationale**: 现阶段优先交付核心业务闭环与轻量运维成本；指标 + 结构化日志足以支撑日常排障与容量评估。
- **Alternatives considered**: 全量链路追踪（需要额外采集与存储组件，部署复杂度提升）；仅依赖非结构化日志（排查效率低）。

## 决策 5：探针通信与扩展机制
- **Decision**: 探针默认通过加密 HTTP 与后端交互，后续对高实时场景支持 gRPC；插件通过声明式配置注册执行脚本，运行结果回传 JSON。
- **Rationale**: 原始需求草案提到 HTTP 或 gRPC；采用 HTTP 起步兼顾通用性，预留 gRPC 保障扩展；JSON 便于日志与告警对接。
- **Alternatives considered**: 直接使用纯 gRPC（对前端、第三方集成门槛高）；MQTT（需额外 Broker，超出当前需求）。

## 决策 6：持续拨测审批与 ITSM 集成
- **Decision**: 通过 REST API 与现有 ITSM 系统交互，采用幂等回调处理审批状态；失败时进入补偿队列，运营人员可在任务清单页手动重试。
- **Rationale**: 原始需求草案要求自动工单创建与审批回调；REST 接口兼容度高，幂等设计避免重复任务。
- **Alternatives considered**: MQ 事件驱动（ITSM 未提供消息通道）；人工审批（违背自动化目标）。

## 决策 7：部署与维护策略
- **Decision**: 采用 Docker Compose/Ansible 在虚拟机或裸机环境分层部署（后端、前端、探针、MySQL、Redis）；暂不启用 Kubernetes；维护窗口安排在周末并执行数据库备份快照。
- **Rationale**: 用户明确暂不考虑 K8s；Docker Compose + Ansible 支持快速部署与环境隔离，同时保持 Git 版本与备份记录满足宪章要求。
- **Alternatives considered**: Kubernetes（具备弹性但超出当前运维诉求）；纯手工部署（可重复性差且易出错）。
