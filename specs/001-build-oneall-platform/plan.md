# Implementation Plan: OneAll 智能运维平台 MVP

**Branch**: `001-build-oneall-platform` | **Date**: 2025-11-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-build-oneall-platform/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

OneAll 平台需要提供自研探针体系、插件化监控集成、拨测申请审批与资产聚合等核心能力，确保一次性拨测、持续拨测、统计分析、工具知识库与系统设置形成闭环。实现遵循 dream.md 的功能要求，并结合最新约束：前端采用 Vue 3 + Element Plus，后端使用 Python Django + Celery 调度；数据层由 MySQL 8（事务数据）与 TimescaleDB 2.x（拨测时序数据）协同，辅以 Redis；部署阶段使用容器或虚拟机编排，不引入 Kubernetes。

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Frontend TypeScript + Vue 3 (Composition API); Backend Python 3.11 + Django 4.2 + Celery 5.x; Probe-side守护程序使用 Python 3.11  
**Primary Dependencies**: Element Plus UI、Vite 构建、Django REST Framework、Celery + Redis、Prometheus Exporter  
**Storage**: MySQL 8.0（事务配置、任务与资产数据）、TimescaleDB 2.x（拨测指标、任务历史）、Redis 7（缓存与任务队列）  
**Testing**: 前端 Vitest + Playwright；后端 pytest + Django TestCase；探针使用 pytest + integration scripts  
**Target Platform**: 前端 Web SPA（Chrome/Edge 最新版本）；后端 Linux (Ubuntu 22.04) 容器化或虚拟机部署；探针跨多地域 Linux 节点  
**Project Type**: Web 应用（独立前后端 + 探针组件）  
**Performance Goals**: 80% 拨测 3 分钟内完成，统计报表 2 分钟内生成，ITSM 回调处理延迟 <30 秒，监控概览实时刷新 <60 秒；首页告警摘要与待办数据延迟不超过 2 分钟。
**Constraints**: 必须满足 dream.md 功能要求；事务存储采用 MySQL，时序数据使用 TimescaleDB；所有接口通过 HTTPS；探针通讯支持 HTTP/gRPC；维护窗口限定周末；部署暂不使用 Kubernetes，采用容器/虚拟机与自动化脚本；关键模块需输出结构化日志并在操作日志门户中可检索导出。
**Scale/Scope**: 初始支持 500+ 域名资产、100+ 探针节点、日均 10k 拨测任务、知识库 5k 文档

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
- [x] 原则一：独立价值交付 —— Spec 用户故事按角色拆分并可独立交付；Plan 将确保 tasks.md 逐故事分组。
- [x] 原则二：计划先行与透明假设 —— 技术上下文已填充，风险集中在多数据库协同（记录于研究任务）。
- [x] 原则三：验证驱动交付 —— 测试工具已选定（Vitest、Playwright、pytest），后续任务将标注验证责任。
- [x] 原则四：可观测与知识沉淀 —— 引入 Prometheus 指标以及 quickstart/代理指南更新计划。
- [x] 原则五：简洁结构与版本纪律 —— 采用前后端分体结构，版本控制与数据库备份计划纳入部署说明。

> 设计工件（data-model、contracts、quickstart）完成后重新核对：所有原则仍满足，无需额外豁免。最新任务计划在 Phase 3 增设“平台概览与系统设置”支撑阶段，请以 `tasks.md` 的阶段顺序为准。

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
backend/
├── src/
│   ├── core/              # Django settings, middleware, auth
│   ├── apps/
│   │   ├── monitoring/    # 拨测任务、探针、插件管理
│   │   ├── assets/        # 资产中心同步与查询
│   │   ├── analytics/     # 统计分析与报表导出
│   │   ├── tools/         # 工具库与代码管理接口
│   │   └── knowledge/     # 知识库 API
│   ├── workers/           # Celery 任务与调度
│   └── integrations/      # ITSM、监控源、CMDB 集成适配
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── stores/
│   ├── services/          # API 客户端、WebSocket/gRPC 网关
│   └── telemetry/         # 预留：可观测性相关实现（当前未启用链路追踪）
└── tests/
    ├── unit/
    └── e2e/

probes/
└── src/
    ├── agent/             # 探针执行器
    ├── plugins/           # 拨测协议扩展
    └── telemetry/         # 指标与日志上报

docs/
├── quickstart/
└── operations/
```

**Structure Decision**: 采用前后端分离 + 探针代理三组件模型，对应 backend、frontend、probes 三套源码目录与独立测试套件；部署文档统一放入 `docs/`。复杂度控制在三组件内，满足宪章对最小可行边界的要求。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

## Implementation Strategy

**首页概览补充说明**：概览数据由 `overview_service` 聚合探针健康、最近告警指标以及待办事项（ITSM 待处理记录与探针异常事件），通过缓存层控制 60 秒刷新节奏；端到端测试需覆盖告警摘要与待办列表的展示与交互。

**成功标准验证安排**：Phase N 将通过性能监控脚本、审批 SLA 报表、资产覆盖率仪表盘、满意度调查以及工具复用率统计等任务，对应 SC-001~SC-007 并在运维文档中沉淀数据存档路径。

### MVP First（User Story 1 Only）

1. 完成 Phase 1–2，搭建共享基础设施、认证、日志与探针框架。
2. 落实 Phase 3 的平台概览与系统设置支撑功能，为后续故事提供首页数据与全局配置能力。
3. 聚焦 User Story 1（Phase 4），按“测试→后端→探针→前端→文档”顺序完成 `tasks.md` 中标记为 US1 的所有任务。
4. 验证一次性拨测场景，准备向值班团队演示。

### Incremental Delivery

1. 在 MVP 基础上交付 User Story 2（Phase 5），形成持续拨测与 ITSM 闭环。
2. 扩展至 User Story 3（Phase 6），提供资产聚合与统计报表能力。
3. 最后完成 User Story 4（Phase 7），建设工具库、代码管理与知识库生态。
4. 每个阶段结束时执行对应 runbook 和验收步骤，确保阶段性可上线。

### Parallel Team Strategy

1. 基础阶段完成后，按领域分组推进：
   - 小组 A：拨测核心与探针（Phase 4 / US1）。
   - 小组 B：持续拨测、ITSM 与集成中心（Phase 5 / US2）。
   - 小组 C：资产与统计（Phase 6 / US3）。
   - 小组 D：工具、代码管理与知识库（Phase 7 / US4）。
2. 利用 `tasks.md` 中标记 `[P]` 的任务进行并行开发；测试与实现可交错执行。
3. 各小组在阶段结束时提交独立验收报告，再推进下一阶段。
