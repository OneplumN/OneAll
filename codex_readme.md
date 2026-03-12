# One-Pro 小白部署清单（Codex 版）

这份文档给**第一次部署**的人用，只走最简单的 Docker 路线。  
目标：你按顺序执行，最终可以在浏览器打开系统并完成一次拨测。

---

## 0）开始前确认（3 分钟）

- [ ] 已安装 Docker Desktop（建议 24+，并确认 `docker compose` 可用）
- [ ] 本机端口未被占用：`80`、`3306`、`5432`、`6379`、`50051`
- [ ] 你在项目根目录（有 `docker-compose.yml` 的目录）

可选检查命令：

```bash
docker --version
docker compose version
```

---

## 1）拉代码并进入目录

- [ ] 克隆项目并进入目录

```bash
git clone <你的仓库地址>
cd one-pro
```

---

## 2）初始化环境变量

- [ ] 复制环境变量模板

```bash
cp .env.example .env
```

- [ ] （建议）把 `.env` 里的 `SECRET_KEY` 改成随机字符串（生产环境必须改）

可用下面命令生成：

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 3）启动核心服务

- [ ] 启动（不含 probe）

```bash
docker compose up -d
```

- [ ] 查看状态（直到大部分服务为 `Up` / `healthy`）

```bash
docker compose ps
docker compose logs -f
```

> 首次构建一般需要 5~10 分钟，耐心等一会儿。

---

## 4）创建管理员账号

- [ ] 执行创建管理员命令

```bash
docker compose exec backend python manage.py createsuperuser
```

- [ ] 记录好用户名和密码

---

## 5）登录系统

- [ ] 打开浏览器访问：`http://localhost`
- [ ] 用上一步创建的管理员账号登录

---

## 6）注册探针并启动（关键步骤）

1. [ ] 登录后进入：`探针管理` → `探针节点` → `新增探针`
2. [ ] 创建探针后，复制 `探针 ID` 和 `API Token`
3. [ ] 回到项目根目录，编辑 `.env` 填入：

```ini
PROBE_NODE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PROBE_API_TOKEN=your-probe-token
```

4. [ ] 启动探针服务

```bash
docker compose --profile probe up -d
```

5. [ ] 回到页面刷新，确认探针状态变为“在线”

---

## 7）验证部署是否成功

1. [ ] 进入“一次性拨测”页面
2. [ ] 输入目标地址（例如：`https://www.baidu.com`）
3. [ ] 选择探针节点，点击“检测”
4. [ ] 能看到检测结果即部署成功

---

## 8）常用运维命令

```bash
# 停止所有服务
docker compose down

# 重启所有服务
docker compose restart

# 查看后端日志
docker compose logs -f backend

# 进入后端容器
docker compose exec backend bash
```

---

## 9）最常见问题（小白排错）

### 问题 A：`docker compose up -d` 后服务起不来

- [ ] 先看日志：`docker compose logs -f`
- [ ] 检查端口冲突（尤其是 80/3306/5432/6379）
- [ ] Docker Desktop 是否正常运行

### 问题 B：能登录，但探针一直离线

- [ ] 是否已经在后台创建了探针节点
- [ ] `.env` 中 `PROBE_NODE_ID`、`PROBE_API_TOKEN` 是否填对
- [ ] 修改 `.env` 后是否重新执行了：`docker compose --profile probe up -d`

### 问题 C：页面打不开 `http://localhost`

- [ ] 看前端容器状态：`docker compose ps`
- [ ] 看前端日志：`docker compose logs -f frontend`
- [ ] 本机 80 端口是否被其他程序占用

---

## 10）完成标准（全部满足才算完成）

- [ ] `docker compose ps` 中核心服务均正常
- [ ] 可以访问 `http://localhost` 并登录
- [ ] 探针状态显示“在线”
- [ ] 一次性拨测能返回结果

如果你希望，我可以继续给你补一份：

- `codex_readme_prod.md`（生产部署版）
- `codex_readme_local_dev.md`（本地开发版，4 进程启动）

