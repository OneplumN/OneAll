# Monitoring Alerts Aggregation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire monitoring task/probe execution results into the new alerts domain using a simple 3-minute / 2-failures aggregation rule and window-level de-duplication.

**Architecture:** After each monitoring task/probe run, reuse existing monitoring history data to compute failures within a rolling 3-minute window per task. When failures >= 2 and no recent alert exists for the same task, construct a `CheckResult` and call `evaluate_and_raise` from `apps.alerts.services`, optionally enqueueing `dispatch_alert_event` for async handling.

**Tech Stack:** Django, Django ORM, Celery, existing `apps.monitoring` services, `apps.alerts` models/services.

---

### Task 1: Identify Monitoring Execution Flow and Failure Semantics

**Files:**
- Inspect: `backend/src/apps/monitoring/services/detection_service.py`
- Inspect: `backend/src/apps/monitoring/services/monitoring_job_service.py`
- Inspect: `backend/src/apps/monitoring/services/job_runner_service.py`
- Inspect: `backend/src/apps/monitoring/services/monitoring_history_service.py`

**Step 1: Locate the primary entry point where monitoring tasks/probes are executed and results are persisted.**

**Step 2: Identify how success/failure is represented (status enums/fields) in monitoring history or task models.**

**Step 3: Note which identifiers (task ID, asset ID, probe ID) are available at that point for use in alerts.**

**Step 4: Decide the exact function(s) where aggregation logic will be hooked after result persistence.**

---

### Task 2: Implement 3-Minute / 2-Failures Aggregation Helper

**Files:**
- Modify: `backend/src/apps/monitoring/services/monitoring_history_service.py`
- Modify: or another clearly central service file identified in Task 1

**Step 1: Add a helper function `evaluate_aggregated_failures(task_id, context)` (exact name TBD) that:**

```python
from datetime import timedelta
from django.utils import timezone

from apps.alerts.services import CheckResult, evaluate_and_raise
from apps.alerts.models import AlertEvent
```

**Step 2: Inside the helper, compute the window start as `timezone.now() - timedelta(minutes=3)` and query monitoring history for the given task ID, filtering by `created_at >= window_start` and failure status.**

**Step 3: If failure count `< 2`, return early without doing anything.**

**Step 4: Query `AlertEvent` for existing events in the same window with `source="monitoring"` and matching `related_task_id`; if one exists, return early to avoid duplicate alerts.**

**Step 5: Build a `CheckResult` instance with fields:**

```python
result = CheckResult(
    source="monitoring",
    event_type="monitoring_check_failed_aggregated",
    severity="critical",
    title="监控任务连续失败告警",
    message=f"任务 {task_name} 在过去 3 分钟内失败了 {failure_count} 次（最近一次失败时间：{last_failure_at}）",
    status="failed",
    task_id=str(task_id),
    asset_id=str(asset_id) if asset_id else None,
    probe_id=str(probe_id) if probe_id else None,
    context={
        "window_minutes": 3,
        "failure_threshold": 2,
        "failure_count": failure_count,
        "last_failure_reason": last_failure_reason,
        "last_failure_at": last_failure_at.isoformat() if last_failure_at else None,
        "target": target,
    },
)
```

**Step 6: Call `evaluate_and_raise(result)` to create the `AlertEvent`, and return the created event (or `None` if suppressed).**

---

### Task 3: Hook Aggregation Helper into Monitoring Execution Flow

**Files:**
- Modify: `backend/src/apps/monitoring/services/detection_service.py`
- Modify: or `backend/src/apps/monitoring/services/monitoring_job_service.py` / other main execution service

**Step 1: In the function that executes a monitoring task/probe and persists its result, after saving the history record, import and invoke the aggregation helper with the appropriate identifiers and context (task ID, asset ID, probe ID, target, failure reason, etc.).**

**Step 2: Ensure the helper is only called when the current run has failed (so we don't waste work on successful runs).**

**Step 3: Optionally, if a non-`None` event is returned, enqueue the Celery task `dispatch_alert_event.delay(str(event.id))` to simulate async delivery ready for future channel integrations.**

**Step 4: Keep the existing monitoring behavior unchanged (status updates, history writes); the new logic should be additive and not modify prior flows.**

---

### Task 4: Add Basic Tests for Aggregated Alerts

**Files:**
- Create: `backend/tests/apps/alerts/test_monitoring_integration.py`

**Step 1: Write a test that creates a monitoring task and two failed history records within 3 minutes for the same task, then calls the aggregation helper and asserts that an `AlertEvent` is created with expected fields (source, event_type, severity, related_task_id, context).**

**Step 2: Write a test that simulates only one failure in the last 3 minutes and asserts that no new `AlertEvent` is created.**

**Step 3: Write a test that simulates an existing `AlertEvent` in the last 3 minutes for the same task and asserts that a subsequent call with additional failures does not create a duplicate alert.**

**Step 4: Run the relevant tests via:**

```bash
cd backend
pytest tests/apps/alerts/test_monitoring_integration.py -v
```

**Step 5: Ensure tests pass, adjusting queries or model imports as needed for the real monitoring history model names and fields.**

---

### Task 5: Smoke Test and Minimal Docs Update

**Files:**
- Modify: `docs/plans/2026-03-18-oneall-v2-domain-refactor-design.md` (optional note)
- Modify: `docs/plans/2026-03-18-oneall-v2-implementation-plan.md` (optional cross-reference)

**Step 1: Run basic Django checks and (if feasible) a local run of the monitoring task execution path to ensure no regressions in normal flows:**

```bash
cd backend
python3 manage.py check
```

**Step 2: Add a short note in the existing v2 design/implementation docs pointing to the new monitoring alerts aggregation design and plan documents.**

**Step 3: Summarize the behavior change: “监控任务在 3 分钟窗口内连续失败 2 次将触发一条告警事件，窗口内去重，统一通过 alerts 模块管理。”**

**Step 4: If everything looks good, stage changes and prepare for review/commit as per your normal workflow.**

