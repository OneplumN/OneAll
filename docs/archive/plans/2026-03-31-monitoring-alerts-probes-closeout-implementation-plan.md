# Monitoring / Alerts / Probes Close-out Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the current monitoring, alerts, and probes consolidation so the product boundary is clear: node capability stays in probes, strategy configuration stays in alerts, and alert results stay in alert events.

**Architecture:** The backend already has the unified alerts-side models (`AlertCheck`, `AlertSchedule`, `AlertCheckExecution`) and a central scheduler entry. The remaining work is primarily close-out and boundary cleanup: remove leftover mixed pages/entry points, complete the alerts-first strategy workflow, and keep probes focused on node runtime/health only.

**Tech Stack:** Django + DRF, Celery, Vue 3, Element Plus, existing `RepositoryPageShell` page system.

---

## 1. Current Architecture Baseline

### Backend baseline

- `apps.alerts` already owns:
  - `AlertEvent`
  - `AlertCheck`
  - `AlertSchedule`
  - `AlertCheckExecution`
- `apps.alerts.tasks` already contains:
  - `run_due_alert_schedules`
  - `run_alert_check`
  - central-scheduler feature flag support
- `apps.probes` still owns:
  - `ProbeNode`
  - probe agent registration / heartbeat / runtime metrics
  - probe-side manual schedule execution helpers
- probe execution failures are already capable of entering the alerts domain and producing `AlertEvent`.

### Frontend baseline

- Monitoring-and-alerts top nav is already the main entry.
- Existing active pages are effectively:
  - `拨测可视化`
  - `告警事件`
  - `监控策略`
  - `节点`
  - `日志`
- Alerts pages already exist:
  - `frontend/src/pages/alerts/AlertChecks.vue`
  - `frontend/src/pages/alerts/AlertCheckDetail.vue`
  - `frontend/src/pages/alerts/AlertEvents.vue`
  - `frontend/src/pages/alerts/AlertEventDetail.vue`
- Probes pages still contain mixed / historical residue:
  - `frontend/src/pages/probes/ProbeCenter.vue`
  - `frontend/src/pages/probes/ProbeSchedules.vue`
  - probe-center widgets that overlap with alerts-side strategy / event responsibilities

### Product boundary already agreed in this round

- Probes domain:
  - only node registration, node heartbeat, node runtime health, node metrics, node logs
- Alerts domain:
  - monitoring strategy definition
  - strategy alert conditions / contacts / channels
  - alert events and detail presentation
  - unified execution perspective where needed
- Monitoring overview:
  - dashboard / visualization only
  - should not reintroduce strategy-editing responsibility

---

## 2. What Is Already Done

### Completed and can be treated as baseline

- Alerts-side unified models and API skeleton are in place.
- Central scheduler implementation path exists behind feature flag.
- Probe agent auto-registration / heartbeat path has already been pushed forward.
- Probe runtime charts and health snapshots already exist in the node page.
- Alert events list + detail page already moved away from raw backend log exposure and toward business-facing fields.
- Alert strategy list and dedicated strategy detail/edit page already exist.
- Top navigation has already been reduced to the monitoring-and-alerts group rather than keeping the old fragmented structure.

### Done enough for now, no further deepening in this round

- Asset line is considered sealed except for future upstream integrations.
- Timescale instability is an environment issue, not the blocker for this close-out line.

---

## 3. Remaining Mixed / Incomplete Areas

### A. Navigation and entry-point residue

- `ProbeCenter.vue` is still a mixed summary page and overlaps with:
  - nodes
  - strategy list
  - execution summary
- Legacy redirects and historical probe center concepts still exist in router.
- The monitoring-and-alerts information architecture is still understandable to the team only because of recent conversation context, not because the code is clean.

### B. Strategy workflow is present but not fully sealed

- `监控策略` already lists and edits strategy basics.
- Still needs final boundary confirmation that:
  - create / edit / clone / delete are all alerts-first
  - probe assignment and detection mode selection belong to strategy editing
  - no remaining page still expects users to configure schedules elsewhere

### C. Probes domain is still carrying non-node responsibility in UI

- Probe center cards and schedule summary still expose strategy semantics.
- The probe area should present:
  - node inventory
  - runtime health
  - recent logs / runtime diagnostics
- It should not be the place where users understand “what should be monitored”.

### D. Validation and regression control are not yet closed

- We already have unit coverage for several backend pieces, but the whole monitoring/alerts/probes path still needs one explicit close-out review pass.
- Frontend pages in this line still need final smoke validation after cleanup:
  - strategy list
  - strategy detail
  - alert events list
  - alert event detail
  - probe nodes page

---

## 4. Close-out Checklist

### Task 1: Lock the agreed module boundary in code

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/pages/probes/ProbeCenter.vue`
- Modify: `frontend/src/pages/probes/ProbeSchedules.vue`
- Modify: `frontend/src/pages/alerts/AlertChecks.vue`
- Modify: `frontend/src/pages/probes/ProbeManager.vue`

**Checklist:**
- Remove or demote pages that still mix node, strategy, and alert concepts.
- Keep monitoring-and-alerts side nav focused on:
  - `拨测可视化`
  - `告警事件`
  - `监控策略`
  - `节点`
  - `日志`
- Ensure each page has exactly one responsibility.

**Expected result:**
- Users no longer need historical knowledge of the product to understand where to do things.

### Task 2: Finish alerts-first strategy flow

**Files:**
- Modify: `frontend/src/pages/alerts/AlertChecks.vue`
- Modify: `frontend/src/pages/alerts/AlertCheckDetail.vue`
- Modify: `frontend/src/services/alertsApi.ts`
- Modify: `backend/src/apps/alerts/api/views.py`

**Checklist:**
- Verify strategy list shows only strategy-level information.
- Verify create / edit / clone / delete all operate in the alerts domain.
- Verify detail form owns:
  - probe selection
  - detection mode
  - target
  - protocol
  - frequency
  - alert conditions
  - contacts / channels
- Remove any remaining dependency on probe-side schedule-editing entry points.

**Expected result:**
- “监控策略” becomes the only business entry for strategy management.

### Task 3: Strip probes UI down to node operations

**Files:**
- Modify: `frontend/src/pages/probes/ProbeManager.vue`
- Modify: `frontend/src/pages/probes/ProbeCenter.vue`
- Modify: `frontend/src/pages/probes/components/*.vue`
- Modify: `frontend/src/services/probeNodeApi.ts`

**Checklist:**
- Keep node table, runtime drawer, health trends, and node-level logs.
- Remove strategy/execution summary widgets that belong to alerts.
- Ensure labels and copy match node-runtime semantics rather than strategy semantics.

**Expected result:**
- Probe pages read like infrastructure/node pages, not like monitoring-control pages.

### Task 4: Finalize alert event presentation

**Files:**
- Modify: `frontend/src/pages/alerts/AlertEvents.vue`
- Modify: `frontend/src/pages/alerts/AlertEventDetail.vue`
- Modify: `frontend/src/services/alertsApi.ts`

**Checklist:**
- Keep list fields simple:
  - monitoring strategy
  - target
  - severity
  - contacts
  - notification status
  - alert time
- Detail page stays business-facing, with no raw backend context dump.
- Ensure navigation is list -> detail only.

**Expected result:**
- Alert events page is readable as an operator-facing incident/event surface.

### Task 5: Remove historical dead paths and verify no hidden dependency remains

**Files:**
- Search/Modify: `frontend/src/**`
- Search/Modify: `backend/src/**`

**Checklist:**
- Search for historical probe-alert / probe-schedule-only UI references.
- Confirm no active page still depends on removed route assumptions.
- Confirm redirects do not send users into dead legacy concepts.

**Expected result:**
- No hidden dependence on old “probe center does everything” model.

### Task 6: Close-out review and validation

**Files:**
- Modify: this plan file progress section
- Test: relevant backend unit tests
- Test: frontend type-check / build or targeted smoke verification

**Checklist:**
- Run targeted backend tests for alerts/probes mapping and scheduler integration.
- Run frontend compilation or type-check for changed pages.
- Perform manual smoke checks:
  - strategy list loads
  - strategy detail opens and saves
  - alert events list/detail work
  - nodes page works
- Record final progress and remaining deferred items.

---

## 5. Priority Order For This Round

1. Module boundary cleanup
2. Alerts-first strategy flow sealing
3. Probes page slimming
4. Alert events polish and dependency cleanup
5. Review + validation

---

## 6. Explicitly Deferred To Next Round

- Further redesign of probe agent/server authentication and packaging flow
- Deep metrics modeling beyond current runtime charts
- Additional alert handling workflow beyond current event / strategy surfaces
- Any new asset-source integration work

---

## 7. Progress Log

### 2026-03-31

- This document is created as the close-out baseline after the asset line was sealed.
- Current judgment:
  - asset line: effectively sealed
  - monitoring / alerts / probes line: backend foundation is present, frontend/domain boundary still needs close-out
- Immediate execution rule for the next implementation steps:
  - do not add new domain concepts
  - only close gaps, remove residue, and make the existing architecture legible
- First close-out pass completed:
  - legacy `/probes` and `/monitoring/probes` entries now redirect to `/probes/nodes`
  - side-nav icon responsibility moved to `监控策略` instead of the removed probe-center entry
  - `监控策略` list now supports actual clone flow and actual delete flow for manual probe strategies
  - probe alert template result links now point to the alerts-side strategy detail page instead of the removed probe schedule page
- Validation completed for this pass:
  - frontend `npm run build`: passed
  - backend `USE_TIMESCALE=0 python3 -m pytest backend/tests/unit/test_probe_alert_service.py -q`: passed
- Second close-out pass completed:
  - `alerts/checks` now supports `POST / PATCH / DELETE` for manual strategies
  - `监控策略` detail page now uses `alertsApi` for create / update / delete flow, no longer directly depends on `probeScheduleApi`
  - strategy detail now supports explicit probe selection in the alerts domain
  - `ProbeScheduleSerializer` now formally supports `alert_channels`, `cert_check_enabled`, `cert_warning_days`
  - manual strategy create/update now always refreshes alerts mapping, and HTTPS certificate-pair sync now runs after probe assignment
- Validation completed for the second pass:
  - backend `USE_TIMESCALE=0 python3 -m pytest backend/tests/unit/test_alert_checks_api.py backend/tests/unit/test_probe_schedule_serializer.py -q`: passed
  - frontend `npx vue-tsc --noEmit`: passed
- Third close-out pass completed:
  - removed dead probe-center / probe-schedules frontend pages and their self-contained dead components
  - removed dead `probeScheduleApi.ts` frontend service after strategy CRUD fully moved to alerts-side APIs
  - `probeScheduleExecutionApi.ts` now carries only the execution-side types it still needs
- Validation completed for the third pass:
  - dead-reference scan for removed probe-center / probe-schedules frontend modules: clean
  - frontend `npx vue-tsc --noEmit`: passed
- Fourth close-out pass completed:
  - `日志` 页面从“拨测历史记录”口径收口为“执行日志”口径
  - `MonitoringHistory.vue` 只保留执行语义字段：策略、目标、协议、状态、探针、耗时、状态码、结果摘要、时间线
  - 探针筛选改为真实节点列表，不再从当前表格结果反推筛选项
  - 删除页面内部未使用的旧统计/旧交互残留，保持与其他列表页一致
- Validation completed for the fourth pass:
  - frontend `npx vue-tsc --noEmit`: passed
- Fifth close-out pass completed:
  - completed a five-page smoke review across `拨测可视化 / 监控策略 / 告警事件 / 节点 / 日志`
  - `拨测可视化` 页面标题与导航口径统一
  - `监控策略` 页面清理未使用的探针健康残留状态和样式，减少历史噪音
  - `节点` 页面操作入口和抽屉标题统一为“详情”语义
- Validation completed for the fifth pass:
  - frontend `npx vue-tsc --noEmit`: passed
