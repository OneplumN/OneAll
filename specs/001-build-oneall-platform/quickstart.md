# Quickstart: OneAll 智能运维平台

## 1. 前置条件
- Node.js 20.x（含 pnpm 8+）
- Python 3.11 与 pipx
- Docker / Docker Compose 2.x（本地启动 MySQL、TimescaleDB、Redis）
- Go 1.21+（仅探针需要）
- 可选：Ansible 2.15+（自动化部署脚本）
- Prometheus 可用实例（可选）
- ITSM、Zabbix、Prometheus、CMDB 等外部系统的测试凭据

## 2. 克隆与初始化
```bash
git clone <repo-url>
cd one-pro
git checkout 001-build-oneall-platform

# 配置环境变量（仅需一次）
cp backend/.env.example backend/.env
vim backend/.env  # 按需更新 MySQL、Timescale、Redis 等连接信息

# 安装前端依赖
cd frontend
pnpm install

# 安装后端依赖
cd ../backend
pipx run pipenv install --python 3.11
pipenv run pip install -r requirements.txt

# 探针依赖
cd ../probes
go mod download
```

## 3. 启动基础服务
```bash
docker compose -f deploy/local/docker-compose.yml up -d \
  mysql timescaledb redis

# 初始化 MySQL 数据库
docker exec -it oneall-mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD:-root} \
  -e "CREATE DATABASE IF NOT EXISTS oneall CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
docker exec -it oneall-mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD:-root} \
  -e "CREATE DATABASE IF NOT EXISTS oneall_metrics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 初始化 TimescaleDB 扩展
docker exec -it oneall-timescaledb psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

## 4. 启动应用组件
```bash
# 后端 API + Celery
cd backend
pipenv run python src/manage.py migrate
pipenv run python src/manage.py runserver 0.0.0.0:8000 &
pipenv run celery -A core.celery_app worker -l info &
pipenv run celery -A core.celery_app beat -l info &

# 前端 Dev Server
cd ../frontend
pnpm run dev --host 0.0.0.0 --port 5173 &

# 本地探针对接
cd ../probes
cp config.example.yaml config.yaml
go build ./cmd/probe
./probe --config config.yaml --debug
```

访问地址：
- 前端：<http://localhost:5173>
- 后端：<http://localhost:8000/api/>

## 5. 外部系统配置
在后台系统设置中填写以下连接信息：
- ITSM API：基础 URL、Client ID、Client Secret
- Zabbix / Prometheus：接口地址、认证信息
- CMDB：GraphQL 或 REST 接入点
- 告警通知：邮件、Webhook、短信模板

## 6. 验证流程
1. 登录后台创建至少一个 ProbeNode，并为该节点生成 API Token；或允许探针首次心跳自动注册并回写 token。
2. 在 `config.yaml` 中配置 `api_base_url`、`node_id`、`api_token`、`grpc_gateway`，启动探针并确认心跳成功。
3. 访问探针指标端点（默认 `http://localhost:9100/probe/metrics`）确认心跳与任务统计更新；如端口有变化以 `metrics_addr` 为准。
4. 使用一次性拨测工具对目标域名执行 HTTP 与证书检测，确认 MySQL 中拨测结果入库且 TimescaleDB/Prometheus 中可看到指标。
5. 提交拨测监控申请，检查 ITSM 工单生成并回调任务列表。
6. 触发资产同步，验证 AssetRecord 表数据更新。
7. 在工具库上传脚本并执行，确认结果回写 DetectionTask。
8. 发布知识库文章，确认可检索并在审计日志中可见。

## 7. 测试套件
```bash
# 前端单元与端到端
cd frontend
pnpm run test
pnpm run test:e2e

# 后端测试
cd ../backend
pipenv run pytest

# 探针集成测试
cd ../probes
go test ./...
```

## 8. 监控与日志
- 业务指标暴露在 `/metrics`（后端）与 `/probe/metrics`（探针）
- 探针鉴权使用 `Authorization: ProbeToken <api_token>`，需确保 token 与 `ProbeNode` 记录一致
- 结构化日志输出到 stdout，并由 Filebeat/Fluent Bit 采集（部署时配置）

## 9. 备份与维护
- MySQL 定期执行 `mysqldump` + binlog 归档；TimescaleDB 使用 `pg_dump` + WAL 归档；Redis 持久化 RDB/AOF
- 计划维护窗口安排在周六/周日，执行前创建 Git Tag 与数据库备份记录
- Celery 任务、ITSM 回调队列需要在维护完成后手动校验重试

## 10. 常见问题
- **探针离线**：检查 proxy 映射与 probe 配置；确认心跳端口放行
- **ITSM 回调失败**：查看后台补偿队列，重试前确保 ITSM 访问凭据有效
- **报表生成超时**：检查 MySQL 分区策略与 TimescaleDB Hypertable 设计；必要时扩容计算资源

## 11. Quickstart 校验记录
| 日期 | 负责人 | 覆盖范围 | 结果 |
|------|--------|----------|------|
| 2025-11-06 | demo-admin | Probe / Detection / ITSM / Asset / Tool / Knowledge | ✅ 全部完成，演示数据由 `seed_demo_data` 生成 |
