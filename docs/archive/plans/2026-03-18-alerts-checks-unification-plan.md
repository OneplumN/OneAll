# Alerts Check/Schedule Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Introduce a unified "alert handling" center under the alerts domain that owns check definitions, schedules, and executions for both monitoring and probes, while preserving existing monitoring/probes UIs and gradually migrating scheduling control into alerts.

**Architecture:** Define new alerts-side models (`AlertCheck`, `AlertSchedule`, `AlertCheckExecution`) that map to existing `MonitoringRequest`/`MonitoringJob`/`DetectionTask` and `ProbeSchedule`/`ProbeScheduleExecution`. Centralize scheduling so only `AlertSchedule` is driven by the scheduler; monitoring/probes become execution backends. Keep old models/APIs as facades that synchronize into the new alerts models to avoid breaking callers.

**Tech Stack:** Django (apps `alerts`, `monitoring`, `probes`), Celery for scheduling, existing monitoring/probes services, PostgreSQL/MySQL via Django ORM.

---

### Task 1: Introduce alerts-side models for checks, schedules, executions

**Files:**
- Modify: `backend/src/apps/alerts/models.py`
- Modify: `backend/src/apps/alerts/apps.py` (if needed to register new submodule)
- Create: `backend/src/apps/alerts/migrations/00xx_alert_checks_schedule_execution.py`
- Test: `backend/tests/unit/test_alert_checks_models.py` (new)

**Step 1:** Add three new models under the alerts app:
- `AlertCheck` with fields: `name`, `target`, `protocol`, `source_type`, `source_id`, `executor_type`, `executor_config`, `asset_id` (nullable).
- `AlertSchedule` with fields: FK to `AlertCheck`, `cron_expression`, `frequency_minutes`, `status`, `start_at`, `end_at`, `last_run_at`, `next_run_at`, `metadata`.
- `AlertCheckExecution` with fields: FK to `AlertSchedule`, `executor_type`, `executor_ref`, `scheduled_at`, `started_at`, `finished_at`, `status`, `response_time_ms`, `status_code`, `error_message`, `result_payload`, `source_type`, `source_id`.

**Step 2:** Generate and inspect a Django migration for the alerts app to create these tables.

Run: `cd backend && python3 manage.py makemigrations alerts`

**Step 3:** Add basic model tests to ensure default values, choices, and simple `__str__` implementations work, and that relationships are wired correctly.

Run: `cd backend && python3 -m pytest backend/tests/unit/test_alert_checks_models.py -q`

---

### Task 2: Map existing monitoring and probes objects into AlertCheck/AlertSchedule

**Files:**
- Modify: `backend/src/apps/monitoring/models/monitoring_request.py`
- Modify: `backend/src/apps/monitoring/models/monitoring_job.py`
- Modify: `backend/src/apps/probes/models/probe_schedule.py`
- Create: `backend/src/apps/alerts/services/check_mapping_service.py`
- Test: `backend/tests/unit/test_alert_checks_mapping.py` (new)

**Step 1:** Implement a mapping service in alerts (e.g. `ensure_check_for_monitoring_request` and `ensure_check_for_probe_schedule`) that:
- Given a `MonitoringRequest`, finds or creates a corresponding `AlertCheck`.
- Given a `ProbeSchedule`, finds or creates a corresponding `AlertCheck`.

**Step 2:** Implement a mapping for schedules:
- For a `MonitoringJob`, create/update an `AlertSchedule` referencing the appropriate `AlertCheck`.
- For a `ProbeSchedule`, create/update an `AlertSchedule` with equivalent frequency/start/end/status.

**Step 3:** Wire model signals or explicit save hooks so that when MonitoringRequest/MonitoringJob/ProbeSchedule are created or updated, the corresponding `AlertCheck`/`AlertSchedule` are synchronized but existing behavior of those models is otherwise unchanged.

**Step 4:** Add tests that creating/updating monitoring requests/jobs and probe schedules produces expected `AlertCheck`/`AlertSchedule` rows and maintains 1:1 or 1:many relationships as intended.

Run: `cd backend && python3 -m pytest backend/tests/unit/test_alert_checks_mapping.py -q`

---

### Task 3: Introduce unified execution records (AlertCheckExecution) alongside existing ones

**Files:**
- Modify: `backend/src/apps/monitoring/services/detection_service.py`
- Modify: `backend/src/apps/probes/services/schedule_execution_service.py`
- Modify/Create: `backend/src/apps/alerts/services/check_execution_service.py`
- Test: `backend/tests/unit/test_alert_checks_execution.py` (new)

**Step 1:** Implement alerts-side helpers to record a `AlertCheckExecution` from:
- A `DetectionTask` (monitoring) instance.
- A `ProbeScheduleExecution` (probes) instance.

**Step 2:** In monitoring detection service and probes schedule execution service, after they persist their own execution record, call into alert check execution helpers to mirror the execution into `AlertCheckExecution` (with `source_type/source_id` filled appropriately). Do not change existing behavior yet; this is additive.

**Step 3:** Add unit tests that simulate monitoring detections and probe schedule executions and assert that corresponding `AlertCheckExecution` rows are created and correctly linked to `AlertSchedule`/`AlertCheck`.

Run: `cd backend && python3 -m pytest backend/tests/unit/test_alert_checks_execution.py -q`

---

### Task 4: Centralize scheduling on AlertSchedule (phase 1: additive, no behavior change)

**Files:**
- Create/Modify: `backend/src/apps/alerts/tasks.py` (new Celery tasks for scheduling)
- Modify: any existing Celery beat configurations or cron jobs that trigger monitoring/probes scheduling
- Modify: `backend/src/apps/monitoring/services/*` and `backend/src/apps/probes/services/*` that currently compute `next_run_at`
- Test: `backend/tests/integration/test_alerts_central_scheduler.py` (new)

**Step 1:** Implement an alerts-side scheduler task that:
- Periodically scans `AlertSchedule` for due schedules (`next_run_at <= now`, `status=active`).
- For each, enqueues a per-schedule task (e.g. `run_alert_check(schedule_id)` under alerts).

**Step 2:** Implement `run_alert_check(schedule_id)` to:
- Resolve the `AlertCheck` and its `source_type` / `source_id` / `executor_type`.
- Delegate execution to monitoring/probes execution services, which will create the underlying `DetectionTask`/`ProbeScheduleExecution` and then an `AlertCheckExecution`.

**Step 3:** Keep existing monitoring/probes-specific scheduling logic in place but mark it as deprecated in comments. For this phase, both the legacy scheduling and the new alerts scheduling may fire, so guard with a feature flag or config to avoid double execution (e.g. an env var `ALERTS_CENTRAL_SCHEDULER_ENABLED` defaulting to false).

**Step 4:** Add integration-style tests (using a fake bean/clock if possible) that, when the central scheduler flag is enabled, a due `AlertSchedule` produces a `AlertCheckExecution` and then an `AlertEvent`.

Run: `cd backend && python3 -m pytest backend/tests/integration/test_alerts_central_scheduler.py -q`

---

### Task 5: Switch primary scheduling control to alerts (phase 2: behavior change with feature flag)

**Files:**
- Modify: configuration (settings/env) to enable central scheduler in non-dev environments when ready
- Modify: legacy monitoring/probes schedulers to no-op when `ALERTS_CENTRAL_SCHEDULER_ENABLED` is true
- Test: reuse/extend `test_alerts_central_scheduler` to assert that with the flag on, only the alerts scheduler path produces executions

**Step 1:** Introduce a setting/env flag `ALERTS_CENTRAL_SCHEDULER_ENABLED` and wire it into both alerts scheduler and monitoring/probes legacy schedulers:
- When false (default for safety), legacy behavior remains primary.
- When true, alerts scheduler becomes primary and legacy schedulers skip creating new jobs.

**Step 2:** Update documentation (comments and possibly docs) to explain the switch and how to roll back by toggling the flag.

**Step 3:** In tests, exercise both modes to ensure no regressions in execution and AlertEvent generation.

---

## 2026-03-19 Implementation Progress Log

> 本节用于记录本轮实际落地进度与关键决策，便于后续回顾与继续迭代。

### 1. 已完成的后端实现

1. Alert 执行记录与监控/探针打通
   - 在 `apps.monitoring.services.detection_service._record_alert_check_execution_for_detection` 中，修正了 `DetectionTask` → `AlertCheckExecution` 的关联方式：
     - 现在通过 `metadata["request_id"]`（MonitoringRequest.id）查找 `AlertSchedule(alert_check__source_id=request_id)`。
     - 原先通过 `job_id` 关联会找不到对应的 `AlertSchedule`，已修复。
   - 探针侧 `apps.probes.services.schedule_execution_service.record_result` 保持不变，仍然将 `ProbeScheduleExecution` 镜像到 `AlertCheckExecution`，形成统一的执行历史。

2. Alerts 中央调度真正“接管执行”
   - 在 `apps.alerts.tasks` 中完成了中央调度的实际执行逻辑：
     - 继续使用 `run_due_alert_schedules` 扫描 `AlertSchedule(status=ACTIVE, next_run_at<=now)`，为每个 due 调度下发 `run_alert_check(schedule_id)`。
     - 新的 `run_alert_check` 在 `ALERTS_CENTRAL_SCHEDULER_ENABLED=True` 时执行以下行为：
       - 监控链路（AlertCheck.source_type = `monitoring_request`）：
         - 通过 `AlertCheck.source_id = MonitoringRequest.id` 查找所有 `MonitoringJob(status=ACTIVE)`。
         - 复用旧逻辑 `apps.monitoring.services.job_runner_service._enqueue_single_job(job, now)` 创建 `DetectionTask`，并推进 `job.next_run_at`。
         - 通过 `apps.alerts.services.ensure_schedule_for_monitoring_job(job)` 将 `job.last_run_at/next_run_at` 同步回对应的 `AlertSchedule`。
       - 探针手工调度链路（AlertCheck.source_type = `probe_schedule`）：
         - 加载 `ProbeSchedule`，仅当 `source_type=MANUAL` 时接管（避免和 MonitoringRequest 派生的 ProbeSchedule 重复调度）。
         - 复用旧逻辑 `apps.probes.services.manual_schedule_runner._enqueue_schedule(schedule=probe_schedule, now=now)` 创建 `DetectionTask` 并更新 `probe_schedule.next_run_at`。
         - 通过 `apps.alerts.services.ensure_schedule_for_probe_schedule(probe_schedule)` 将 `ProbeSchedule.next_run_at` 同步回 `AlertSchedule`。
   - 结果：当 `ALERTS_CENTRAL_SCHEDULER_ENABLED=True` 时，周期性 `DetectionTask` 的创建由 alerts 侧 `AlertSchedule` 驱动，原有 `enqueue_due_jobs` / `run_due_manual_schedules` 在 flag 打开时会直接返回 `0, 0`，不再负责执行调度。

3. 手工 ProbeSchedule 与 AlertSchedule 的闭环
   - 在 `apps.probes.api.serializers.ProbeScheduleSerializer` 中：
     - `create`：
       - 手工创建 `ProbeSchedule` 后，立即调用 `ensure_schedule_for_probe_schedule(schedule)`，为其生成对应的 `AlertCheck` + `AlertSchedule`。
       - 确保打开中央调度后，手工调度不会因为缺少 AlertSchedule 而“失联”。
     - `update`：
       - 当更新 `timeout_seconds`、`expected_status_codes`、`alert_threshold` 等字段时，会合并到 `schedule.metadata` 并 `save`。
       - 随后调用 `ensure_schedule_for_probe_schedule(schedule)`，将最新 metadata 同步到对应的 `AlertSchedule`，方便后续在告警域内统一使用这些配置。

4. Feature Flag 语义保持不变
   - `settings.ALERTS_CENTRAL_SCHEDULER_ENABLED` 仍然是行为开关：
     - False（默认）：沿用原有监控 / 手工探针调度逻辑，alerts 中央调度任务早退不做任何事情。
     - True：`run_due_alert_schedules` + `run_alert_check` 成为唯一的周期调度入口，监控/探针的 legacy runner 仅作为兼容存在但不再创建任务。

### 2. 当前已知限制与环境情况

- 当前开发环境中 `python` 命令不可用，无法在本机直接执行 `pytest` 验证所有变更。
  - 建议在有 Python 环境的机器上运行至少以下用例：
    - `backend/tests/unit/test_alert_checks_mapping.py`
    - `backend/tests/unit/test_job_runner_service.py`
    - `backend/tests/unit/test_manual_schedule_runner.py`
  - 后续可以增加针对 `apps.alerts.tasks.run_due_alert_schedules/run_alert_check` 的专门测试，验证 flag=true 时 DetectionTask / AlertCheckExecution 的实际产生行为。

### 3. 后续迭代建议（本轮会话结论）

1. 后端
   - 新增简单只读 API：
     - `GET /api/alerts/checks`：列出 `AlertCheck` + 关键信息（来源、目标、协议等）。
     - `GET /api/alerts/checks/{id}/schedules`：列出该检查下的 `AlertSchedule` 及最近一次 `AlertCheckExecution`。
   - 在测试环境开启 `ALERTS_CENTRAL_SCHEDULER_ENABLED=true`，观察：
     - DetectionTask 是否只由 alerts 调度产生；
     - AlertCheckExecution 是否完整覆盖监控 + 手工探针执行。

2. 前端
   - 在 alerts 模块下新增“告警检查 / 调度”页面，用于：
     - 查看各个检查的来源（监控/探针）、目标、协议。
     - 查看调度频率、状态、`next_run_at`。
     - 查看最近一次执行状态（成功/失败/超时等）。
   - 首阶段以只读为主，后续再考虑在该页面上支持“暂停 / 恢复调度”等操作。

3. 权限与域划分（相关决策记录）
   - 功能开关（集成模块中的“功能开放”）将逐步收敛到系统权限和告警域中，不再作为独立的模块开关。
   - 告警与探针保持为两个独立的域：
     - 探针域负责资源配置、任务执行（拨测、调度执行）。
     - 告警域负责告警事件聚合、调度、处理与展示，通过 `source + context` 关联到探针或监控任务。

### Task 6: Align AlertRule and probe/monitoring thresholds with AlertCheck

**Files:**
- Modify: `backend/src/apps/alerts/models.py` (AlertRule if necessary)
- Modify: `backend/src/apps/alerts/services.py` (to use rules when evaluating CheckResult)
- Modify: `backend/src/apps/probes/api/serializers.py` and `backend/src/apps/monitoring/api/*` where thresholds/contacts are set
- Test: `backend/tests/unit/test_alert_rules_for_checks.py` (new or extended)

**Step 1:** Decide minimal mapping for this phase:
- For probe schedules and monitoring requests, continue writing thresholds/contacts into their own metadata but also mirror the effective threshold/contacts into an `AlertRule` bound to the corresponding `AlertCheck`.

**Step 2:** Update `evaluate_and_raise` or a wrapper service to consult `AlertRule` when creating `AlertEvent` (at least using severity/channels if present), keeping current behavior as fallback.

**Step 3:** Add tests that changing thresholds/contacts in probe/monitoring configs results in corresponding `AlertRule` updates and that the alerts pipeline consumes these correctly.

---

### Task 7: UI exposure for alert checks/schedules (optional for first backend pass)

**Files:**
- Create: `frontend/src/pages/alerts/AlertChecks.vue`
- Modify: `frontend/src/router/index.ts` to add a menu entry under alerts
- Create: `frontend/src/services/alertChecksApi.ts`

**Step 1:** Add a simple read-only list page under alerts module to show:
- `AlertCheck` rows with source (monitoring/probes), target, protocol.
- Associated `AlertSchedule` info (frequency/status/next_run_at).

**Step 2:** Use this page as a debugging/visibility tool during rollout; in a later iteration, consider letting users edit schedules and thresholds from here instead of monitoring/probes modules.

**Step 3:** Manual smoke test in browser to ensure the new page loads and filters correctly once the backend APIs are implemented.

---

### Task 8: Documentation and cleanup

**Files:**
- Modify: `specs/001-build-oneall-platform/module-guide.md`
- Modify: any README or architecture docs that describe monitoring/probes scheduling

**Step 1:** Update module guide to reflect that: resource configuration (ProbeNode) is system-level; monitoring/probes execution are backends; all scheduling and alert generation are owned by alerts.

**Step 2:** Document the central scheduler flag and migration path so future changes can safely retire legacy schedulers and potentially merge execution tables if desired.
