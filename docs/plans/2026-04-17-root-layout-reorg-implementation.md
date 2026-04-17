# Root Layout Reorg Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将当前拥挤的仓库根目录收口成 `frontend/ + backend/ + probes/ + infra/` 结构，并保持前后端、Docker 与文档路径一致。

**Architecture:** 前端完整迁回 `frontend/` 子目录；所有运行基础设施文件统一迁入 `infra/`；根目录仅保留项目入口文件与主模块目录。迁移后同步修正 Docker 构建上下文、README、测试与脚本路径，并通过前后端验证确保无回归。

**Tech Stack:** Vue 3 + Vite + pnpm，Django + pytest，Go probe，Docker Compose，Nginx

---

### Task 1: 建立目标目录骨架

**Files:**
- Create: `frontend/`
- Create: `infra/`
- Create: `infra/local/`
- Create: `infra/probe/`
- Create: `infra/timescale/`

**Step 1: 创建新目录**

Run:

```bash
mkdir -p frontend infra/local infra/probe infra/timescale
```

**Step 2: 验证目录存在**

Run:

```bash
find frontend infra -maxdepth 2 -type d | sort
```

Expected:
- 能看到 `frontend`
- 能看到 `infra/local`
- 能看到 `infra/probe`
- 能看到 `infra/timescale`

### Task 2: 迁移前端源码与前端配置

**Files:**
- Move: `src/ -> frontend/src/`
- Move: `tests/ -> frontend/tests/`
- Move: `package.json -> frontend/package.json`
- Move: `pnpm-lock.yaml -> frontend/pnpm-lock.yaml`
- Move: `vite.config.ts -> frontend/vite.config.ts`
- Move: `vitest.config.ts -> frontend/vitest.config.ts`
- Move: `vitest.setup.ts -> frontend/vitest.setup.ts`
- Move: `playwright.config.ts -> frontend/playwright.config.ts`
- Move: `tsconfig.json -> frontend/tsconfig.json`
- Move: `env.d.ts -> frontend/env.d.ts`
- Move: `index.html -> frontend/index.html`
- Move: `.eslintignore -> frontend/.eslintignore`
- Move: `.eslintrc.cjs -> frontend/.eslintrc.cjs`
- Move: `.prettierignore -> frontend/.prettierignore`
- Move: `.prettierrc.cjs -> frontend/.prettierrc.cjs`

**Step 1: 搬迁文件**

使用 `mv` 完成文件和目录迁移。

**Step 2: 检查前端目录结构**

Run:

```bash
find frontend -maxdepth 2 -type f | sort
```

Expected:
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/src/...`
- `frontend/tests/e2e/...`

### Task 3: 迁移基础设施文件到 infra

**Files:**
- Move: `Dockerfile -> infra/frontend.Dockerfile`
- Move: `backend/Dockerfile -> infra/backend.Dockerfile`
- Move: `probes/Dockerfile -> infra/probe.Dockerfile`
- Move: `docker-compose.yml -> infra/docker-compose.yml`
- Move: `nginx.conf -> infra/nginx.conf`
- Move: `deploy/local/docker-compose.yml -> infra/local/docker-compose.yml`
- Move: `deploy/docker/probe-config.yaml -> infra/probe/probe-config.yaml`
- Move: `deploy/docker/init-timescale.sql -> infra/timescale/init-timescale.sql`

**Step 1: 搬迁文件**

使用 `mv` 完成迁移。

**Step 2: 删除空的 `deploy/`**

Run:

```bash
find deploy -type d -empty -delete
```

### Task 4: 修正 Docker 与基础设施引用

**Files:**
- Modify: `infra/frontend.Dockerfile`
- Modify: `infra/docker-compose.yml`
- Modify: `infra/local/docker-compose.yml`

**Step 1: 修正 frontend Dockerfile**

需要让它基于 `frontend/` 作为 build context 工作，并从 `infra/nginx.conf` 读取 Nginx 配置。

**Step 2: 修正 compose 文件**

需要统一为：
- frontend context: `../frontend`
- backend context: `../backend`
- probes context: `../probes`
- Dockerfile 指向 `../infra/*.Dockerfile`
- 本地挂载路径改成 `./probe/...` 与 `./timescale/...`

**Step 3: 验证 compose 文件语义**

Run:

```bash
sed -n '1,260p' infra/docker-compose.yml
```

### Task 5: 修正 README 与文档路径

**Files:**
- Modify: `README.md`

**Step 1: 把前端命令路径改为 `frontend/`**

包括：
- `pnpm install`
- `pnpm dev`
- `pnpm lint`
- `pnpm test:unit`
- `pnpm build`

**Step 2: 把 Docker / compose / nginx 路径改为 `infra/`**

包括：
- `infra/docker-compose.yml`
- `infra/local/docker-compose.yml`
- `infra/frontend.Dockerfile`
- `infra/nginx.conf`

### Task 6: 运行前端验证

**Files:**
- Verify: `frontend/`

**Step 1: 运行 lint**

Run:

```bash
cd frontend && pnpm lint
```

**Step 2: 运行单测**

Run:

```bash
cd frontend && pnpm test:unit
```

**Step 3: 运行构建**

Run:

```bash
cd frontend && pnpm build
```

Expected:
- 全部通过

### Task 7: 运行后端回归验证

**Files:**
- Verify: `backend/`

**Step 1: 运行后端全量测试**

Run:

```bash
cd backend && DJANGO_DATABASE_MODULE=core.settings.database_sqlite USE_TIMESCALE=0 ../.venv/bin/python -m pytest
```

Expected:
- `158 passed`

### Task 8: 提交并同步远端

**Files:**
- Commit: 全部变更

**Step 1: 检查 git 状态**

Run:

```bash
git status --short
```

**Step 2: 提交**

```bash
git add -A
git commit -m "refactor: reorganize root layout into frontend and infra"
```

**Step 3: 推送**

```bash
git push origin main
```
