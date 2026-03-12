<div align="center">

# 🚀 OneAll

### 智能运维平台

*探针为眼，数据为脉，让运维更简单*

[![Vue 3](https://img.shields.io/badge/Vue-3.x-42b883?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Django](https://img.shields.io/badge/Django-4.2-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Go](https://img.shields.io/badge/Go-1.21+-00add8?style=for-the-badge&logo=go&logoColor=white)](https://go.dev/)

</div>

---

## 📖 目录

- [这是什么](#-这是什么)
- [功能模块](#-功能模块)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [配置详解](#-配置详解)
- [探针部署](#-探针部署)
- [生产部署](#-生产部署)
- [常见问题](#-常见问题)

---

## 💡 这是什么

**OneAll** 是一个智能运维平台，通过分布式探针网络监控您的基础设施健康状况。

**它能帮你做什么？**

- 🔍 **拨测检测** - 定时或手动检测网站、API、端口是否正常
- 📜 **证书监控** - 自动检测 HTTPS 证书到期时间，提前预警
- 📊 **统一监控** - 整合 Zabbix、Prometheus 数据，一个界面看所有
- 🗂️ **资产管理** - 自动同步 CMDB、Zabbix 主机信息
- 📚 **知识库** - 团队运维经验沉淀

---

## ✨ 功能模块

### 模块总览

| 模块 | 功能 | 依赖组件 |
|:-----|:-----|:---------|
| 🔍 一次性拨测 | HTTP/HTTPS/TCP/Telnet/WSS 即时检测 | 探针 |
| 📜 证书检测 | TLS 证书有效期、证书链完整性检测 | 探针 |
| 📡 持续监控 | 创建定时拨测任务，自动告警 | 探针 + Celery |
| 📊 监控集成 | Zabbix/Prometheus 数据展示 | 对应的外部系统 |
| 🗂️ 资产中心 | 多源资产同步与管理 | Celery |
| 📈 统计报表 | 拨测成功率、响应时间趋势分析 | TimescaleDB |
| 🛠️ 工具库 | 脚本工具管理与执行 | - |
| 📚 知识库 | 文档管理、版本控制 | - |
| ⚙️ 系统设置 | 用户、权限、告警通道配置 | - |

### 模块详细说明

#### 🔍 一次性拨测

**功能**：对目标地址进行即时检测，查看是否可达、响应时间、返回内容等。

**支持的协议**：

| 协议 | 检测内容 | 配置项 |
|:-----|:---------|:-------|
| HTTP/HTTPS | 状态码、响应时间、响应体 | Method、Headers、Body、预期状态码 |
| TCP | 端口连通性、Banner 信息 | 端口、Payload、预期返回 |
| Telnet | 端口连通性、Banner 信息 | 端口、Payload、预期返回 |
| WebSocket (WSS) | 握手验证、消息收发 | Payload、预期响应、子协议 |
| Certificate | 证书有效期、证书链、颁发者 | 过期预警天数 |

**依赖**：需要至少部署一个探针节点。

---

#### 📡 持续监控（拨测调度）

**功能**：创建定时拨测任务，按设定频率自动执行检测，异常时触发告警。

**工作流程**：
1. 用户提交监控申请（可对接 ITSM 审批）
2. 审批通过后自动创建调度任务
3. Celery Beat 按频率触发任务
4. 探针执行检测并上报结果
5. 连续失败达到阈值时发送告警

**告警通道**：
- 邮件（SMTP）
- 企业微信（Webhook）
- 钉钉（Webhook）
- 飞书（Webhook）
- 自定义 HTTP 回调

**依赖**：探针 + Celery Worker + Celery Beat

---

#### 📈 统计报表

**功能**：展示拨测历史数据的统计分析。

| 指标 | 说明 |
|:-----|:-----|
| 成功率 | 一段时间内拨测成功的比例 |
| 平均响应时间 | 响应时间的平均值、P95、P99 |
| 趋势图 | 响应时间和成功率的时间趋势 |
| 节点分布 | 各探针节点的执行情况 |

**依赖**：**TimescaleDB**（时序数据库）

---

#### 📊 监控集成

**功能**：对接外部监控系统，统一展示监控数据。

| 集成 | 功能 | 配置位置 |
|:-----|:-----|:---------|
| Zabbix | 主机列表、主机组、告警状态 | 系统设置 → 插件配置 |
| Prometheus | 指标查询、告警规则 | 系统设置 → 插件配置 |

**依赖**：对应的外部监控系统已部署并可访问

---

#### 🗂️ 资产中心

**功能**：从多个数据源同步资产信息，统一管理。

| 数据源 | 同步内容 |
|:-------|:---------|
| CMDB | 域名、系统、负责人 |
| Zabbix | 主机 IP、主机名、主机组、Proxy |
| IPMP | 应用编号、项目名称、负责人、等保级别 |
| 手动导入 | CSV/Excel 批量导入 |

**同步方式**：
- 手动触发：点击「同步」按钮
- 定时同步：Celery Beat 每日凌晨自动执行

**依赖**：Celery Worker + Celery Beat

---

#### 📚 知识库

**功能**：团队运维经验沉淀，支持文档管理。

| 特性 | 说明 |
|:-----|:-----|
| 格式支持 | Markdown、Word（.docx）、HTML |
| 版本控制 | 自动保存历史版本，可回滚 |
| 权限控制 | 公开、内部、受限三级可见性 |
| 分类管理 | 自定义目录分类 |

**依赖**：无额外依赖

---

## 🏗️ 系统架构

### 组件关系图

```
┌─────────────────────────────────────────────────────────────────────┐
│                              用户浏览器                              │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Nginx (反向代理)                             │
│                    处理 HTTPS、静态文件、负载均衡                      │
└───────────────┬─────────────────────────────────────┬───────────────┘
                │                                     │
                ▼                                     ▼
┌───────────────────────────┐         ┌───────────────────────────────┐
│        Frontend           │         │          Backend              │
│     Vue 3 + Element+      │         │    Django + DRF + Celery      │
│      (静态文件部署)         │         │                               │
└───────────────────────────┘         └───────────────┬───────────────┘
                                                      │
                ┌─────────────────────────────────────┼─────────────────────────────────────┐
                │                                     │                                     │
                ▼                                     ▼                                     ▼
┌───────────────────────────┐         ┌───────────────────────────┐         ┌───────────────────────────┐
│          MySQL            │         │       TimescaleDB         │         │          Redis            │
│        业务数据存储         │         │       时序指标存储         │         │     缓存 + 消息队列        │
│  用户、资产、任务、知识库等   │         │  探针指标、拨测历史趋势     │         │   Celery Broker/Result    │
└───────────────────────────┘         └───────────────────────────┘         └───────────────────────────┘

                                                      │
                                                      │ gRPC
                                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            探针节点                                  │
│                     Go Agent（可部署多个）                            │
│              执行拨测任务、上报心跳、采集指标                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 必需 | 说明 |
|:-----|:----:|:-----|
| **Frontend** | ✅ | Vue 3 单页应用，提供用户界面 |
| **Backend (Django)** | ✅ | 核心 API 服务，处理业务逻辑 |
| **MySQL** | ✅ | 存储业务数据（用户、资产、任务、文章等） |
| **Redis** | ✅ | Celery 消息队列 + 结果存储 + 缓存 |
| **Celery Worker** | ✅ | 执行异步任务（资产同步、告警发送等） |
| **Celery Beat** | ✅ | 定时任务调度（定时拨测、定时同步） |
| **TimescaleDB** | ✅ | 存储时序指标（探针运行指标、拨测结果历史） |
| **探针 (Probe)** | ✅ | 执行拨测检测的分布式节点 |
| **gRPC Gateway** | ✅ | 探针与后端的通信网关 |

### 功能与组件依赖关系

| 功能 | MySQL | Redis | Celery | TimescaleDB | 探针 |
|:-----|:-----:|:-----:|:------:|:-----------:|:----:|
| 用户登录 | ✅ | ✅ | - | - | - |
| 一次性拨测 | ✅ | ✅ | - | - | ✅ |
| 持续监控 | ✅ | ✅ | ✅ | - | ✅ |
| 统计报表 | ✅ | - | - | ✅ | - |
| 资产同步 | ✅ | ✅ | ✅ | - | - |
| 知识库 | ✅ | - | - | - | - |
| 告警通知 | ✅ | ✅ | ✅ | - | - |

---

## 🚀 快速开始

有两种部署方式，推荐使用 **Docker 一键部署**。

### 方式一：Docker 一键部署（推荐）👍

只需安装 Docker，即可一键启动所有服务。

#### 第一步：安装 Docker

| 软件 | 版本 | 安装方式 |
|:-----|:-----|:---------|
| Docker | 24+ | https://www.docker.com/ |
| Docker Compose | v2+ | Docker Desktop 已包含 |

#### 第二步：克隆代码并启动

```bash
# 克隆代码
git clone <你的仓库地址>
cd one-pro

# 复制环境变量配置
cp .env.example .env

# 一键启动所有服务
docker compose up -d
```

等待镜像构建和服务启动（首次约 5-10 分钟），可通过以下命令查看状态：

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

#### 第三步：创建管理员账号

```bash
docker compose exec backend python manage.py createsuperuser
```

按提示输入用户名、邮箱、密码。

#### 第四步：访问系统

打开浏览器访问 **http://localhost**

使用刚才创建的管理员账号登录。

#### 第五步：注册并启动探针

1. 登录后进入「探针管理」→「探针节点」→「新增探针」
2. 填写探针名称（如 `local-probe`），点击创建
3. 复制 **探针 ID** 和 **API Token**
4. 编辑 `.env` 文件，填入探针信息：

```ini
PROBE_NODE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PROBE_API_TOKEN=your-probe-token
```

5. 启动探针容器：

```bash
docker compose --profile probe up -d
```

6. 在管理界面刷新，确认探针状态变为「在线」

#### 第六步：验证部署

1. 进入「一次性拨测」页面
2. 输入目标地址（如 `https://www.baidu.com`）
3. 选择探针节点，点击「检测」
4. 查看拨测结果

🎉 **部署完成！**

#### 常用 Docker 命令

```bash
# 停止所有服务
docker compose down

# 重启服务
docker compose restart

# 查看某个服务日志
docker compose logs -f backend

# 进入后端容器执行命令
docker compose exec backend bash
```

---

### 方式二：本地开发部署

适合需要修改代码的开发者。

#### 第一步：环境准备

**你需要安装：**

| 软件 | 版本 | 用途 | 安装方式 |
|:-----|:-----|:-----|:---------|
| Node.js | 20.x | 前端构建 | https://nodejs.org/ |
| pnpm | 8+ | 前端包管理 | `npm install -g pnpm` |
| Python | 3.11 | 后端运行 | https://www.python.org/ |
| Docker | 24+ | 运行数据库 | https://www.docker.com/ |
| Go | 1.21+ | 编译探针 | https://go.dev/ |

#### 第二步：克隆代码

```bash
git clone <你的仓库地址>
cd one-pro
```

#### 第三步：启动数据库

```bash
docker compose -f deploy/local/docker-compose.yml up -d
```

这会启动：
- `oneall-mysql` - 业务数据库 (端口 3306)
- `oneall-timescaledb` - 时序数据库 (端口 5432)
- `oneall-redis` - 缓存和消息队列 (端口 6379)

> ⚠️ **端口冲突？** 如果本地已有这些服务，请先停止或修改 `deploy/local/docker-compose.yml` 中的端口。

#### 第四步：配置后端

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件（详见 [配置详解](#-配置详解)）。

**本地开发最小配置**：

```ini
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DB=oneall
MYSQL_USER=root
MYSQL_PASSWORD=root

# Redis
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1

# TimescaleDB
TIMESCALE_HOST=127.0.0.1
TIMESCALE_PORT=5432
TIMESCALE_DB=oneall_metrics
TIMESCALE_USER=postgres
TIMESCALE_PASSWORD=postgres

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

#### 第五步：初始化数据库

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# MySQL 数据库迁移
cd src
python manage.py migrate

# 创建管理员账号（按提示输入用户名、邮箱、密码）
python manage.py createsuperuser
```

**初始化 TimescaleDB（创建时序表）**：

```bash
# 连接到 TimescaleDB 并执行初始化 SQL
docker exec -i oneall-timescaledb psql -U postgres -d oneall_metrics << 'EOF'
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS probe_runtime_metrics (
    id BIGSERIAL NOT NULL,
    probe_id UUID NOT NULL,
    node_name TEXT NOT NULL,
    uptime_seconds BIGINT NOT NULL,
    heartbeats_sent BIGINT NOT NULL,
    heartbeats_failed BIGINT NOT NULL,
    heartbeats_last_success TIMESTAMPTZ NULL,
    tasks_fetched BIGINT NOT NULL,
    tasks_executed BIGINT NOT NULL,
    tasks_failed BIGINT NOT NULL,
    queue_depth BIGINT NOT NULL,
    queue_capacity BIGINT NOT NULL,
    active_workers BIGINT NOT NULL,
    metrics_generated_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, recorded_at)
);

SELECT create_hypertable('probe_runtime_metrics', 'recorded_at', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS probe_detection_results (
    detection_id UUID NOT NULL,
    probe_id UUID NULL,
    protocol VARCHAR(32) NOT NULL,
    target TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    response_time_ms INTEGER NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (detection_id, recorded_at)
);

SELECT create_hypertable('probe_detection_results', 'recorded_at', if_not_exists => TRUE);
EOF
```

#### 第六步：启动后端服务

需要启动 **四个进程**（建议开四个终端）：

**终端 1 - Django API 服务**：
```bash
cd backend/src
python manage.py runserver 0.0.0.0:8000
```

**终端 2 - gRPC Gateway（探针通信网关）**：
```bash
cd backend/src
python manage.py run_probe_gateway --port 50051
```

**终端 3 - Celery Worker（异步任务执行）**：
```bash
cd backend/src
celery -A core.celery_app worker -l info
```

**终端 4 - Celery Beat（定时任务调度）**：
```bash
cd backend/src
celery -A core.celery_app beat -l info
```

#### 第七步：启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

#### 第八步：编译并部署探针

探针是执行拨测任务的核心组件，必须至少部署一个。

```bash
# 编译探针
cd probes
go build -o probe ./cmd/probe

# 复制配置模板
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，填写以下必要配置：

```yaml
api_base_url: "http://127.0.0.1:8000"
grpc_gateway: "127.0.0.1:50051"
grpc_insecure: true
node_id: ""      # 第九步获取
api_token: ""    # 第九步获取
```

#### 第九步：注册探针并启动

1. 打开浏览器访问 **http://localhost:5173**
2. 使用第五步创建的管理员账号登录
3. 进入「探针管理」→「探针节点」→「新增探针」
4. 填写探针名称（如 `local-probe`），点击创建
5. 复制 **探针 ID** 和 **API Token**，填入 `config.yaml`
6. 启动探针（在 probes 目录下）：

```bash
./probe --config config.yaml --debug
```

7. 在管理界面刷新，确认探针状态变为「在线」

#### 第十步：验证部署

1. 进入「一次性拨测」页面
2. 输入目标地址（如 `https://www.baidu.com`）
3. 选择探针节点，点击「检测」
4. 查看拨测结果

🎉 **部署完成！**

---

## ⚙️ 配置详解

### 后端配置 (.env)

#### Django 基础配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-------|:----:|:-------|:-----|
| `DEBUG` | ✅ | - | 调试模式，生产环境必须设为 `False` |
| `SECRET_KEY` | ✅ | - | Django 密钥，生产环境使用随机长字符串 |
| `ALLOWED_HOSTS` | ✅ | - | 允许访问的域名，逗号分隔 |

#### MySQL 配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-------|:----:|:-------|:-----|
| `MYSQL_HOST` | ✅ | - | MySQL 服务器地址 |
| `MYSQL_PORT` | ✅ | `3306` | MySQL 端口 |
| `MYSQL_DB` | ✅ | - | 数据库名称 |
| `MYSQL_USER` | ✅ | - | 用户名 |
| `MYSQL_PASSWORD` | ✅ | - | 密码 |

#### Redis 配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-------|:----:|:-------|:-----|
| `REDIS_URL` | ✅ | - | Redis 连接地址，格式：`redis://[:password@]host:port/db` |
| `CELERY_BROKER_URL` | ✅ | - | Celery 消息队列地址，通常与 REDIS_URL 相同 |
| `CELERY_RESULT_BACKEND` | ✅ | - | Celery 结果存储地址，建议用不同的 db 号 |

#### TimescaleDB 配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-------|:----:|:-------|:-----|
| `TIMESCALE_HOST` | ✅ | `localhost` | TimescaleDB 地址 |
| `TIMESCALE_PORT` | ✅ | `5432` | TimescaleDB 端口 |
| `TIMESCALE_DB` | ✅ | `oneall_metrics` | 数据库名 |
| `TIMESCALE_USER` | ✅ | `postgres` | 用户名 |
| `TIMESCALE_PASSWORD` | ✅ | `postgres` | 密码 |


#### 外部集成配置（可选）

| 配置项 | 说明 |
|:-------|:-----|
| `ZABBIX_API_URL` | Zabbix API 地址，如 `http://zabbix.example.com/api_jsonrpc.php` |
| `ZABBIX_API_TOKEN` | Zabbix API Token |
| `ZABBIX_VERIFY_TLS` | 是否验证 TLS 证书，默认 `True` |

#### 其他配置

| 配置项 | 说明 |
|:-------|:-----|
| `CORS_ALLOWED_ORIGINS` | 允许跨域的前端地址，如 `http://localhost:5173` |
| `CONSOLE_BASE_URL` | 控制台地址，用于告警消息中的链接 |

### 前端配置

前端配置文件位于 `frontend/` 目录：

**开发环境** (`.env.development`)：
```ini
VITE_API_BASE_URL=/api
```

> 开发环境使用 Vite 代理，自动将 `/api` 请求转发到 `http://127.0.0.1:8000`。

**生产环境**：

Docker 部署时，Nginx 会自动代理 `/api` 请求到后端，无需额外配置。

---

## 📡 探针部署

探针是部署在目标网络中的检测程序，负责执行拨测任务并上报结果。

### 部署前准备

1. 登录 OneAll 管理界面
2. 进入「探针管理」→「探针节点」
3. 点击「新增探针」，填写：
   - 名称：如 `probe-beijing-01`
   - 位置：如 `北京机房`
   - 网络类型：内网 / 外网
   - 支持协议：HTTP、HTTPS、TCP 等
4. 创建成功后，记录 **探针 ID**
5. 点击「重置 Token」，记录 **API Token**

### 方式一：使用预编译版本（推荐）

我们提供了 Linux amd64 预编译版本：

```bash
# 在目标服务器上
mkdir -p /opt/oneall-probe && cd /opt/oneall-probe

# 解压（从项目的 probes/ 目录获取）
tar -xzf probe-linux-amd64.tar.gz

# 创建配置文件
cp config.example.yaml config.yaml
vim config.yaml
```

### 方式二：自行编译

需要 Go 1.21+ 环境：

```bash
cd probes
go build -o probe ./cmd/probe

# 交叉编译 Linux 版本
GOOS=linux GOARCH=amd64 go build -o probe-linux-amd64 ./cmd/probe
```

### 探针配置 (config.yaml)

```yaml
# ========== 必填配置 ==========

# 后端 API 地址（不含 /api 后缀）
api_base_url: "http://your-oneall-server:8000"

# 探针 ID（从管理界面「探针管理」获取）
node_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# 探针 Token（从管理界面「重置 Token」获取）
api_token: "your-probe-token"

# gRPC 网关地址（后端 gRPC 服务地址）
grpc_gateway: "your-oneall-server:50051"

# ========== 网络配置 ==========

# 跳过 gRPC TLS 验证（测试环境可设为 true）
grpc_insecure: true

# gRPC TLS 证书（生产环境配置）
grpc_ca_file: ""
grpc_client_cert: ""
grpc_client_key: ""

# 跳过 HTTP TLS 验证（不建议生产环境使用）
insecure_skip_tls: false

# ========== 性能配置 ==========

# 心跳间隔（秒），向后端报告存活状态
heartbeat_interval: 30

# 任务轮询间隔（秒）
task_poll_interval: 15

# HTTP 请求超时（秒）
request_timeout: 10

# 最大并发任务数
max_concurrent_tasks: 4

# 任务重试次数
task_retry_limit: 2

# ========== 存储配置 ==========

# 结果缓存路径（网络断开时缓存结果，恢复后上报）
result_cache_path: "/var/lib/oneall-probe/cache/results.json"

# 缓存条数上限
result_cache_limit: 200

# 调度状态存储路径
schedule_store_path: "/var/lib/oneall-probe/state/schedules.json"

# 自更新下载目录（留空禁用自更新）
update_dir: "/var/lib/oneall-probe/updates"

# ========== 监控配置 ==========

# 指标暴露端口（留空禁用）
# 访问 http://probe-ip:9100/probe/metrics 查看指标
metrics_addr: ":9100"

# OpenTelemetry Collector 地址（留空禁用）
otlp_collector: ""
```

### 启动探针

**调试模式**：
```bash
./probe --config config.yaml --debug
```

**后台运行**：
```bash
nohup ./probe --config config.yaml > /var/log/oneall-probe.log 2>&1 &
```

### 使用 systemd 管理（推荐）

创建 `/etc/systemd/system/oneall-probe.service`：

```ini
[Unit]
Description=OneAll Probe Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/oneall-probe
ExecStart=/opt/oneall-probe/probe --config /opt/oneall-probe/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 创建数据目录
mkdir -p /var/lib/oneall-probe/{cache,state,updates}

# 启动服务
systemctl daemon-reload
systemctl enable oneall-probe
systemctl start oneall-probe

# 查看状态
systemctl status oneall-probe

# 查看日志
journalctl -u oneall-probe -f
```

### 验证探针状态

1. 在管理界面「探针管理」查看探针状态是否变为「在线」
2. 查看「最后心跳时间」是否在更新
3. 创建一个一次性拨测任务测试

---

## 🏭 生产部署

### 部署架构

```
                         ┌─────────────────┐
                         │   DNS / CDN     │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     Nginx       │ ← HTTPS 终结、静态文件、反向代理
                         │   (端口 443)    │
                         └────────┬────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
     ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
     │  Frontend   │       │   Backend   │       │  gRPC GW    │
     │  (静态文件)  │       │  (Gunicorn) │       │  (端口50051) │
     └─────────────┘       └─────────────┘       └─────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
  │    MySQL    │          │ TimescaleDB │          │    Redis    │
  │  (主从复制)  │          │             │          │  (哨兵模式)  │
  └─────────────┘          └─────────────┘          └─────────────┘
```

### 前端构建

```bash
cd frontend
pnpm build
```

产物在 `dist/` 目录，部署到 Nginx 静态文件目录。

### 后端部署

**使用 Gunicorn**：

```bash
cd backend/src
gunicorn core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile /var/log/oneall/access.log \
    --error-logfile /var/log/oneall/error.log
```

**使用 systemd 管理后端**：

创建 `/etc/systemd/system/oneall-backend.service`：

```ini
[Unit]
Description=OneAll Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/oneall/backend/src
ExecStart=/usr/bin/gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

**gRPC Gateway（探针通信网关）**：

创建 `/etc/systemd/system/oneall-grpc-gateway.service`：

```ini
[Unit]
Description=OneAll gRPC Gateway
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/oneall/backend/src
ExecStart=/usr/bin/python manage.py run_probe_gateway --port 50051
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Worker**：

创建 `/etc/systemd/system/oneall-celery-worker.service`：

```ini
[Unit]
Description=OneAll Celery Worker
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/oneall/backend/src
ExecStart=/usr/bin/celery -A core.celery_app worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Beat**：

创建 `/etc/systemd/system/oneall-celery-beat.service`：

```ini
[Unit]
Description=OneAll Celery Beat
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/oneall/backend/src
ExecStart=/usr/bin/celery -A core.celery_app beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx 配置

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书
    ssl_certificate /etc/ssl/certs/your-domain.pem;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    # 前端静态文件
    location / {
        root /var/www/oneall/frontend;
        try_files $uri $uri/ /index.html;
        expires 1d;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # WebSocket（如果需要）
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 生产环境 .env 配置要点

```ini
# 关闭调试模式
DEBUG=False

# 使用强密钥（可用 python -c "import secrets; print(secrets.token_urlsafe(50))" 生成）
SECRET_KEY=your-very-long-random-secret-key

# 配置允许的域名
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# 数据库使用独立服务器
MYSQL_HOST=your-mysql-server
MYSQL_PASSWORD=strong-password

# Redis 配置密码
REDIS_URL=redis://:redis-password@redis-server:6379/0

# 配置控制台地址（用于告警消息中的链接）
CONSOLE_BASE_URL=https://your-domain.com
```

---

## ❓ 常见问题

### 启动问题

**Q: Docker 容器启动失败？**

检查端口占用：
```bash
lsof -i :3306  # MySQL
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

**Q: 后端报数据库连接错误？**

1. 确认 Docker 容器正在运行：`docker ps`
2. 确认 `.env` 配置正确
3. 测试连接：`mysql -h 127.0.0.1 -u root -p`

**Q: Celery 任务不执行？**

确认 Worker 和 Beat 都在运行：
```bash
ps aux | grep celery
```

### 前端问题

**Q: 前端报 CORS 错误？**

- Docker 部署：检查 Nginx 是否正确代理 `/api/` 到后端
- 本地开发：检查 Vite 代理配置是否正确

**Q: 前端页面空白？**

1. 检查浏览器控制台是否有错误
2. 确认后端服务正常运行
3. 本地开发时确认 Vite 代理配置正确

### 探针问题

**Q: 探针状态一直是离线？**

1. 检查 `api_base_url` 是否正确（能从探针服务器访问）
2. 检查 `node_id` 和 `api_token` 是否正确
3. 检查防火墙是否放行端口
4. 使用 `--debug` 启动查看详细日志

**Q: 探针心跳正常但任务不执行？**

1. 检查 `grpc_gateway` 是否正确
2. 检查 gRPC 端口是否开放
3. 如果使用 TLS，检查证书配置

### 功能问题

**Q: 统计报表没有数据？**

1. 确认 TimescaleDB 已配置并正常运行
2. 确认已执行 TimescaleDB 初始化（第五步）
3. 确认探针已上报数据

**Q: 资产同步失败？**

1. 检查 Celery Worker 是否运行
2. 检查外部系统（CMDB/Zabbix）API 凭据是否正确
3. 查看 Celery 日志排查错误

---

## 📂 目录结构

```
one-pro/
├── backend/                    # 后端代码
│   ├── src/
│   │   ├── apps/               # 业务模块
│   │   │   ├── core/           # 用户、认证、审计
│   │   │   ├── probes/         # 探针管理
│   │   │   ├── monitoring/     # 监控任务
│   │   │   ├── assets/         # 资产管理
│   │   │   ├── analytics/      # 统计分析
│   │   │   ├── tools/          # 工具库
│   │   │   ├── knowledge/      # 知识库
│   │   │   └── settings/       # 系统设置
│   │   ├── core/               # Django 配置
│   │   └── manage.py
│   ├── Dockerfile              # 后端 Docker 镜像
│   ├── .env.example            # 配置模板
│   └── requirements.txt
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   ├── components/         # 通用组件
│   │   ├── services/           # API 调用
│   │   ├── stores/             # 状态管理
│   │   └── router/             # 路由配置
│   ├── Dockerfile              # 前端 Docker 镜像
│   ├── nginx.conf              # Nginx 配置
│   └── package.json
├── probes/                     # 探针代码 (Go)
│   ├── cmd/probe/              # 入口
│   ├── internal/
│   │   ├── agent/              # Agent 核心
│   │   ├── plugins/            # 协议插件
│   │   ├── scheduler/          # 任务调度
│   │   └── transport/          # gRPC 通信
│   ├── Dockerfile              # 探针 Docker 镜像
│   └── config.example.yaml     # 配置模板
├── deploy/
│   ├── docker/                 # Docker 部署配置
│   │   ├── init-timescale.sql  # TimescaleDB 初始化
│   │   └── probe-config.yaml   # 探针配置模板
│   └── local/
│       └── docker-compose.yml  # 本地开发（仅数据库）
├── docker-compose.yml          # 一键部署配置
├── .env.example                # 环境变量模板
├── scripts/                    # 运维脚本
├── specs/                      # 设计文档
├── data/                       # 数据文件
├── dream.md                    # 产品需求文档
└── README.md                   # 本文档
```

---

## 📚 更多文档

| 文档 | 说明 |
|:-----|:-----|
| [dream.md](./dream.md) | 产品需求和功能规划 |
| [specs/](./specs/) | 详细设计与技术方案 |

---

<div align="center">

**OneAll** — 让运维更简单

如有问题，请提交 Issue 或联系开发团队

</div>
