# Alerts–Probes Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Route all probe-related alerts into the unified alerts domain (`AlertEvent`), remove legacy probe alerts API and UI, and ensure all alert displays use `/api/alerts/events`.

**Architecture:** Probe execution remains in `apps.probes`, but when a probe schedule execution fails it produces a `CheckResult(source="probes", ...)` that flows through `apps.alerts.services.evaluate_and_raise` to create `AlertEvent` records. The alerts API is extended with filtering, and the frontend dashboard/menus are updated to rely exclusively on the alerts domain for alert display.

**Tech Stack:** Django (apps `alerts`, `probes`, `monitoring`), DRF, Celery, Vue 3 + Pinia, axios.

---

### Task 1: Locate and understand existing probe alert creation and API

**Files:**
- Modify: `backend/src/apps/probes/api/probe_views.py`
- Modify: `backend/src/apps/probes/api/serializers.py`
- Search: `backend/src/apps/probes` for `probes.alert` / `AuditLog`

**Step 1:** Use ripgrep to find where probe alerts are currently created and how `RecentProbeAlertView` works.

Run: `rg "probes\.alert" -n backend/src/apps/probes backend/src/apps`

**Step 2:** Open `probe_views.py` and `serializers.py` to confirm current response shape for `/api/probes/alerts/recent/` and what data is pulled from `AuditLog`.

**Step 3:** Open any services that write probe alert audit logs and note which execution fields they include (schedule, probe, status, threshold, contacts, message, occurred_at).

---

### Task 2: Extend alerts API to support filtering (source/severity/limit)

**Files:**
- Modify: `backend/src/apps/alerts/api/views.py`
- Modify: `backend/src/apps/alerts/api/serializers.py` (if needed to expose context)
- Test: `backend/tests/**/test_alerts_*.py` (or create a new test module)

**Step 1:** Update `AlertEventListView.get_queryset` (or equivalent) to read query params `source`, `severity`, and `limit`, applying filters and slicing on the base queryset.

**Step 2:** Ensure the serializer used for `AlertEvent` includes `source`, `severity`, `title`, `message`, `status`, `created_at`, `sent_at`, and `context` (if not already exposed).

**Step 3:** Add or update unit tests to validate:
- Filtering by `source` returns only matching events.
- Filtering by `severity` works.
- The `limit` parameter enforces a maximum count and respects an upper bound (e.g., max 200).

**Step 4:** Run relevant tests (or full backend test suite if fast enough) and ensure they pass.

Run: `cd backend && python3 -m pytest -q`

---

### Task 3: Route probe execution failures into AlertEvent via CheckResult

**Files:**
- Search/Modify: `backend/src/apps/probes/services/**`
- Search/Modify: `backend/src/apps/probes/tasks.py`
- Modify: `backend/src/apps/alerts/services.py` imports usage
- Test: `backend/tests/unit/test_probes_alerts_integration.py` (new)

**Step 1:** Use ripgrep to find where `ProbeScheduleExecution.record_result` or probe schedule execution failures are handled and where any `AuditLog(action="probes.alert")` entries are created.

Run: `rg "ProbeScheduleExecution" -n backend/src/apps/probes` and `rg "probes.alert" -n backend/src`

**Step 2:** In the place where a probe execution result is finalized (especially FAILED/MISSED/timeout-like statuses), construct a `CheckResult` with:
- `source="probes"`
- appropriate `event_type` (e.g., `"probe_schedule_execution"`)
- `severity` derived from execution status
- `title` summarizing the schedule/probe
- `message` using the execution message or error
- `task_id` set to the `ProbeSchedule.id`
- `context` containing probe/schedule/execution details (ids, names, status, response_time_ms, etc.).

**Step 3:** Call `evaluate_and_raise(check_result)` and, if it returns an `AlertEvent`, call `dispatch_alert_event.delay(event.id)` to enqueue dispatch. Preserve any existing audit logging if required, but remove reliance on `AuditLog(probes.alert)` as the UI data source.

**Step 4:** Add unit tests that simulate a failing probe execution and assert that an `AlertEvent` is created with `source="probes"` and correct `context` fields populated.

**Step 5:** Run relevant tests.

Run: `cd backend && python3 -m pytest tests/unit/test_probes_alerts_integration.py -q`

---

### Task 4: Remove legacy probe alerts API and serializer

**Files:**
- Modify: `backend/src/apps/probes/api/probe_views.py`
- Modify: `backend/src/apps/probes/api/serializers.py`
- Modify: `backend/src/apps/probes/api/urls.py`
- Test: Remove/update any tests referencing `/api/probes/alerts/recent/`

**Step 1:** Delete the `RecentProbeAlertView` class and any helper functions used only by it.

**Step 2:** Remove `ProbeAlertRecordSerializer` and any imports/usages.

**Step 3:** Remove the URL pattern for `"probes/alerts/recent/"` from `urls.py`.

**Step 4:** Search the backend tests for `/probes/alerts/recent/` and either delete or update those tests to target `/api/alerts/events` instead.

Run: `rg "/probes/alerts/recent" -n backend`

**Step 5:** Run the backend test suite again to ensure no references remain and all tests pass.

Run: `cd backend && python3 -m pytest -q`

---

### Task 5: Update frontend services to use alertsApi instead of probeAlertApi

**Files:**
- Modify/Delete: `frontend/src/services/probeAlertApi.ts`
- Modify: `frontend/src/services/alertsApi.ts`
- Modify: any components that import `probeAlertApi` or `ProbeAlertRecord`
- Test: `npm run test` (if configured) or manual smoke test via `npm run dev`

**Step 1:** Open `alertsApi.ts` and add a `fetchAlertEvents(params?: { source?: string; severity?: string; limit?: number })` function that calls `/alerts/events` with query params.

**Step 2:** Search for usages of `probeAlertApi` and `ProbeAlertRecord` across `frontend/src`.

Run: `rg "probeAlertApi" -n frontend/src` and `rg "ProbeAlertRecord" -n frontend/src`

**Step 3:** For each usage, switch to `alertsApi.fetchAlertEvents`, adapting the data mapping as needed (mapping from `AlertEvent` to the component's expected props or updating the component types to use `AlertEvent`).

**Step 4:** Once all usages are migrated, delete `probeAlertApi.ts`.

**Step 5:** Run `npm run build` (or at least `npm run lint` / `npm run test` if available) to ensure the frontend compiles.

---

### Task 6: Remove probe-specific alert visuals from probes module and dashboard, add global recent alerts card (optional)

**Files:**
- Modify: `frontend/src/pages/dashboard/HomeOverview.vue`
- Modify: `frontend/src/pages/probes/components/RecentAlertsPanel.vue` (or remove if no longer needed)
- Modify: any probes pages that reference recent alerts

**Step 1:** Update `HomeOverview.vue` to remove the "最近探针告警" card and, if desired, replace it with a generic "最近告警" card that uses `alertsApi.fetchAlertEvents({ limit: 8 })` and displays events from all sources.

**Step 2:** Remove any references to `RecentAlertsPanel` under probes pages if they display probe-specific alerts. Decide whether to delete the component or keep it as a generic alert list component wired to `AlertEvent` types.

**Step 3:** Search for any remaining references to probe alerts UI and clean them up.

Run: `rg "探针告警" -n frontend/src` and `rg "RecentAlertsPanel" -n frontend/src`

**Step 4:** Run `npm run dev` and verify manually in the browser that:
- Probes pages no longer show alert lists.
- Alert events page `/alerts/events` shows both monitoring and probes alerts (once data exists).
- (If implemented) Dashboard shows a global "最近告警" card driven by `/api/alerts/events`.

---

### Task 7: End-to-end smoke test and documentation update

**Files:**
- Modify: `docs/plans/2026-03-18-alerts-probes-unification-design.md` (if design doc exists)
- Modify: any high-level README or module docs that mention probe alerts API

**Step 1:** With backend running (`python3 manage.py runserver 0.0.0.0:8000`) and frontend via `npm run dev`, trigger a failing probe schedule execution (using existing UI or an ad-hoc script) and confirm that:
- An `AlertEvent` with `source="probes"` is created.
- It appears in `/alerts/events`.

**Step 2:** Verify no network calls are made to `/api/probes/alerts/recent/` from the frontend (use browser devtools network tab).

**Step 3:** Update any relevant docs to reflect that probe alerts are now unified under the alerts domain and the old probe alerts API is gone.

