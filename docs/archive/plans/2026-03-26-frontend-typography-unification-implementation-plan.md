# Frontend Typography Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Unify frontend font-family and font-size usage so assets, alerts, probes, and settings pages use one shared typography system instead of page-local hardcoded sizes.

**Architecture:** Centralize the type scale in `theme.scss`, reduce duplicate root/body font definitions, then migrate page-level styles in phases. Each phase should replace hardcoded font sizes with shared tokens or shared semantic classes and verify that key list, detail, and form views still render correctly.

**Tech Stack:** Vue 3, Vite, TypeScript, SCSS, Element Plus

---

### Task 1: Freeze the current typography baseline

**Files:**
- Modify: `frontend/src/styles/theme.scss`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/assets/main.css`
- Test: `frontend` build and targeted lint

**Step 1: Write the failing check list**

Document the expected single source of truth:

- `theme.scss` owns the typography tokens
- `App.vue` no longer defines root font-family
- `main.css` only inherits from the theme instead of redefining a competing stack

**Step 2: Verify the current duplication**

Run:

```bash
rg -n "font-family|font-size" frontend/src/App.vue frontend/src/assets/main.css frontend/src/styles/theme.scss
```

Expected: multiple conflicting font-family and font-size definitions are present.

**Step 3: Write minimal implementation**

- Add the new token family:
  - `--oa-font-size-xs`
  - `--oa-font-size-sm`
  - `--oa-font-size-md`
  - `--oa-font-size-lg`
  - `--oa-font-size-xl`
  - `--oa-font-size-2xl`
- Point existing semantic tokens to the new scale
- Remove redundant root typography declarations from `App.vue`
- Make `main.css` inherit the shared font stack instead of redefining a different one

**Step 4: Run verification**

Run:

```bash
npx eslint src/App.vue
npm run build
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/styles/theme.scss frontend/src/App.vue frontend/src/assets/main.css
git commit -m "refactor: centralize frontend typography tokens"
```

### Task 2: Add reusable typography semantics for shared shells

**Files:**
- Modify: `frontend/src/components/RepositoryPageShell.vue`
- Modify: `frontend/src/pages/settings/components/SettingsPageShell.vue`
- Modify: `frontend/src/pages/settings/components/SettingsRepositoryShell.vue`
- Modify: `frontend/src/pages/detection/components/OneOffPageShell.vue`
- Test: affected shell pages via build

**Step 1: Write the failing consistency checklist**

Expected shell behaviors:

- root title uses shared title size
- subtitle / breadcrumb uses shared helper size
- body inherits base font size

**Step 2: Verify current hardcoded sizes**

Run:

```bash
rg -n "font-size:" frontend/src/components/RepositoryPageShell.vue frontend/src/pages/settings/components/SettingsPageShell.vue frontend/src/pages/settings/components/SettingsRepositoryShell.vue frontend/src/pages/detection/components/OneOffPageShell.vue
```

Expected: these shells contain page-local numeric sizes.

**Step 3: Write minimal implementation**

- Replace hardcoded title and subtitle sizes with shared typography tokens
- Keep only shell-specific spacing and layout in the shell files

**Step 4: Run verification**

Run:

```bash
npx eslint src/components/RepositoryPageShell.vue src/pages/settings/components/SettingsPageShell.vue src/pages/settings/components/SettingsRepositoryShell.vue src/pages/detection/components/OneOffPageShell.vue
npm run build
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/RepositoryPageShell.vue frontend/src/pages/settings/components/SettingsPageShell.vue frontend/src/pages/settings/components/SettingsRepositoryShell.vue frontend/src/pages/detection/components/OneOffPageShell.vue
git commit -m "refactor: unify typography in shared page shells"
```

### Task 3: Migrate assets pages to the shared scale

**Files:**
- Modify: `frontend/src/pages/assets/AssetCenter.vue`
- Modify: `frontend/src/pages/assets/AssetModelCenter.vue`
- Modify: `frontend/src/pages/assets/AssetModelAdmin.vue`
- Modify: `frontend/src/pages/assets/AssetFieldAdmin.vue`
- Test: assets pages build and smoke review

**Step 1: Write the failing audit list**

Expected mappings:

- list/table meta text => `12px`
- list/table secondary text => `13px`
- primary table content => `14px`
- section titles => `16px`

**Step 2: Verify hardcoded sizes**

Run:

```bash
rg -n "font-size:" frontend/src/pages/assets/AssetCenter.vue frontend/src/pages/assets/AssetModelCenter.vue frontend/src/pages/assets/AssetModelAdmin.vue frontend/src/pages/assets/AssetFieldAdmin.vue
```

Expected: multiple `12px` and `13px` values remain.

**Step 3: Write minimal implementation**

- Replace repeated font sizes with shared tokens
- Keep intentional large titles only where needed
- Ensure assets list and model management pages visually align

**Step 4: Run verification**

Run:

```bash
npx eslint src/pages/assets/AssetCenter.vue src/pages/assets/AssetModelCenter.vue src/pages/assets/AssetModelAdmin.vue src/pages/assets/AssetFieldAdmin.vue
npm run build
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/assets/AssetCenter.vue frontend/src/pages/assets/AssetModelCenter.vue frontend/src/pages/assets/AssetModelAdmin.vue frontend/src/pages/assets/AssetFieldAdmin.vue
git commit -m "refactor: unify typography in asset pages"
```

### Task 4: Migrate alerts pages to the shared scale

**Files:**
- Modify: `frontend/src/pages/alerts/AlertEvents.vue`
- Modify: `frontend/src/pages/alerts/AlertEventDetail.vue`
- Modify: `frontend/src/pages/alerts/AlertChecks.vue`
- Modify: `frontend/src/pages/alerts/AlertCheckDetail.vue`
- Test: alerts pages build and smoke review

**Step 1: Write the failing audit list**

Expected mappings:

- list header and subtitle layers match asset pages
- detail labels and values use the approved shared scale
- alert list and alert detail no longer invent separate title sizes without reason

**Step 2: Verify hardcoded sizes**

Run:

```bash
rg -n "font-size:" frontend/src/pages/alerts/AlertEvents.vue frontend/src/pages/alerts/AlertEventDetail.vue frontend/src/pages/alerts/AlertChecks.vue frontend/src/pages/alerts/AlertCheckDetail.vue
```

Expected: a mix of `12px`, `13px`, `14px`, `15px`, `16px`, `18px`, and `20px`.

**Step 3: Write minimal implementation**

- Replace detail-page and list-page hardcoded font sizes with tokens
- Preserve the approved alert event detail hierarchy while converting to shared sizes

**Step 4: Run verification**

Run:

```bash
npx eslint src/pages/alerts/AlertEvents.vue src/pages/alerts/AlertEventDetail.vue src/pages/alerts/AlertChecks.vue src/pages/alerts/AlertCheckDetail.vue
npm run build
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/alerts/AlertEvents.vue frontend/src/pages/alerts/AlertEventDetail.vue frontend/src/pages/alerts/AlertChecks.vue frontend/src/pages/alerts/AlertCheckDetail.vue
git commit -m "refactor: unify typography in alert pages"
```

### Task 5: Migrate probes pages to the shared scale

**Files:**
- Modify: `frontend/src/pages/probes/ProbeCenter.vue`
- Modify: `frontend/src/pages/probes/ProbeManager.vue`
- Modify: `frontend/src/pages/probes/ProbeSchedules.vue`
- Modify: `frontend/src/pages/probes/components/ProbeSummaryGrid.vue`
- Modify: `frontend/src/pages/probes/components/ExecutionStatusPanel.vue`
- Modify: `frontend/src/pages/probes/components/CriticalNodesPanel.vue`
- Test: probes pages build and smoke review

**Step 1: Write the failing audit list**

Expected mappings:

- summary cards use shared headline and meta sizes
- probe list/detail text matches the other domains
- monospace remains only for machine values where it helps readability

**Step 2: Verify hardcoded sizes**

Run:

```bash
rg -n "font-size:" frontend/src/pages/probes/ProbeCenter.vue frontend/src/pages/probes/ProbeManager.vue frontend/src/pages/probes/ProbeSchedules.vue frontend/src/pages/probes/components/ProbeSummaryGrid.vue frontend/src/pages/probes/components/ExecutionStatusPanel.vue frontend/src/pages/probes/components/CriticalNodesPanel.vue
```

Expected: multiple hardcoded sizes remain.

**Step 3: Write minimal implementation**

- Replace hardcoded sizes with shared tokens
- Keep KPI cards and health numbers legible without creating a separate probe-only typography system

**Step 4: Run verification**

Run:

```bash
npx eslint src/pages/probes/ProbeCenter.vue src/pages/probes/ProbeManager.vue src/pages/probes/ProbeSchedules.vue src/pages/probes/components/ProbeSummaryGrid.vue src/pages/probes/components/ExecutionStatusPanel.vue src/pages/probes/components/CriticalNodesPanel.vue
npm run build
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/probes/ProbeCenter.vue frontend/src/pages/probes/ProbeManager.vue frontend/src/pages/probes/ProbeSchedules.vue frontend/src/pages/probes/components/ProbeSummaryGrid.vue frontend/src/pages/probes/components/ExecutionStatusPanel.vue frontend/src/pages/probes/components/CriticalNodesPanel.vue
git commit -m "refactor: unify typography in probe pages"
```

### Task 6: Final audit and regression check

**Files:**
- Modify: `docs/plans/2026-03-26-frontend-typography-unification-design.md`
- Modify: `docs/plans/2026-03-26-frontend-typography-unification-implementation-plan.md`
- Test: full frontend verification

**Step 1: Verify no new raw sizes were added to targeted files**

Run:

```bash
rg -n "font-size:\\s*(12px|13px|14px|15px|16px|18px|20px)" frontend/src/pages/assets frontend/src/pages/alerts frontend/src/pages/probes frontend/src/components frontend/src/pages/settings/components
```

Expected: remaining hits should be intentional exceptions only.

**Step 2: Run the final build**

Run:

```bash
npm run build
```

Expected: PASS

**Step 3: Manually review critical pages**

Review:

- Assets list and model pages
- Alert events list and detail
- Alert checks list and detail
- Probe center and probe manager

Expected: same typography hierarchy across equivalent page structures.

**Step 4: Update the docs if the implemented mapping changed**

- Keep the design doc aligned with the actual adopted scale

**Step 5: Commit**

```bash
git add docs/plans/2026-03-26-frontend-typography-unification-design.md docs/plans/2026-03-26-frontend-typography-unification-implementation-plan.md
git commit -m "docs: record frontend typography unification plan"
```
