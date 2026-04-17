<div align="center">

# OneAll

### 智能运维平台

探针为眼，数据为脉，让运维系统回到清晰、可维护、可观测的状态。

[![Vue 3](https://img.shields.io/badge/Vue-3.x-42b883?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Django](https://img.shields.io/badge/Django-4.2-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Go](https://img.shields.io/badge/Go-1.21+-00add8?style=for-the-badge&logo=go&logoColor=white)](https://go.dev/)

</div>

---

## 目录

- [项目说明](#项目说明)
- [当前功能范围](#当前功能范围)
- [系统架构](#系统架构)
- [代码结构](#代码结构)
- [快速开始](#快速开始)
- [本地开发](#本地开发)
- [配置说明](#配置说明)
- [探针部署](#探针部署)
- [生产部署](#生产部署)
- [常见问题](#常见问题)
- [相关文档](#相关文档)

---

## 项目说明

**OneAll** 是一个面向运维场景的统一平台，围绕三条主线构建：

- **检测**：一次性拨测、证书检测、CMDB 域名检测
- **调度**：监控申请、定时执行、日志与结果回传
- **治理**：资产同步、运维工具、告警事件、系统设置

当前仓库已经完成一轮前端结构收口，现行前端以 `src/app + src/features + src/shared` 为主结构；旧 `pages / stores / components` 已不再作为运行时主链。

---

## 当前功能范围

### 1. 一次性检测

- 域名拨测
- 证书检测
- CMDB 域名检测

### 2. 监控申请与执行

- 拨测监控申请
- 任务调度与执行
- 执行日志
- 节点状态与运行信息

### 3. 资产中心

- 多来源资产同步
- 扩展模型管理
- 字段管理
- 导入、冲突处理、同步历史

当前已保留的主要资产来源包括：

- CMDB
- Zabbix 资产同步脚本
- IPMP
- 手工导入

### 4. 运维工具

- IP 正则助手
- 账号同步
- Grafana 同步
- 工具库 / 脚本执行能力

说明：

- 历史上的“代码管理”页面概念已弱化，当前保留的是脚本仓库与脚本执行底座能力。

### 5. 监控与告警

- 拨测可视化总览
- 告警事件
- 监控策略
- 节点运行态
- 执行日志

### 6. 系统设置

- 用户与权限
- 角色模板
- 审计日志
- 通知渠道
- 通知模板
- 平台配置
- 个人资料

不再作为当前功能真相源的历史模块包括：

- 知识库
- analytics 报表域
- 旧监控集成中心
- 旧 `frontend/` 目录结构

---

## 系统架构

### 核心组件

| 组件 | 作用 |
|:-----|:-----|
| 前端 | Vue 3 + Vite + Element Plus 控制台 |
| 后端 | Django + DRF 提供业务 API |
| Celery Worker | 异步任务执行 |
| Celery Beat | 定时调度 |
| Redis | Celery Broker / Result Backend / 缓存 |
| MySQL | 业务数据存储 |
| TimescaleDB | 探针指标与时序结果 |
| gRPC Gateway | 探针与后端通信网关 |
| Probe | Go 编写的探针执行节点 |

### 组件关系

```text
Browser
  -> Frontend (Vue 3)
  -> Backend API (Django)
      -> MySQL
      -> Redis
      -> TimescaleDB
      -> Celery Worker / Beat
      -> gRPC Gateway
          -> Probe Nodes
```

### 依赖关系简表

| 功能 | MySQL | Redis | Celery | TimescaleDB | Probe |
|:-----|:-----:|:-----:|:------:|:-----------:|:-----:|
| 登录与权限 | ✅ | ✅ | - | - | - |
| 一次性检测 | ✅ | ✅ | - | - | ✅ |
| 持续监控 / 调度 | ✅ | ✅ | ✅ | - | ✅ |
| 探针运行指标 | ✅ | - | - | ✅ | ✅ |
| 资产同步 | ✅ | ✅ | ✅ | - | - |
| 告警投递 | ✅ | ✅ | ✅ | - | - |

---

## 代码结构

### 顶层目录

```text
.
├── backend/              # Django 后端
├── probes/               # Go 探针
├── src/                  # Vue 前端
├── deploy/               # 部署与初始化配置
├── docs/                 # 当前结论文档与历史归档
├── scripts/              # 运维/验证脚本
├── specs/                # 历史方案与保留契约
├── Dockerfile            # 前端镜像
├── docker-compose.yml    # 一键部署
└── package.json          # 前端依赖与脚本
```

### 前端结构

```text
src/
├── app/                  # 应用级状态、API、会话
├── features/             # 按业务域组织的主代码
│   ├── alerts/
│   ├── assets/
│   ├── auth/
│   ├── dashboard/
│   ├── detection/
│   ├── monitoring/
│   ├── probes/
│   ├── profile/
│   ├── settings/
│   └── tools/
├── shared/               # 真正跨域复用能力
├── router/               # 路由
├── layouts/              # 布局
└── i18n/                 # 国际化
```

### 后端结构

```text
backend/src/
├── apps/
│   ├── alerts/
│   ├── assets/
│   ├── core/
│   ├── dashboard/
│   ├── monitoring/
│   ├── probes/
│   ├── settings/
│   └── tools/
├── core/
└── manage.py
```

### 文档结构

```text
docs/
├── plans/                # 当前仍有参考价值的审计 / 收官文档
└── archive/plans/        # 历史设计稿与实施计划归档
```

---

## 快速开始

推荐使用 Docker 启动完整系统。

### 1. 准备环境

- Docker 24+
- Docker Compose v2+

### 2. 克隆并配置

```bash
git clone <你的仓库地址>
cd <repo-dir>
cp .env.example .env
```

### 3. 启动服务

```bash
docker compose up -d --build
```

启动后可检查状态：

```bash
docker compose ps
docker compose logs -f
```

### 4. 创建管理员账号

```bash
docker compose exec backend python manage.py createsuperuser
```

### 5. 访问系统

- 前端入口：`http://localhost`

### 6. 注册并启动探针

1. 登录系统
2. 进入“节点”
3. 创建探针节点并获取 `node_id` / `api_token`
4. 在 `.env` 中补充：

```ini
PROBE_NODE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PROBE_API_TOKEN=your-probe-token
```

5. 启动探针服务：

```bash
docker compose --profile probe up -d
```

---

## 本地开发

### 环境要求

| 软件 | 版本 |
|:-----|:-----|
| Node.js | 20+ |
| pnpm | 10+ |
| Python | 3.11 |
| Go | 1.21+ |
| Docker | 24+ |

### 1. 启动数据库

```bash
docker compose -f deploy/local/docker-compose.yml up -d
```

会启动：

- MySQL
- TimescaleDB
- Redis

### 2. 启动后端

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt

cd src
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

另开终端启动 gRPC 网关：

```bash
cd backend/src
python manage.py run_probe_gateway --host 0.0.0.0 --port 50051
```

另开终端启动 Celery Worker：

```bash
cd backend/src
celery -A core.celery_app worker -l info
```

另开终端启动 Celery Beat：

```bash
cd backend/src
celery -A core.celery_app beat -l info
```

### 3. 启动前端

前端位于仓库根目录，不再使用历史 `frontend/` 子目录。

```bash
pnpm install
pnpm dev
```

默认访问地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`

### 4. 编译并启动探针

```bash
cd probes
go build -o probe ./cmd/probe
cp config.example.yaml config.yaml
```

编辑 `config.yaml`：

```yaml
api_base_url: "http://127.0.0.1:8000"
grpc_gateway: "127.0.0.1:50051"
grpc_insecure: true
node_id: ""
api_token: ""
```

运行探针：

```bash
./probe --config config.yaml --debug
```

### 5. 前端常用命令

```bash
pnpm lint
pnpm test:unit
pnpm build
```

### 6. 后端常用命令

```bash
cd backend/src
pytest
```

---

## 配置说明

### 后端配置

后端配置文件：

- `backend/.env.example`
- `backend/.env`

关键变量：

| 配置项 | 说明 |
|:-------|:-----|
| `DEBUG` | Django 调试开关 |
| `SECRET_KEY` | Django 密钥 |
| `ALLOWED_HOSTS` | 允许访问的域名 |
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_DB` / `MYSQL_USER` / `MYSQL_PASSWORD` | 业务数据库 |
| `REDIS_URL` | Redis 连接 |
| `CELERY_BROKER_URL` | Celery Broker |
| `CELERY_RESULT_BACKEND` | Celery Result Backend |
| `TIMESCALE_HOST` / `TIMESCALE_PORT` / `TIMESCALE_DB` / `TIMESCALE_USER` / `TIMESCALE_PASSWORD` | 时序库 |
| `CORS_ALLOWED_ORIGINS` | 前端跨域地址 |
| `CONSOLE_BASE_URL` | 控制台访问地址 |

可选外部集成：

| 配置项 | 说明 |
|:-------|:-----|
| `ZABBIX_API_URL` | Zabbix API 地址 |
| `ZABBIX_API_TOKEN` | Zabbix Token |
| `ZABBIX_VERIFY_TLS` | 是否校验 TLS |

### 前端配置

前端配置位于仓库根目录，常用的是：

- `vite.config.ts`
- 可选的 `.env.local`（仅在需要覆盖本地 Vite 配置时自行创建）

本地开发如需显式覆盖 API 地址，可创建 `.env.local`：

```ini
VITE_API_BASE_URL=/api
```

### Probe 配置

探针配置模板：

- `probes/config.example.yaml`

关键字段：

| 配置项 | 说明 |
|:-------|:-----|
| `api_base_url` | 后端 API 地址 |
| `grpc_gateway` | gRPC 网关地址 |
| `node_id` | 节点 ID |
| `api_token` | 节点 Token |
| `heartbeat_interval` | 心跳间隔 |
| `task_poll_interval` | 拉取任务间隔 |
| `metrics_addr` | Prometheus 指标地址 |

---

## 探针部署

### 方式一：Docker

如果你使用根目录 `docker-compose.yml`，推荐直接启用 `probe` profile。

```bash
docker compose --profile probe up -d
```

### 方式二：手工部署

```bash
cd probes
go build -o probe ./cmd/probe
cp config.example.yaml config.yaml
./probe --config config.yaml --debug
```

### systemd 示例

```ini
[Unit]
Description=OneAll Probe Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/oneall-probe
ExecStart=/opt/oneall-probe/probe --config /opt/oneall-probe/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 生产部署

### 推荐方式

- 前端：根目录 `Dockerfile`
- 后端：`backend/Dockerfile`
- 一键编排：根目录 [docker-compose.yml](./docker-compose.yml)

### 生产最小组件

- Nginx
- Frontend
- Backend
- gRPC Gateway
- Celery Worker
- Celery Beat
- MySQL
- TimescaleDB
- Redis
- Probe

### 生产部署要点

- `DEBUG=False`
- 使用强随机 `SECRET_KEY`
- 正确配置 `ALLOWED_HOSTS`
- 配置 `CONSOLE_BASE_URL`
- Redis / MySQL / TimescaleDB 使用独立持久化卷或独立实例
- 对外暴露 `80/443`
- 探针所在网络需能访问后端 API 与 gRPC 端口

---

## 常见问题

### 前端页面空白

1. 检查浏览器控制台报错
2. 确认前端 `VITE_API_BASE_URL` 配置正确
3. 确认后端 API 可访问

### 后端无法连接数据库

1. 检查 MySQL / Redis / TimescaleDB 是否已启动
2. 检查 `backend/.env` 配置
3. 确认已执行迁移

### Celery 任务不执行

确认以下两个进程都在运行：

- `celery worker`
- `celery beat`

### 探针离线

1. 检查 `api_base_url`
2. 检查 `grpc_gateway`
3. 检查 `node_id` / `api_token`
4. 检查防火墙和端口放行

### 资产同步失败

1. 检查 Celery Worker
2. 检查资产源脚本与外部系统凭据
3. 查看后端日志和 Worker 日志

### 监控 / 可视化没有数据

1. 检查探针是否真正上报结果
2. 检查 TimescaleDB 是否正常
3. 检查后端写入流程和调度执行状态

---

## 相关文档

当前优先参考：

- [docs/plans/README.md](./docs/plans/README.md)
- [docs/plans/2026-04-16-frontend-architecture-audit.md](./docs/plans/2026-04-16-frontend-architecture-audit.md)
- [docs/plans/2026-04-16-frontend-architecture-phase-closeout.md](./docs/plans/2026-04-16-frontend-architecture-phase-closeout.md)

历史过程文档：

- [docs/archive/plans/README.md](./docs/archive/plans/README.md)

保留契约：

- [specs/001-build-oneall-platform/contracts/openapi.yaml](./specs/001-build-oneall-platform/contracts/openapi.yaml)

---

<div align="center">

OneAll

当前真相源以 README、现行源码和保留契约为准。

</div>
