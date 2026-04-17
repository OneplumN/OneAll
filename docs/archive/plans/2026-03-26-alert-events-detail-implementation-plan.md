# Alert Events Detail Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reshape the alert events list and detail pages into a user-facing notification result view, removing raw context exposure while keeping the business fields needed for on-call handling.

**Architecture:** Keep the current backend event model and list API unchanged for this round. Implement the new semantics in the frontend by deriving strategy/target/contact fields from `context`, renaming `status` to “通知状态”, simplifying list filters, and replacing the technical detail layout with a two-column “字段：值” presentation.

**Tech Stack:** Vue 3, TypeScript, Element Plus, existing `alertsApi` service, existing `RepositoryPageShell` / page shell styles.

---

### Task 1: Record the Product Semantics in Docs

**Files:**
- Create: `docs/plans/2026-03-26-alert-events-detail-design.md`
- Create: `docs/plans/2026-03-26-alert-events-detail-implementation-plan.md`

**Step 1: Write the design decisions for alert event definition, list columns, detail fields, and removed technical sections.**

**Step 2: Save the exact list/detail field order and default fallback texts so implementation stays aligned with the approved design.**

---

### Task 2: Simplify the Alert Events List Page

**Files:**
- Modify: `frontend/src/pages/alerts/AlertEvents.vue`

**Step 1: Remove the source filter and replace the current status column label with `通知状态`.**

**Step 2: Derive `监控策略` and `目标` from each event’s `context` object.**

**Step 3: Change the table columns to exactly:**

```text
告警级别 / 告警标题 / 监控策略 / 目标 / 通知状态 / 告警时间
```

**Step 4: Keep row-click navigation to the detail page.**

**Step 5: Update keyword search to match title, message, strategy, and target.**

---

### Task 3: Rebuild the Alert Event Detail Page Layout

**Files:**
- Modify: `frontend/src/pages/alerts/AlertEventDetail.vue`

**Step 1: Remove the existing `el-descriptions` block and the `原始上下文` section.**

**Step 2: Replace it with a text-based layout in this order:**

```text
告警标题
告警内容

目标 / 状态码
监控策略 / 关联探针
告警级别 / 通知状态
连续失败次数 / 告警时间
通知对象 / 通知发送时间
```

**Step 3: Keep values derived from `context`, with user-facing fallback text instead of raw technical empties.**

**Step 4: Keep the top right `返回列表` action and do not add extra section headings.**

---

### Task 4: Validate Types and Build

**Files:**
- Inspect: `frontend/src/services/alertsApi.ts`

**Step 1: Ensure existing event typings still support the new derived fields without requiring backend changes.**

**Step 2: Run the frontend production build:**

```bash
cd frontend
npm run build
```

**Step 3: Fix any Vue template / TypeScript issues discovered during build.**

---

### Task 5: Review and Residual Risk Check

**Files:**
- Review: `frontend/src/pages/alerts/AlertEvents.vue`
- Review: `frontend/src/pages/alerts/AlertEventDetail.vue`

**Step 1: Verify the frontend no longer exposes raw `context` JSON.**

**Step 2: Verify list/detail semantics consistently use `通知状态` instead of `状态`.**

**Step 3: Note residual risk: detail page still fetches all events and finds one locally until a dedicated detail endpoint is added.**
