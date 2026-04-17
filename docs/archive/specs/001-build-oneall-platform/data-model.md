# Data Model: OneAll 智能运维平台

> 历史说明：本数据模型文档描述的是原始规划范围，部分实体可能已在后续版本中合并、删除或降级为历史概念。请以当前 Django 模型定义为准。

## 概览

平台由三大域组成：拨测监控域、资产管理域、知识与工具域。所有域共享统一身份与审计体系，并通过插件与外部系统联通。

## 核心实体

### 1. User
- **主键**: `id` (UUID)
- **字段**: `username`, `display_name`, `email`, `phone`, `roles[]`, `status`, `last_login_at`
- **关系**: 与 `AuditLog`、`MonitoringRequest`、`ToolDefinition`、`KnowledgeArticle` 存在创建/更新关联。
- **约束**: 用户名唯一；角色来自系统设置中的 RBAC 配置。

### 2. ProbeNode
- **主键**: `id` (UUID)
- **字段**: `name`, `location`, `network_type` (enum: 内网/外网), `supported_protocols[]`, `status` (enum: 在线/离线/维护), `last_heartbeat_at`
- **关系**: 被 `MonitoringJob` 和 `DetectionTask` 引用。
- **约束**: 心跳超时自动标记离线；每个节点必须归属一个区域。

### 3. DetectionTask
- **主键**: `id` (UUID)
- **字段**: `target`, `protocol` (HTTP/HTTPS/Telnet/WSS/Custom), `probe_id`, `request_payload`, `result_status` (成功/失败/超时), `response_time_ms`, `status_code`, `certificate_expiry`, `log_trace`, `executed_at`, `initiated_by`
- **关系**: `initiated_by` → User；`probe_id` → ProbeNode。
- **约束**: 存储最近一次结果；日志保留 30 天并归档至存储桶。

### 4. MonitoringRequest
- **主键**: `id` (UUID)
- **字段**: `domain`, `system_name`, `network_type`, `owners[]`, `alert_contacts[]`, `threshold_rules`, `probe_selection[]`, `notification_policy`, `itsm_ticket_id`, `status`, `submitted_at`, `approved_at`, `rejected_reason`
- **关系**: `owners` 引用 User；审批流关联 `AuditLog`；成功后派生 `MonitoringJob`。
- **状态流**: `Draft` → `Submitted` → (`Approved` 或 `Rejected` 或 `Returned`)；`Approved` 触发 `MonitoringJob`；`Returned` 可重新提交。

### 5. MonitoringJob
- **主键**: `id` (UUID)
- **字段**: `request_id`, `probes[]`, `schedule_cron`, `frequency_minutes`, `protocol`, `threshold_rules`, `status` (Active/Paused/Archived), `last_run_at`, `next_run_at`, `failure_count`, `alert_channel`
- **关系**: `request_id` → MonitoringRequest；生成 `DetectionTask` 历史；告警发送至外部通知中心。
- **约束**: `schedule_cron` 与 `frequency_minutes` 二选一；`failure_count` 达阈值触发升级流程。

### 6. MonitoringSource
- **主键**: `id` (UUID)
- **字段**: `type` (Zabbix/Prometheus/Custom), `config_payload`, `enabled`, `health_status`, `last_health_check_at`, `connector_version`
- **关系**: 与 `MonitoringJob`、`MonitoringRequest` 间接关联（用于数据展示）；健康结果写入 `AuditLog`。
- **约束**: `type + connector_version` 唯一；禁用时停止同步。

### 7. AssetRecord
- **主键**: `id` (UUID)
- **字段**: `source` (Domain/Zabbix/IPMP/WorkOrder), `external_id`, `name`, `system_name`, `network_type`, `owners[]`, `contacts[]`, `metadata`, `synced_at`, `sync_status`
- **关系**: `owners`、`contacts` → User；记录同步日志。
- **约束**: `source + external_id` 唯一；保持历史版本以便追溯。

### 8. ToolDefinition
- **主键**: `id` (UUID)
- **字段**: `name`, `category`, `tags[]`, `description`, `script_id`, `parameters_schema`, `run_policy`, `created_by`, `updated_by`
- **关系**: `script_id` → ScriptVersion；执行记录写入 `AuditLog` 与 `DetectionTask`（当复用拨测探针）。
- **约束**: 名称唯一；参数 schema 采用 JSON Schema。

### 9. ScriptVersion
- **主键**: `id` (UUID)
- **字段**: `repository_path`, `version`, `language`, `content`, `commit_message`, `created_by`, `created_at`
- **关系**: 多个 `ToolDefinition` 可指向相同脚本版本；与代码仓库同步。
- **约束**: `repository_path + version` 唯一；内容需通过安全扫描。

### 10. KnowledgeArticle
- **主键**: `id` (UUID)
- **字段**: `title`, `slug`, `category`, `tags[]`, `content`, `attachments[]`, `visibility_scope`, `last_editor_id`, `last_edited_at`
- **关系**: `last_editor_id` → User；（可选）同步至全文检索引擎。
- **约束**: `slug` 在类别内唯一；附件存储 OSS 并记录元信息。

### 11. AuditLog
- **主键**: `id` (UUID)
- **字段**: `actor_id`, `action`, `target_type`, `target_id`, `metadata`, `result`, `occurred_at`
- **关系**: `actor_id` → User；`target_type` 可引用任一实体。
- **约束**: 保留不可变；敏感操作记录掩码数据。

## 关系图谱（文字概述）
- User 与 MonitoringRequest/ToolDefinition/KnowledgeArticle 存在作者关系；与 AuditLog 形成操作痕迹。
- MonitoringRequest 经 ITSM 审批后生成 MonitoringJob；MonitoringJob 定期创建 DetectionTask。
- DetectionTask 与 ProbeNode、MonitoringJob 关联，并向 TimescaleDB 写入指标。
- AssetRecord 与 MonitoringJob 通过域名/系统进行逻辑绑定，用于展示或校验。
- ToolDefinition 引用 ScriptVersion，执行时可调用 ProbeNode 或内部脚本。
- MonitoringSource 决定监控模块的外部集成配置，与 MonitoringJob 展示数据结合。

## 关键业务规则
- 任何新增或变更监控任务需关联至少一个 ProbeNode；当所有关联节点离线时任务暂停并通知责任人。
- ITSM 回调失败自动重试三次，仍失败则写入补偿队列，由管理员在任务清单中手动重放。
- 资产同步记录增量与全量两种策略，冲突以外部最新时间戳优先，并保留历史版本。
- 工具执行结果若涉及拨测或检测数据，应回写至 DetectionTask 以便统一审计。
- 知识库内容发布需至少一名审核者确认，审核流程写入 AuditLog。

## 状态机摘要
- MonitoringRequest: Draft → Submitted → (Approved | Rejected | Returned)；Returned 可重提，Rejected 需新建申请。
- MonitoringJob: PendingActivation → Active → (Paused | Archived)；Paused 可恢复 Active；Archived 只读。
- DetectionTask: Scheduled → Running → (Succeeded | Failed | Timeout)；失败或超时写入告警队列。

## 数据保留与归档
- 拨测原始日志保留 90 天后归档至对象存储，指标保留 365 天。
- AuditLog 与审批记录保留 3 年，符合法规要求。
- 知识库历史版本保留最新 5 个版本以便回滚。
