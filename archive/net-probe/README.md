# OneAll 重构历史归档

## 状态

本次重构已于 2026-10-27 停止开发，不再继续实现原计划。保留现有成果供历史查阅与按需提取，不作为生产交付或完整功能承诺。

停止原因：平台功能范围过大，逐步叠加资产、监控、告警、探针、工单和工具，未形成清晰的核心价值与产品边界。

## 保存内容

| 目录或文件 | 内容 |
| --- | --- |
| `oneall-antd-prototype/` | React + Ant Design 前端、契约、测试、验收脚本和设计截图 |
| `oneall-api/` | Node.js 参考 API、数据库迁移和测试 |
| `oneall-go-api/` | Go API、真实探针 Agent 和测试脚本 |
| `oneall-redesign/` | 重构设计、架构、范围约定和历史任务清单 |
| `early-design/core-design.md` | 从 OneplumN/One_All_In_Ai 保存的早期核心设计草案，含来源与文件 SHA |
| `regex-lab-site/` | 本地 IP 正则工具的现存源码和部署参考 |
| `ip-regex-static-20261016.zip` | 已有 IP 正则静态页面打包文件 |

本地来源：`/Volumes/oneplums/workspace/OneA/net-probe`。

未上传 `node_modules`、构建/验收输出、嵌套 Git 元数据、托管平台配置、环境凭据和 `oneall-api/data/oneall-state.json` 运行状态数据。本地原文件保留。

## 阅读说明

- 本分支从旧平台 `main` 提交 `ebc5a970df73128b7624428c1ef63c4a22b4e855` 创建；原平台代码保留，本次归档没有合并到 `main`。
- 原设计文档、任务清单及验收说明保留历史内容；其“当前主线”“下一步”等表述不再表示后续开发计划，以本页停止维护状态为准。
- Vue / Django 旧平台、React / Go 重构和早期设计草案属于不同阶段，不是同一套可直接混用的运行系统。
- 本次仅进行文件归档核对，未重新运行应用功能测试，不宣称所有模块已完成或可用于生产。
- 归档时基线仓库没有 `.github/workflows` 工作流文件；本次未新增自动构建或部署流程。
