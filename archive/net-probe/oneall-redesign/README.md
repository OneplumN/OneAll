# OneAll 平台重构设计工作区

> 这个目录用于沉淀 OneAll 下一版重构设计，不承载旧前端实现，不连接后端，不作为生产代码目录。

## 当前结论

OneAll 下一版建议按“轻量运维控制台”重构，而不是继续堆功能：

- 前端技术栈：React + Ant Design
- 后端技术栈：Go + Gin 可作为重构目标，但需要先完成 API 契约和领域边界设计
- 产品定位：资产、监控、探针、工单、通知、系统配置的一体化运维平台
- 资产中心定位：模型驱动的简单数据中心，不预置固定资产模型，由用户创建模型；系统只提供可选模板
- 运维工具定位：只保留高频实用工具，例如 IP 正则助手；不保留脚本仓库、工具库这类重功能
- 系统设置定位：平台参数、用户角色、凭据、数据源、通知、Webhook、审计

## 阅读顺序

重构时优先阅读这些权威文档：

1. `01-product-redesign.md`：先确认产品定位、一级模块和主业务闭环。
2. `03-domain-and-refactor-boundaries.md`：再确认领域边界、保留范围和删除范围。
3. `02-frontend-antd-design.md`：前端实现时参考 React + Ant Design 页面规范。
4. `06-technical-architecture.md`：确认后端、数据库、鉴权、事件、Redis 和探针通信决策。
5. `07-archive-boundaries.md`：确认旧 Vue 前端和误做原型的归档边界。
6. `05-tasklist.md`：执行阶段只维护这一份任务清单。

`00-legacy-full-platform-redesign.md` 是早期完整草案，只作为细节参考，不再作为当前重构基线。

## 目录说明

| 文件 | 用途 |
| --- | --- |
| `00-legacy-full-platform-redesign.md` | 早期完整重构详稿，含过期技术栈和旧模块划分，只作参考 |
| `01-product-redesign.md` | 平台级产品重构设计 |
| `02-frontend-antd-design.md` | React + Ant Design 前端设计说明 |
| `03-domain-and-refactor-boundaries.md` | 领域边界、保留/删除范围、重构原则 |
| `04-skills-mapping.md` | JEECG skills 如何转化为 OneAll 设计 |
| `05-tasklist.md` | 后续可执行任务清单，唯一任务维护入口 |
| `06-technical-architecture.md` | 后端、数据库、鉴权、事件、Redis、TimescaleDB、探针通信决策 |
| `07-archive-boundaries.md` | 旧 Vue 前端和误做 Vue 原型的归档边界 |

## 当前可预览原型

Ant Design 独立原型：

```text
http://127.0.0.1:5182/
```

对应代码目录：

```text
oneall-antd-prototype
```

## 注意

旧目录说明：

- `frontend/`：现有 Vue + Element Plus 老前端，暂不作为新设计基准。
- `oneall-frontend-prototype/`：早期误做的 Vue + Element Plus 独立原型，不再作为主线。
- `oneall-antd-prototype/`：当前新前端原型代码目录。
