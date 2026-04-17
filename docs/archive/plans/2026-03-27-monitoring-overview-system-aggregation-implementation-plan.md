# Monitoring Overview System Aggregation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve each monitoring strategy target to an asset-backed system name, then build a system-level honeycomb monitoring overview that aggregates latest probe/check status by system.

**Architecture:** Keep asset center as the only source of truth for domain-to-system ownership. Add derived resolution snapshot fields onto `AlertCheck`, compute them in backend service flows when checks are created or updated, expose a dedicated system overview API, and render a system honeycomb plus detail table in the existing monitoring overview frontend.

**Tech Stack:** Django, Django REST Framework, MySQL, existing alerts/probes execution models, Vue 3, TypeScript, Element Plus, existing `DetectionHoneycomb` component.

---

### Task 1: Record the Approved Design

**Files:**
- Create: `docs/plans/2026-03-27-monitoring-overview-system-aggregation-design.md`
- Create: `docs/plans/2026-03-27-monitoring-overview-system-aggregation-implementation-plan.md`

**Step 1: Save the approved source-of-truth decision.**

Write that asset center `cmdb-domain` records provide `system_name`, and monitoring strategies must not introduce a second hand-maintained system field.

**Step 2: Save the exact resolution statuses and fallback buckets.**

Document `matched`, `missing_system`, `unmanaged`, and `invalid_target`, plus the two display buckets `未配置系统` and `未纳管域名`.

**Step 3: Save the aggregation rule.**

Record that system status is red if any domain is abnormal, green if all latest results are healthy, and gray if no valid latest result exists.

---

### Task 2: Add Resolution Snapshot Fields to AlertCheck

**Files:**
- Modify: `backend/src/apps/alerts/models.py`
- Create: `backend/src/apps/alerts/migrations/000x_alertcheck_resolution_snapshot.py`
- Test: `backend/tests/unit/test_alert_check_target_resolution.py`

**Step 1: Write the failing model/service test.**

Add a unit test that creates an `AlertCheck`, runs the resolution flow, and asserts:

```python
assert check.resolved_domain == "pay.demo.oneall.com"
assert check.resolved_system_name == "支付平台"
assert check.asset_match_status == "matched"
assert check.asset_record_id is not None
```

**Step 2: Run the test to verify it fails.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_alert_check_target_resolution.py -v`

Expected: FAIL because `AlertCheck` does not yet contain resolution snapshot fields or service behavior.

**Step 3: Add the fields with conservative defaults.**

Add these fields to `AlertCheck`:

```python
resolved_domain = models.CharField(max_length=255, blank=True)
resolved_system_name = models.CharField(max_length=128, blank=True)
asset_record_id = models.UUIDField(null=True, blank=True)
asset_match_status = models.CharField(max_length=32, blank=True)
```

**Step 4: Create and inspect the migration.**

Run: `cd /mnt/d/workspace/OneAll/backend/src && python3 manage.py makemigrations alerts`

Expected: a migration file that adds the four columns without rewriting unrelated tables.

**Step 5: Run the test again after the model change.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_alert_check_target_resolution.py -v`

Expected: still FAIL because resolution logic is not yet implemented.

---

### Task 3: Implement Target Parsing and Asset Matching Service

**Files:**
- Create: `backend/src/apps/alerts/services/check_target_resolution_service.py`
- Modify: `backend/src/apps/alerts/services.py`
- Modify: `backend/src/apps/alerts/services/check_mapping_service.py`
- Test: `backend/tests/unit/test_alert_check_target_resolution.py`

**Step 1: Extend the failing test with all core cases.**

Add tests for:

- URL target resolves to matched asset
- bare domain target resolves to matched asset
- matched domain with empty `system_name` becomes `missing_system`
- unmatched domain becomes `unmanaged`
- IP / invalid target becomes `invalid_target`

**Step 2: Run the test file to verify all cases fail.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_alert_check_target_resolution.py -v`

Expected: FAIL with missing parser/resolution behavior.

**Step 3: Write the minimal parsing service.**

Implement:

- `normalize_target_to_domain(target: str) -> str | None`
- `resolve_check_target(target: str) -> ResolutionResult`
- `apply_resolution_snapshot(check: AlertCheck) -> AlertCheck`

Use `urllib.parse` for URL host extraction and normalize to lowercase host without port/path.

**Step 4: Wire the service into check creation/update flows.**

After `AlertCheck` is created or target is updated in:

- `ensure_check_for_monitoring_request`
- `ensure_check_for_probe_schedule`

call the resolution snapshot service before returning the check.

**Step 5: Run the test file and make it pass.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_alert_check_target_resolution.py -v`

Expected: PASS

---

### Task 4: Backfill Existing Checks

**Files:**
- Create: `backend/src/apps/alerts/management/commands/backfill_check_resolution.py`
- Test: `backend/tests/unit/test_alert_check_resolution_backfill_command.py`

**Step 1: Write the failing management command test.**

Create checks with empty resolution snapshot fields, run the command, and assert fields are filled from matching assets.

**Step 2: Run the command test to verify it fails.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_alert_check_resolution_backfill_command.py -v`

Expected: FAIL because the command does not exist.

**Step 3: Implement the backfill command.**

Create a command that iterates `AlertCheck` rows in batches and reapplies the resolution service.

**Step 4: Run the command test again.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_alert_check_resolution_backfill_command.py -v`

Expected: PASS

---

### Task 5: Build the System Overview Aggregation Service

**Files:**
- Create: `backend/src/apps/alerts/services/system_overview_service.py`
- Test: `backend/tests/unit/test_system_overview_service.py`

**Step 1: Write the failing aggregation tests.**

Cover:

- one system with all healthy latest results -> `success`
- one system with any failed latest result -> `danger`
- one system with no latest result -> `idle`
- `missing_system` rows aggregate into `未配置系统`
- `unmanaged` / `invalid_target` rows aggregate into `未纳管域名`

**Step 2: Run the service tests to verify failure.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_system_overview_service.py -v`

Expected: FAIL because the service does not exist.

**Step 3: Implement the minimal aggregation service.**

For each `AlertCheck`, fetch its latest `AlertCheckExecution` across schedules, derive a normalized status, group by resolved system bucket, and return:

- system summary rows
- domain/detail rows under each system

**Step 4: Run the service tests again.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_system_overview_service.py -v`

Expected: PASS

---

### Task 6: Expose the System Overview API

**Files:**
- Modify: `backend/src/apps/alerts/api/views.py`
- Modify: `backend/src/apps/alerts/api/urls.py`
- Test: `backend/tests/unit/test_alerts_system_overview_api.py`

**Step 1: Write the failing API test.**

Assert that:

```python
response = client.get("/api/alerts/checks/system-overview")
assert response.status_code == 200
assert "systems" in response.json()
assert "items" in response.json()
```

**Step 2: Run the API test to verify failure.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_alerts_system_overview_api.py -v`

Expected: FAIL because the route does not exist.

**Step 3: Add the read-only API view.**

Create an API view that returns:

- `systems`
- `items`
- optional generated timestamp

and protect it with the existing `alerts.module.access` permission.

**Step 4: Run the API test again.**

Run: `cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest backend/tests/unit/test_alerts_system_overview_api.py -v`

Expected: PASS

---

### Task 7: Add Frontend API Types and Data Loader

**Files:**
- Modify: `frontend/src/services/alertsApi.ts`
- Test: `frontend` build validation

**Step 1: Add typed contracts for the overview API.**

Define types for:

- `MonitoringOverviewSystem`
- `MonitoringOverviewItem`
- `MonitoringOverviewPayload`

**Step 2: Add the fetch function.**

Implement:

```ts
export async function fetchMonitoringOverview(): Promise<MonitoringOverviewPayload>
```

**Step 3: Run frontend build validation.**

Run: `cd /mnt/d/workspace/OneAll/frontend && npx vite build`

Expected: PASS or surface any missing imports/types before UI work begins.

---

### Task 8: Rebuild the Monitoring Overview Page Around System Honeycomb

**Files:**
- Modify: `frontend/src/pages/Home.vue`
- Modify: `frontend/src/pages/dashboard/HomeOverview.vue`
- Modify: `frontend/src/pages/dashboard/components/DetectionHoneycomb.vue`
- Test: `frontend` build validation

**Step 1: Write the UI against the new payload shape.**

Convert the existing overview page to:

- render one honeycomb cell per system
- display system name and `异常数 / 总数`
- color by aggregated latest status

**Step 2: Add selection-driven detail view below the honeycomb.**

When a user clicks a cell, show a detail panel with:

- system title
- domain count
- abnormal count
- last update time
- domain detail table

**Step 3: Keep the layout restrained and consistent with the rest of the platform.**

Reuse shared table styles (`.oa-table`) and existing overview shell where possible; do not introduce a second sidebar or card maze.

**Step 4: Run frontend build validation.**

Run: `cd /mnt/d/workspace/OneAll/frontend && npx vite build`

Expected: PASS

---

### Task 9: Run Backend and Frontend Verification

**Files:**
- Verify runtime behavior only

**Step 1: Run focused backend tests.**

Run:

```bash
cd /mnt/d/workspace/OneAll/backend && .venv/bin/pytest \
  backend/tests/unit/test_alert_check_target_resolution.py \
  backend/tests/unit/test_alert_check_resolution_backfill_command.py \
  backend/tests/unit/test_system_overview_service.py \
  backend/tests/unit/test_alerts_system_overview_api.py -v
```

Expected: PASS

**Step 2: Run frontend build.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend && npx vite build
```

Expected: PASS

**Step 3: Manual verification checklist.**

Verify that:

- 已纳管并配置系统的域名出现在对应系统单元格下
- 未纳管域名进入 `未纳管域名`
- 有资产但无系统名的域名进入 `未配置系统`
- 点击系统单元格后能看到域名明细和最新状态

---

### Task 10: Review and Residual Risk Check

**Files:**
- Review: `backend/src/apps/alerts/models.py`
- Review: `backend/src/apps/alerts/services/check_target_resolution_service.py`
- Review: `backend/src/apps/alerts/services/system_overview_service.py`
- Review: `backend/src/apps/alerts/api/views.py`
- Review: `frontend/src/pages/dashboard/HomeOverview.vue`
- Review: `frontend/src/pages/dashboard/components/DetectionHoneycomb.vue`

**Step 1: Review the source-of-truth boundary.**

Confirm that system ownership only comes from asset center matching, not from frontend free text.

**Step 2: Review status bucketing.**

Confirm that `missing_system`, `unmanaged`, and `invalid_target` all have explicit, deterministic display behavior.

**Step 3: Review residual risks.**

Document:

- asset record changes do not live-refresh existing checks until backfill runs
- URL normalization may need future support for uncommon protocols
- if data volume grows significantly, the single overview payload may need pagination or split endpoints
