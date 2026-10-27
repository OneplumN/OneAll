# 领域边界与重构范围

## 1. 核心领域

| 领域 | 职责 |
| --- | --- |
| Assets | 资产模型、资产记录、字段配置、同步历史 |
| Detection | 一次性检测、检测结果、转监控策略 |
| Monitoring | 监控策略、调度、探针执行、执行日志 |
| Alerts | 告警规则、告警事件、告警状态流转 |
| Probes | 探针注册、心跳、配置版本、任务领取 |
| Workorders | 工单申请、审批、执行、操作日志 |
| Settings | 用户、角色、权限、凭据、数据源、通知、Webhook、审计 |
| Notifications | 站内信、外部通知、模板、投递记录 |

## 2. 保留

应保留并重构：

- 资产模型与字段配置
- 蓝鲸 CMDB 同步
- Zabbix 数据源
- 探针节点
- 拨测链路
- 告警事件
- 工单闭环
- 通知中心
- 数据源管理
- 凭据管理
- 审计日志
- IP 正则助手

## 3. 删除或不进入新版本

不建议进入重构版本：

- 脚本仓库
- 工具库
- 账号同步独立模块
- Grafana 同步独立模块
- 复杂资产拓扑
- 低频插件化工具市场
- 和核心闭环无关的历史占位页面

## 4. 资产同步链路

资产中心采用模型驱动，不把“全部资产、域名资产、主机资产、应用资产”等写成固定导航。首版默认提供四个业务模型，且按自定义模型一样维护：CMDB 域名、Zabbix 主机、IPMP 项目、工单纳管主机信息。

模型创建方式：

- 默认业务模型：作为平台默认模型出现在不分组模型树中，字段列按模型定义动态展示，可按自定义模型维护，默认选中域名模型
- 空白模型：用户自定义模型名称、字段、权限和同步方式
- 模板创建：首版不提供模板创建，也不导入模型定义 JSON；新建模型采用一步表单完成
- 外部同步创建：数据源同步前必须先选择已有模型或创建模型，再在同步任务中配置外部字段到平台字段的映射

资产模型是资产记录、字段配置、同步配置、权限控制和审计的归属边界。删除模型前必须校验实例数据、同步任务、工单、告警和策略引用；字段被实例数据使用后不能直接删除，只能先禁用以保留历史数据。

OneAll 资产中心参考蓝鲸 CMDB 的模型管理思想，但首版只保留 2 个核心域：

- 模型管理：模型定义、字段、唯一键、主显示字段、权限和审计；不保留模型分类
- 模型资产：某个模型下的实例数据列表、实例 Drawer、实例级新增/查看/编辑/删除和变更记录

独立模型关系和业务拓扑不进入首版。实例之间的弱关联可以先在实例详情中展示，等资产规模和告警归因需求明确后再升级为独立能力。

目标链路：

```text
数据源配置
→ 凭据引用
→ 同步任务字段映射
→ 同步预览
→ 执行同步
→ 写入资产记录
→ 记录同步历史
→ 通知同步结果
```

蓝鲸 CMDB 同步不应该写死在页面，也不应该由用户直接改脚本。

应抽象为：

- 数据源类型：`blueking_cmdb`
- 凭据类型：`token` 或 `app_secret`
- 字段映射：在同步任务中配置外部字段 → 当前模型的平台字段；字段配置只定义平台字段结构，不绑定具体外部数据源字段。禁用字段不参与映射，必填字段、唯一键和主显示字段必须完成映射后才能预览和执行。
- 同步策略：手动触发 / 定时触发
- 同步结果：新增、更新、删除、失败明细

## 5. 探针链路

目标链路：

```text
探针注册
→ 平台下发配置版本
→ 探针心跳
→ 探针领取任务
→ 探针执行检测
→ 回传结果
→ 生成日志
→ 告警规则判断
```

异常处理：

- 心跳超过阈值判定离线
- 已领取任务超时后重新分配
- 过期配置版本需要提示升级
- 长期不可用探针可退役

## 6. 系统设置链路

系统设置不是一个“杂物间”，而是平台基础能力：

- 平台参数
- 用户与角色
- 权限矩阵
- 凭据管理
- 数据源管理
- 通知通道
- 通知模板
- 出站 Webhook
- 审计日志
- 数据保留策略

## 7. 用户角色与权限矩阵

首版角色先保持少而清晰，避免做成复杂 IAM。

| 角色 | 定位 |
| --- | --- |
| PlatformAdmin | 平台管理员，负责系统设置、用户权限、数据源和凭据 |
| OpsAdmin | 运维管理员，负责资产、监控、告警、探针和工单闭环 |
| OpsEngineer | 运维工程师，处理日常检测、告警、工单和资产维护 |
| Approver | 审批人，只处理待审批工单和相关详情 |
| Viewer | 只读用户，可查看授权范围内的数据 |

| 模块 / 能力 | PlatformAdmin | OpsAdmin | OpsEngineer | Approver | Viewer |
| --- | --- | --- | --- | --- | --- |
| 监控总览 | 读 | 读 | 读 | 读 | 读 |
| 告警事件 | 读 / 处理 / 关闭 | 读 / 处理 / 关闭 | 读 / 处理 | 读 | 读 |
| 监控策略 | 读 / 写 | 读 / 写 / 启停 | 读 / 写 | 读 | 读 |
| 探针节点 | 读 / 管理 | 读 / 管理 | 读 | 无 | 读 |
| 资产中心 | 读 / 写 | 读 / 写 / 同步 | 读 / 写 | 读 | 读 |
| 一次性检验 | 执行 | 执行 | 执行 | 读 | 读 |
| 工单申请 | 读 / 管理 | 读 / 管理 | 提交 / 处理 | 审批 | 读 |
| 用户与角色 | 读 / 写 | 无 | 无 | 无 | 无 |
| 凭据管理 | 读 / 写 / 授权 | 读 / 引用 | 引用 | 无 | 无 |
| 数据源管理 | 读 / 写 | 读 / 写 | 读 | 无 | 无 |
| 通知与 Webhook | 读 / 写 | 读 / 写 | 读 | 无 | 无 |
| 审计日志 | 读 | 读 | 无 | 无 | 无 |

权限动作统一抽象为：`read`、`create`、`update`、`delete`、`execute`、`approve`、`close`、`manage`。页面按钮必须由权限动作驱动，不在前端写死角色名。

## 8. 资产字段模型定义

资产中心的基础对象分为资产模型、字段定义、资产记录、字段映射和同步历史。

| 对象 | 关键字段 |
| --- | --- |
| AssetModel | `id`、`code`、`name`、`description`、`template_key`、`is_template_based`、`status` |
| AssetField | `id`、`model_id`、`code`、`name`、`type`、`required`、`unique`、`searchable`、`visible`、`order` |
| AssetRecord | `id`、`model_id`、`external_id`、`display_name`、`fields`、`source_id`、`sync_batch_id`、`status` |
| FieldMapping | `id`、`model_id`、`source_id`、`external_field`、`asset_field`、`transform_rule` |
| SyncHistory | `id`、`model_id`、`source_id`、`status`、`created_count`、`updated_count`、`deleted_count`、`failed_count` |

字段类型首版支持：

- `string`
- `number`
- `boolean`
- `datetime`
- `enum`
- `ip`
- `domain`
- `url`
- `json`

系统只约定最小通用字段，不强制每个模型继承固定资产类型字段：

| 字段 | 说明 |
| --- | --- |
| `name` | 资产名称或展示名 |
| `owner` | 负责人 |
| `department` | 所属团队 |
| `environment` | 环境，例如 prod、staging、test |
| `status` | active、inactive、archived |
| `source` | 数据来源 |
| `external_id` | 外部系统唯一标识 |
| `last_sync_at` | 最近同步时间 |

同步链路只能写入 `AssetRecord.fields` 中已登记的字段；外部系统新增字段必须先进入当前模型的字段配置，再在同步任务中补充字段映射。

## 9. 告警规则 DSL

告警规则 DSL 用于描述“对什么对象、用什么指标、在什么窗口、满足什么条件、如何升级”。

首版规则结构：

```json
{
  "scope": {
    "asset_model": "domain",
    "asset_filter": {
      "environment": "prod"
    }
  },
  "signal": {
    "metric": "http_status",
    "source": "probe_result"
  },
  "condition": {
    "operator": "not_in",
    "value": [200, 301, 302],
    "duration": "3m",
    "consecutive": 3
  },
  "severity": "critical",
  "recovery": {
    "operator": "in",
    "value": [200, 301, 302],
    "consecutive": 2
  },
  "actions": {
    "notify_channels": ["site", "webhook"],
    "create_workorder": false
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `scope` | 规则适用资产范围 |
| `signal` | 参与判断的指标或事件 |
| `condition` | 触发条件 |
| `severity` | `info`、`warning`、`critical` |
| `recovery` | 恢复条件 |
| `actions` | 通知、工单、Webhook 等动作 |

首版操作符支持：`eq`、`ne`、`gt`、`gte`、`lt`、`lte`、`in`、`not_in`、`contains`、`regex`。所有规则保存前必须做语法校验和试算预览。

## 10. 工单状态机

工单状态必须驱动页面 Tab、按钮和权限判断。

```text
draft
→ submitted
→ approved
→ executing
→ completed

submitted
→ rejected

approved
→ canceled

executing
→ failed
→ completed

draft / submitted
→ withdrawn
```

| 状态 | 页面归属 | 可见操作 |
| --- | --- | --- |
| `draft` | 我的申请 | 编辑、提交、删除 |
| `submitted` | 我的申请、待我审批 | 审批、驳回、撤回 |
| `rejected` | 我的申请 | 重新编辑、归档 |
| `approved` | 待我执行 | 执行、取消 |
| `executing` | 待我执行 | 更新进度、标记失败、完成 |
| `completed` | 工单详情 | 查看、关联告警关闭记录 |
| `failed` | 工单详情 | 重试、转人工处理 |
| `canceled` | 工单详情 | 查看 |
| `withdrawn` | 我的申请 | 查看、重新提交 |

工单类型首版包括：拨测监控申请、资产纳管申请、资产变更申请。每个状态流转都必须写操作日志，并触发通知事件。
