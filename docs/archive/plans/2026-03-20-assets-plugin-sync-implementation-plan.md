# Assets Plugin-Based Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Introduce a plugin-based asset synchronization flow where admins can define asset models (fields + unique key), upload a Python sync script per model, and trigger sync to populate `AssetRecord` without any extra runtime config.

**Architecture:** Each asset model is stored as configuration (key, label, fields, unique_key, bound script id). A script implements a simple `run(context)` interface and hardcodes any external connection details. The sync service loads the model, dynamically imports the script, calls `run(context)`, and upserts `AssetRecord` rows according to the model's unique key definition.

**Tech Stack:** Django (backend, REST API), MySQL (persistence), Vue 3 + Vite (frontend), existing OneAll settings + asset center infrastructure.

## 2026-03-31 Progress Status

### 已完成

- 资产中心已形成“内置模型 + 扩展模型”的主结构，模型管理、字段管理、唯一键配置、脚本上传/下载、模型同步、同步历史均已落地。
- 资产模型同步现在会创建 `AssetSyncRun`，并将模型同步结果写入历史记录，前端同步历史能够区分模型同步和普通同步。
- 字段管理页已从演示态打通为真实保存：
  - 唯一键仅允许选择当前资产类型的真实字段；
  - 管理字段可保存并回显；
  - 管理字段不允许与内置字段重名。
- 扩展模型模板脚本已改为“安全骨架”：
  - 不再生成 `demo-1` 这类假数据；
  - 未配置真实数据源时会明确报错；
  - 避免将模板数据写入正式资产库。

### 当前封板口径

- 资产线已经进入“主线完成、待接入扩展源”的阶段。
- `ali-account` 当前定义为“已建模、待接入真实数据源”的扩展模型，不再视为资产线主计划阻塞项。
- 资产线当前封板标准是：
  - 主骨架完成；
  - 管理能力完成；
  - 扩展模型机制完成；
  - 未接入真实源的模型具有明确且安全的失败提示。

### 延期到下一阶段

- 扩展模型逐个接入真实数据源（按模型推进，不阻塞当前资产线封板）。
- 资产关系建模。
- 更复杂的生命周期能力。
- 更高级的脚本在线查看/编辑体验。

### 环境说明

- 资产中心主链路依赖远端默认业务库（MySQL），该链路已验证通过。
- 当前 `timescale` 连接仍不稳定，但它不属于资产线封板阻塞项，应作为独立环境问题处理。

---

### Task 1: Map current asset model and sync paths

**Files:**
- Inspect: `backend/src/apps/assets/models.py`
- Inspect: `backend/src/apps/assets/api/asset_type_view.py`
- Inspect: `backend/src/apps/assets/api/asset_view.py`
- Inspect: `backend/src/apps/settings/api/system_settings_view.py` (or equivalent)
- Inspect: `backend/src/integrations/assets_sync/`
- Inspect: `frontend/src/pages/assets/AssetCenter.vue`
- Inspect: `frontend/src/pages/settings/SystemSettings.vue`

**Step 1: Identify current AssetRecord + asset type definition structures**

Goal: Understand how asset types, fields and unique keys are currently represented in code and in SystemSettings.

**Step 2: Identify existing asset sync implementation**

Goal: Locate any existing sync services (e.g. `integrations/assets_sync`) and how they are triggered by APIs.

**Step 3: Identify existing system settings schema for assets**

Goal: Confirm where asset-related configuration currently lives (SystemSettings fields, serializers, APIs).

**Step 4: Summarize findings in comments at the top of this plan file (local notes only, no code changes)**

No code to run for this task.

**Step 5: Commit (optional, only if notes were added in other files)**

If you edited any tracers or left TODOs:

```bash
cd OneAll
git add .
git commit -m "chore: document current asset model and sync paths"
```

---

### Task 2: Define backend data model for asset models and script binding

**Files:**
- Modify: `backend/src/apps/assets/models.py`
- Modify: `backend/src/apps/assets/admin.py` (if exists and is used)
- Modify: `backend/src/apps/assets/migrations/` (new migration)
- Test: `backend/src/apps/assets/tests/` (add/extend model tests)

**Step 1: Add AssetModel (or similar) Django model**

Add a model to represent asset model configuration, for example:

```python
class AssetModel(models.Model):
    key = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=128)
    category = models.CharField(max_length=64, blank=True)  # e.g. cmdb, monitoring, workorder
    fields = models.JSONField(default=dict)  # list of field definitions
    unique_key = models.JSONField(default=list)  # list of field keys forming business uniqueness
    script_id = models.CharField(max_length=128, blank=True)  # identifier/path for uploaded script

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "assets_asset_model"
```

Adjust names and db_table to match project conventions.

**Step 2: Generate and inspect migration**

Run:

```bash
cd OneAll/backend
python manage.py makemigrations assets
python manage.py showmigrations assets
```

Verify the new table is created as expected.

**Step 3: Register AssetModel in admin (optional but helpful)**

In `admin.py`, register the new model for easier inspection.

**Step 4: Add basic model tests**

Create or extend a test module, e.g. `backend/src/apps/assets/tests/test_models.py`, to assert:

```python
def test_create_asset_model(db):
    m = AssetModel.objects.create(
        key="aliyun-account",
        label="阿里云账号",
        category="cmdb",
        fields=[{"key": "account_id", "label": "账号ID", "type": "string"}],
        unique_key=["account_id"],
    )
    assert m.key == "aliyun-account"
```

**Step 5: Run tests**

```bash
cd OneAll/backend
pytest apps/assets/tests/test_models.py -q
```

**Step 6: Commit**

```bash
cd OneAll
git add backend/src/apps/assets/models.py backend/src/apps/assets/migrations backend/src/apps/assets/tests
git commit -m "feat(assets): add AssetModel for configurable asset types"
```

---

### Task 3: Implement script storage and dynamic loading helper

**Files:**
- Create: `backend/src/apps/assets/services/script_loader.py`
- Modify: `backend/src/apps/assets/models.py` (helper method optional)
- Test: `backend/src/apps/assets/tests/test_script_loader.py`

**Step 1: Decide script storage location and interface**

Implement a simple convention where scripts are stored under a known directory, e.g. `backend/src/apps/assets/scripts/` with filenames derived from `AssetModel.script_id`.

**Step 2: Implement dynamic script loader**

In `script_loader.py`, implement something like:

```python
import importlib.util
import pathlib

SCRIPTS_ROOT = pathlib.Path(__file__).resolve().parent / "scripts"

def load_sync_script(script_id: str):
    if not script_id:
        raise ValueError("script_id is required")
    script_path = SCRIPTS_ROOT / f"{script_id}.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    spec = importlib.util.spec_from_file_location(script_id, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    if not hasattr(module, "run"):
        raise AttributeError(f"Script {script_id} missing required run(context) function")
    return module.run
```

**Step 3: Add simple unit tests**

Create a dummy script file in a test-only scripts directory or write a temporary file in the test, then assert:

```python
def test_load_sync_script(tmp_path, monkeypatch):
    # arrange: write a dummy script with a run(context) function
    ...
    run = load_sync_script("dummy")
    result = run({"asset_type": "test"})
    assert isinstance(result, list)
```

**Step 4: Run tests**

```bash
cd OneAll/backend
pytest apps/assets/tests/test_script_loader.py -q
```

**Step 5: Commit**

```bash
cd OneAll
git add backend/src/apps/assets/services/script_loader.py backend/src/apps/assets/tests/test_script_loader.py
git commit -m "feat(assets): add dynamic sync script loader"
```

---

### Task 4: Extend backend API to manage AssetModel (models + script binding)

**Files:**
- Create: `backend/src/apps/assets/api/asset_model_view.py`
- Modify: `backend/src/apps/assets/api/__init__.py` or urls
- Modify: `backend/src/core/urls.py` (if needed to expose new endpoints)
- Test: `backend/src/apps/assets/tests/test_asset_model_api.py`

**Step 1: Implement serializer for AssetModel**

Create DRF serializer:

```python
class AssetModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetModel
        fields = [
            "id",
            "key",
            "label",
            "category",
            "fields",
            "unique_key",
            "script_id",
        ]
        read_only_fields = ["id"]
```

**Step 2: Implement CRUD API for asset models**

Add a viewset or class-based views to allow:
- List models
- Create model (key, label, fields, unique_key)
- Update model (especially fields and unique_key)
- Bind/unbind script_id (the actual script upload handled separately)

Use DRF generics or ViewSet according to project style.

**Step 3: Wire URLs**

Expose endpoints under `/api/assets/models/` via app urls and core urls.

**Step 4: Add basic API tests**

Tests should cover:
- Creating a model
- Listing models
- Updating fields and unique_key
- Validation (e.g. key uniqueness)

**Step 5: Run tests**

```bash
cd OneAll/backend
pytest apps/assets/tests/test_asset_model_api.py -q
```

**Step 6: Commit**

```bash
cd OneAll
git add backend/src/apps/assets/api backend/src/core/urls.py backend/src/apps/assets/tests/test_asset_model_api.py
git commit -m "feat(assets): add AssetModel CRUD API"
```

---

### Task 5: Implement script upload/replace API for asset models

**Files:**
- Modify: `backend/src/apps/assets/api/asset_model_view.py` (or new view)
- Modify: `backend/src/apps/assets/services/script_loader.py` (add save helpers)
- Test: `backend/src/apps/assets/tests/test_asset_model_script_upload.py`

**Step 1: Add service functions for saving scripts**

In `script_loader.py`, add helpers:

```python
def save_sync_script(script_id: str, file_obj) -> pathlib.Path:
    # write uploaded file to SCRIPTS_ROOT / f"{script_id}.py"
    ...
```

**Step 2: Add API endpoint for uploading/replacing scripts**

Endpoint example: `POST /api/assets/models/{id}/script/`
- Accept multipart file upload with one `.py` file
- Derive `script_id` from AssetModel.key or a generated identifier
- Save file via `save_sync_script`
- Update `AssetModel.script_id`

**Step 3: Validate uploaded script**

After saving, attempt `load_sync_script(script_id)` to ensure:
- File is importable
- Contains a `run(context)` function

If validation fails, delete the file and return 400 with a readable error message.

**Step 4: Add tests**

Cover:
- Successful upload and binding of a valid script
- Upload of invalid script (missing run) -> 400 and file cleanup

**Step 5: Run tests**

```bash
cd OneAll/backend
pytest apps/assets/tests/test_asset_model_script_upload.py -q
```

**Step 6: Commit**

```bash
cd OneAll
git add backend/src/apps/assets/api backend/src/apps/assets/services/script_loader.py backend/src/apps/assets/tests
git commit -m "feat(assets): support uploading sync scripts for asset models"
```

---

### Task 6: Hook sync execution to AssetModel + scripts

**Files:**
- Modify: `backend/src/apps/assets/services/sync_service.py` (or create)
- Modify: `backend/src/apps/assets/api/asset_view.py` or a dedicated sync API
- Test: `backend/src/apps/assets/tests/test_asset_sync_with_script.py`

**Step 1: Implement service function to run sync for one AssetModel**

Pseudo-code:

```python
def sync_asset_model(model: AssetModel, *, logger=None) -> dict:
    if not model.script_id:
        raise ValueError("AssetModel has no script bound")
    run = load_sync_script(model.script_id)
    context = {
        "asset_type": model.key,
        # optionally add last_sync_at, logger, etc.
    }
    assets = run(context) or []
    # upsert into AssetRecord using model.unique_key
    ...
    return {
        "total": len(assets),
        "created": created_count,
        "updated": updated_count,
    }
```

**Step 2: Extend sync API to trigger by model key**

Add or modify endpoint, e.g. `POST /api/assets/models/{key}/sync/`:
- Look up AssetModel by key
- Call `sync_asset_model`
- Return summary + error info if any

**Step 3: Ensure AssetRecord uniqueness logic uses model.unique_key**

If not already present, implement a helper to build a business key from `unique_key` fields and the record metadata, and use it to upsert.

**Step 4: Add tests**

Test a flow end-to-end with:
- One AssetModel
- Bound dummy script that returns a couple of assets
- Hitting the sync endpoint and asserting AssetRecord rows created/updated correctly

**Step 5: Run tests**

```bash
cd OneAll/backend
pytest apps/assets/tests/test_asset_sync_with_script.py -q
```

**Step 6: Commit**

```bash
cd OneAll
git add backend/src/apps/assets/services backend/src/apps/assets/api backend/src/apps/assets/tests
git commit -m "feat(assets): sync asset models via uploaded scripts"
```

---

### Task 7: Expose AssetModel and sync actions to frontend (settings)

**Files:**
- Modify: `frontend/src/pages/settings/SystemSettings.vue`
- Modify: `frontend/src/pages/settings/components/SettingsTabs.vue` (or dedicated asset settings component)
- Modify: `frontend/src/services/settingsApi.ts` (or add new api)
- Test: `frontend` unit tests if present

**Step 1: Add API client functions for AssetModel CRUD and script upload**

In `settingsApi.ts` (or a new `assetsSettingsApi.ts`), add functions:
- `listAssetModels()`
- `createAssetModel(payload)`
- `updateAssetModel(id, payload)`
- `uploadAssetModelScript(id, file)`

**Step 2: Add UI section “资产模型管理”**

In SystemSettings, add a new panel:
- Show table of existing asset models (key, name, category, has_script flag)
- Actions: create, edit, upload/replace script

**Step 3: Implement “新增模型”对话框**

Fields:
- 模型 key
- 名称
- 分类
- 字段列表编辑（字段 key、名称、类型、是否必填）
- 唯一键字段多选

Save via create API.

**Step 4: Implement编辑模型**

Allow updating label, category, fields, unique_key. Bind to update API.

**Step 5: Implement脚本上传/替换**

Add “上传同步脚本”按钮:
- 打开文件选择器，选择 `.py`
- 调用 upload API
- 根据后端返回的错误信息展示“脚本校验失败”提示

**Step 6: Manual frontend check**

Run:

```bash
cd OneAll/frontend
npm run dev
```

Open settings page, verify:
- 模型列表展示正常
- 新建/编辑模型成功
- 脚本上传能收到后端成功/失败反馈

**Step 7: Commit**

```bash
cd OneAll
git add frontend/src/pages/settings frontend/src/services
git commit -m "feat(frontend): asset model management and script upload UI"
```

---

### Task 8: Integrate AssetModel into AssetCenter views (列表 + 详情 + 同步按钮)

**Files:**
- Modify: `frontend/src/pages/assets/AssetCenter.vue`
- Modify: `frontend/src/services/assetsApi.ts`

**Step 1: Add API for “按模型 key 列表资产 + 同步”**

In `assetsApi.ts`, add:
- `listAssetsByModel(modelKey, params)`
- `syncAssetModel(modelKey)`

**Step 2: Adapt AssetCenter to be model-driven**

For at least one path (e.g. cmdb 域名视图), wire it to:
- Use AssetModel metadata for columns (fields)
- Use new sync endpoint for “同步资产”按钮

**Step 3: Ensure详情弹窗字段来自模型字段**

Use AssetModel.fields to render all model fields for a record using its metadata.

**Step 4: Manual end-to-end check**

Flow:
- 新建一个简单模型（例如自定义测试模型）
- 上传一个返回 1-2 条假数据的脚本
- 在 AssetCenter 对应入口看到列表
- 点“同步资产”，看到列表中出现脚本返回的数据

**Step 5: Commit**

```bash
cd OneAll
git add frontend/src/pages/assets/AssetCenter.vue frontend/src/services/assetsApi.ts
git commit -m "feat(assets): drive AssetCenter from AssetModel and sync scripts"
```

---

### Task 9: Error handling, logging, and UX polish

**Files:**
- Modify: backend sync service + APIs
- Modify: frontend AssetCenter and settings UIs
- Test: extend existing tests

**Step 1: Standardize backend error messages**

Ensure sync errors (script not found, import error, runtime exception) return:
- 4xx/5xx with a clear, non-technical message suitable for UI
- log full stack trace on server side

**Step 2: Improve frontend error handling**

In settings and AssetCenter:
- Show用户可读错误提示（例如“同步脚本执行失败，请联系管理员查看日志”）
- 保留原有列表状态，避免整页崩溃

**Step 3: Add minimal documentation**

Update or create a short markdown note under `docs/` describing:
- 如何新增资产模型
- 如何编写并上传同步脚本（run(context) 接口）
- 如何触发同步和查看结果

**Step 4: Run full test suite (backend + relevant frontend checks)**

```bash
cd OneAll/backend
pytest -q

cd ../frontend
npm test  # if tests exist
```

**Step 5: Final commit**

```bash
cd OneAll
git add .
git commit -m "feat(assets): plugin-based asset sync with model-defined schemas"
```
