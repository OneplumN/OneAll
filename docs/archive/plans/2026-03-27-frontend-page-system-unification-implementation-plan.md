# Frontend Page System Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Unify ordinary business pages across the frontend so buttons, headers, toolbars, tables, and footers all follow one shared page system, while explicitly excluding the monitoring visualization page currently being developed in another session.

**Architecture:** Evolve `RepositoryPageShell.vue` into the single shared page shell, move page-system rules into shared theme/classes, then migrate representative modules first (`assets`, `alerts`, `settings`) before rolling the shared structure into the remaining ordinary list/form pages. Avoid touching the monitoring visualization page and related files under active parallel development.

**Tech Stack:** Vue 3, TypeScript, SCSS, Element Plus, existing shared theme tokens in `frontend/src/styles/theme.scss`

---

### Task 1: Record the approved page-system design

**Files:**
- Create: `docs/plans/2026-03-27-frontend-page-system-unification-design.md`
- Create: `docs/plans/2026-03-27-frontend-page-system-unification-implementation-plan.md`

**Step 1: Save the approved scope.**

Document that all ordinary business pages are included, but monitoring visualization pages are explicitly excluded.

**Step 2: Save the approved structure.**

Record the four-layer page frame:

```text
标题栏 -> 工具栏 -> 主内容区 -> 底部区
```

**Step 3: Save the approved control rules.**

Document the final rules for:

- primary / secondary / danger / text actions
- refresh placement
- parallel filters
- right-aligned search input
- table action ordering and colors

---

### Task 2: Freeze the shared page-system tokens and utility classes

**Files:**
- Modify: `frontend/src/styles/theme.scss`
- Test: `frontend` build validation

**Step 1: Write the failing audit checklist.**

Expected shared rules:

- one standard for toolbar buttons
- one standard for refresh action
- one standard for filter controls
- one standard for footer layout

**Step 2: Verify the current fragmentation.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
rg -n "toolbar-button|refresh-card|alerts-toolbar|asset-filters|repository-header|page-panel__footer" src
```

Expected: the same concepts are implemented in multiple places with different page-local rules.

**Step 3: Write minimal implementation.**

Add or normalize shared classes/tokens for:

- page header action spacing
- primary / secondary toolbar buttons
- shared refresh action
- toolbar container layout
- narrow / standard filter controls
- list footer layout

**Step 4: Run verification.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
npx vite build
```

Expected: PASS

---

### Task 3: Evolve RepositoryPageShell into the single page shell baseline

**Files:**
- Modify: `frontend/src/components/RepositoryPageShell.vue`
- Modify: `frontend/src/pages/settings/components/SettingsPageShell.vue`
- Modify: `frontend/src/pages/settings/components/SettingsRepositoryShell.vue`
- Test: `frontend` build validation

**Step 1: Write the failing shell checklist.**

Expected shared shell behavior:

- one consistent header layout
- one consistent body border/scroll model
- one consistent footer model
- settings pages can still support aside layouts without becoming a separate visual language

**Step 2: Verify current shell duplication.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
rg -n "repository-header|page-panel|repository-main__footer|repository-aside" \
  src/components/RepositoryPageShell.vue \
  src/pages/settings/components/SettingsPageShell.vue \
  src/pages/settings/components/SettingsRepositoryShell.vue
```

Expected: duplicated shell structure and styling across three components.

**Step 3: Write minimal implementation.**

- make `RepositoryPageShell.vue` the baseline shared shell
- reduce settings shell components to thin wrappers or align them fully with the shared shell rules
- preserve settings-specific aside layout without preserving a separate settings-only visual system

**Step 4: Run verification.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
npx vite build
```

Expected: PASS

---

### Task 4: Migrate representative pages to the unified system

**Files:**
- Modify: `frontend/src/pages/assets/AssetCenter.vue`
- Modify: `frontend/src/pages/alerts/AlertChecks.vue`
- Modify: `frontend/src/pages/alerts/AlertEvents.vue`
- Modify: `frontend/src/pages/settings/SystemSettings.vue`
- Test: `frontend` build validation

**Step 1: Write the failing consistency checklist.**

Expected after migration:

- same header/action rhythm
- same toolbar rhythm
- same button sizing
- same filter sizing/alignment
- same footer structure

**Step 2: Verify current mismatch.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
rg -n "alerts-header|alerts-toolbar|asset-filters|refresh-card|toolbar-button" \
  src/pages/assets/AssetCenter.vue \
  src/pages/alerts/AlertChecks.vue \
  src/pages/alerts/AlertEvents.vue \
  src/pages/settings/SystemSettings.vue
```

Expected: each page still carries its own structure or local variation.

**Step 3: Write minimal implementation.**

- migrate these four pages onto the shared page-system classes
- keep business behavior unchanged
- do not change the monitoring visualization page

**Step 4: Run verification.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
npx vite build
```

Expected: PASS

---

### Task 5: Migrate the remaining ordinary settings pages

**Files:**
- Modify: `frontend/src/pages/settings/Alerts.vue`
- Modify: `frontend/src/pages/settings/AlertTemplates.vue`
- Modify: `frontend/src/pages/settings/AuditLogViewer.vue`
- Modify: `frontend/src/pages/settings/Permissions.vue`
- Modify: `frontend/src/pages/settings/Users.vue`
- Modify: `frontend/src/pages/settings/AlertChannelDetail.vue`
- Test: `frontend` build validation

**Step 1: Write the failing audit list.**

Expected:

- settings pages should no longer look like a parallel product
- table pages and form pages both inherit the shared page system

**Step 2: Run structure audit.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
rg -n "repository-header|toolbar-button|refresh-card|page-panel__footer|repository-main__footer" src/pages/settings
```

Expected: local settings-page-specific structure still exists.

**Step 3: Write minimal implementation.**

Migrate settings pages onto the shared structure without changing their data flow.

**Step 4: Run verification.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
npx vite build
```

Expected: PASS

---

### Current Progress Snapshot

Completed in this round:

- shared ordinary business page shell has been aligned onto `RepositoryPageShell.vue`
- representative list pages in assets / alerts / settings have been migrated
- detail pages now aligned onto the shared detail-page baseline:
  - `frontend/src/pages/settings/PermissionRoleDetail.vue`
  - `frontend/src/pages/settings/AlertChannelDetail.vue`
  - `frontend/src/pages/alerts/AlertCheckDetail.vue`
  - `frontend/src/pages/alerts/AlertEventDetail.vue`

Immediate next steps after the current layout spacing fix:

1. continue cleaning the remaining old page-local detail shells in real pages and shared settings internals
2. focus next on:
   - `frontend/src/pages/tools/GrafanaSync.vue`
   - `frontend/src/pages/tools/AccountSync.vue`
   - `frontend/src/pages/settings/components/SettingsTabs.vue`
3. keep excluding the monitoring visualization page being developed in the parallel session

### Task 6: Unify MainLayout content spacing with the approved page baseline

**Files:**
- Modify: `frontend/src/layouts/MainLayout.vue`
- Test: `frontend` build validation

**Problem statement:**

`MainLayout.vue` currently applies default padding at both `layout__main` and `layout__content-wrapper`, which causes a double outer gutter on non-flat pages. This is inconsistent with the approved business-page baseline that has converged on a single content gutter and `0 16px 16px` route-level padding for most ordinary pages.

**Step 1: Remove double default padding responsibility.**

- stop using `layout__main` as a default padding carrier
- keep `layout__content-wrapper` as the single content gutter layer

**Step 2: Align the default gutter with the current page baseline.**

- change the default non-flat page padding from `24px` to `0 16px 16px`
- preserve `route.meta.contentPadding`
- preserve `layoutFlat`

**Step 3: Leave max width unchanged in this task.**

- keep `max-width: 1600px` for now
- defer any page-type-specific width expansion to a separate task if still needed after the padding fix

**Step 4: Run verification.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
npx vite build
```

Expected: PASS

### Task 6: Migrate probes and tools ordinary pages

**Files:**
- Modify: `frontend/src/pages/probes/ProbeManager.vue`
- Modify: `frontend/src/pages/probes/ProbeSchedules.vue`
- Modify: `frontend/src/pages/monitoring/MonitoringHistory.vue`
- Modify: `frontend/src/pages/tools/ToolLibrary.vue`
- Modify: `frontend/src/pages/tools/CodeRepository.vue`
- Test: `frontend` build validation

**Step 1: Write the failing audit list.**

Expected:

- probes/tools list pages should inherit the same button, filter, table, and footer system
- no page should keep a module-specific toolbar style unless structurally necessary

**Step 2: Run structure audit.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
rg -n "toolbar-button|refresh-card|page-header|page-toolbar|repository-table|asset-footer" \
  src/pages/probes \
  src/pages/monitoring/MonitoringHistory.vue \
  src/pages/tools
```

Expected: mixed page-local structures remain.

**Step 3: Write minimal implementation.**

Migrate the remaining ordinary list pages onto the shared page system, while explicitly skipping the monitoring visualization page and any file under active parallel work.

**Step 4: Run verification.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
npx vite build
```

Expected: PASS

---

### Task 7: Review exclusions and regression boundaries

**Files:**
- Review: `frontend/src/pages/Home.vue`
- Review: `frontend/src/pages/dashboard/HomeOverview.vue`
- Review: `frontend/src/services/alertsApi.ts`

**Step 1: Verify excluded pages were not touched.**

Confirm that monitoring visualization files were not modified by this workstream.

**Step 2: Verify no business behavior changed.**

Check that this round only changes presentation/system structure, not APIs, routing, or domain logic.

**Step 3: Record residual risk.**

Document:

- pages with especially custom form layouts may need one extra pass
- a few legacy scoped styles may still survive in low-traffic pages
- if future pages bypass the shared shell, drift will reappear

---

### Task 8: Final validation and code review

**Files:**
- Review: `frontend/src/styles/theme.scss`
- Review: `frontend/src/components/RepositoryPageShell.vue`
- Review: `frontend/src/pages/assets/AssetCenter.vue`
- Review: `frontend/src/pages/alerts/AlertChecks.vue`
- Review: `frontend/src/pages/alerts/AlertEvents.vue`
- Review: `frontend/src/pages/settings/SystemSettings.vue`

**Step 1: Run build verification.**

Run:

```bash
cd /mnt/d/workspace/OneAll/frontend
npx vite build
```

Expected: PASS

**Step 2: Run targeted code review.**

Review for:

- shared classes replacing page-local duplicates
- no new hardcoded page-system sizes or action patterns
- no accidental edits to excluded monitoring visualization files

**Step 3: Manual acceptance review.**

Verify on representative pages:

- button sizes match
- refresh entry matches
- filters align horizontally
- footer spacing matches
- action column ordering/colors match
