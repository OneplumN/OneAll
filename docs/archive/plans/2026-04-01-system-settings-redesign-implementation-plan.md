# System Settings Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the system settings domain into four stable platform-administration areas: platform configuration, users and permissions, notification management, and authentication integration.

**Architecture:** Keep the existing top-level platform navigation unchanged and restructure only the `settings` subdomain. Reuse current settings pages where possible, split the overloaded global settings page into focused pages, and normalize route labels, headers, and left-nav wording together so the domain reads as one coherent workspace.

**Tech Stack:** Vue 3, TypeScript, Vue Router, Element Plus, existing settings APIs in Django/DRF

---

### Task 1: Audit the Current Settings Domain and Lock the Route Map

**Files:**
- Modify: `frontend/src/router/index.ts`
- Reference: `frontend/src/pages/settings/SystemSettings.vue`
- Reference: `frontend/src/pages/settings/Users.vue`
- Reference: `frontend/src/pages/settings/Permissions.vue`
- Reference: `frontend/src/pages/settings/Alerts.vue`

**Step 1: Write the failing test**

Create or extend a router-oriented frontend test that asserts the settings nav labels and route meta labels use the new wording:

```ts
expect(settingsNavItems).toEqual([
  expect.objectContaining({ label: '平台配置', path: '/settings/platform' }),
  expect.objectContaining({ label: '用户与权限', path: '/settings/users' }),
  expect.objectContaining({ label: '通知管理', path: '/settings/notifications' }),
  expect.objectContaining({ label: '认证接入', path: '/settings/auth' }),
]);
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand <router test file>`

Expected: FAIL because current route map still uses `全局设置` and `告警`.

**Step 3: Write minimal implementation**

Update `frontend/src/router/index.ts`:

- replace `/settings/system` with `/settings/platform`
- replace `/settings/alerts` labels with `通知管理`
- add `/settings/auth` route placeholder
- keep permissions stable
- update route meta labels to match the new wording

Also keep backward-compat redirects if needed:

```ts
{ path: '/settings/system', redirect: '/settings/platform' }
{ path: '/settings/alerts', redirect: '/settings/notifications' }
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand <router test file>`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/router/index.ts <router test file>
git commit -m "refactor: reshape system settings route map"
```

### Task 2: Create a Dedicated Settings Navigation Source

**Files:**
- Create: `frontend/src/pages/settings/config/navigation.ts`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/pages/settings/components/SettingsRepositoryShell.vue`
- Test: `frontend/src/pages/settings/config/navigation.spec.ts`

**Step 1: Write the failing test**

Create a unit test that asserts the navigation source returns only the approved four groups and the correct children.

```ts
expect(buildSettingsNav()).toMatchObject([
  { key: 'platform', label: '平台配置' },
  { key: 'identity', label: '用户与权限' },
  { key: 'notifications', label: '通知管理' },
  { key: 'auth', label: '认证接入' },
]);
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/config/navigation.spec.ts`

Expected: FAIL because the navigation config file does not exist yet.

**Step 3: Write minimal implementation**

Create `frontend/src/pages/settings/config/navigation.ts` with a typed config such as:

```ts
export interface SettingsNavGroup {
  key: string;
  label: string;
  items: Array<{ label: string; routeName: string; permission?: string }>;
}
```

Populate it with:

- 平台配置
- 用户与权限
- 通知管理
- 认证接入

Refactor `frontend/src/router/index.ts` and `SettingsRepositoryShell.vue` to consume the same navigation source instead of duplicating labels.

**Step 4: Run test to verify it passes**

Run:

- `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/config/navigation.spec.ts`
- `cd /mnt/d/workspace/OneAll/frontend && npx vue-tsc --noEmit`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/settings/config/navigation.ts frontend/src/pages/settings/config/navigation.spec.ts frontend/src/router/index.ts frontend/src/pages/settings/components/SettingsRepositoryShell.vue
git commit -m "refactor: centralize settings navigation config"
```

### Task 3: Convert Global Settings into Platform Configuration

**Files:**
- Modify: `frontend/src/pages/settings/SystemSettings.vue`
- Modify: `frontend/src/pages/settings/components/SettingsTabs.vue`
- Optional Create: `frontend/src/pages/settings/components/PlatformSettingsForm.vue`
- Test: `frontend/src/pages/settings/__tests__/platform-settings.spec.ts`

**Step 1: Write the failing test**

Write a component test that renders the page and asserts only platform-level settings remain:

```ts
expect(screen.getByText('平台配置')).toBeInTheDocument();
expect(screen.queryByText('LDAP')).not.toBeInTheDocument();
expect(screen.queryByText('资产配置')).not.toBeInTheDocument();
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/__tests__/platform-settings.spec.ts`

Expected: FAIL because the current page still renders LDAP and asset sections.

**Step 3: Write minimal implementation**

Refactor `SystemSettings.vue` into a platform-configuration page:

- change section title from `全局设置` to `平台配置`
- keep only:
  - platform name
  - logo
  - timezone
  - theme
  - alert escalation threshold
  - certificate thresholds
- remove LDAP handling from the form UI
- remove asset settings UI from the page
- trim imports and local types that are no longer needed

If `SettingsTabs.vue` becomes an anti-pattern, split the kept sections into a new focused component instead of preserving tabs.

**Step 4: Run test to verify it passes**

Run:

- `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/__tests__/platform-settings.spec.ts`
- `cd /mnt/d/workspace/OneAll/frontend && npx vue-tsc --noEmit`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/settings/SystemSettings.vue frontend/src/pages/settings/components/SettingsTabs.vue frontend/src/pages/settings/components/PlatformSettingsForm.vue frontend/src/pages/settings/__tests__/platform-settings.spec.ts
git commit -m "refactor: split platform configuration from global settings"
```

### Task 4: Introduce a Dedicated Authentication Integration Page

**Files:**
- Create: `frontend/src/pages/settings/AuthIntegration.vue`
- Optional Create: `frontend/src/pages/settings/components/LdapSettingsForm.vue`
- Modify: `frontend/src/router/index.ts`
- Reuse: `frontend/src/services/settingsApi.ts`
- Test: `frontend/src/pages/settings/__tests__/auth-integration.spec.ts`

**Step 1: Write the failing test**

Write a component test that asserts the auth page renders LDAP fields and a sync action:

```ts
expect(screen.getByText('认证接入')).toBeInTheDocument();
expect(screen.getByLabelText('LDAP 主机')).toBeInTheDocument();
expect(screen.getByRole('button', { name: '同步 LDAP 用户' })).toBeInTheDocument();
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/__tests__/auth-integration.spec.ts`

Expected: FAIL because the page and route do not exist yet.

**Step 3: Write minimal implementation**

Create `AuthIntegration.vue` and move the LDAP UI and sync flow out of `SystemSettings.vue` into this page.

The page should:

- load `/settings/system` initially if no dedicated backend endpoint exists yet
- display LDAP connection fields
- preserve existing role-loading and sync behavior
- use the same page shell and fixed footer actions as other settings pages

**Step 4: Run test to verify it passes**

Run:

- `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/__tests__/auth-integration.spec.ts`
- `cd /mnt/d/workspace/OneAll/frontend && npx vue-tsc --noEmit`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/settings/AuthIntegration.vue frontend/src/pages/settings/components/LdapSettingsForm.vue frontend/src/router/index.ts frontend/src/pages/settings/__tests__/auth-integration.spec.ts
git commit -m "feat: add authentication integration settings page"
```

### Task 5: Rename Alerts in Settings to Notification Management

**Files:**
- Modify: `frontend/src/pages/settings/Alerts.vue`
- Modify: `frontend/src/pages/settings/AlertTemplates.vue`
- Modify: `frontend/src/pages/settings/AlertChannelDetail.vue`
- Modify: `frontend/src/router/index.ts`
- Test: `frontend/src/pages/settings/__tests__/notification-labels.spec.ts`

**Step 1: Write the failing test**

Write a test asserting settings pages use notification wording instead of alert wording:

```ts
expect(screen.getByText('通知管理')).toBeInTheDocument();
expect(screen.getByText('通知渠道')).toBeInTheDocument();
expect(screen.queryByText(/^告警$/)).not.toBeInTheDocument();
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/__tests__/notification-labels.spec.ts`

Expected: FAIL because the current labels still use `告警`.

**Step 3: Write minimal implementation**

Update settings-specific wording only:

- `系统设置 / 通知管理`
- `通知渠道`
- `通知模板`
- breadcrumb labels and button copy that still say `告警`

Do not change monitoring-domain alert wording.

**Step 4: Run test to verify it passes**

Run:

- `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/__tests__/notification-labels.spec.ts`
- `cd /mnt/d/workspace/OneAll/frontend && npx vue-tsc --noEmit`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/settings/Alerts.vue frontend/src/pages/settings/AlertTemplates.vue frontend/src/pages/settings/AlertChannelDetail.vue frontend/src/router/index.ts frontend/src/pages/settings/__tests__/notification-labels.spec.ts
git commit -m "refactor: rename settings alerts to notification management"
```

### Task 6: Normalize the Settings Shell for List and Config Pages

**Files:**
- Modify: `frontend/src/pages/settings/components/SettingsPageShell.vue`
- Modify: `frontend/src/pages/settings/components/SettingsRepositoryShell.vue`
- Modify: `frontend/src/components/RepositoryPageShell.vue`
- Test: `frontend/src/pages/settings/components/__tests__/settings-shell.spec.ts`

**Step 1: Write the failing test**

Add a shell test asserting:

- left settings navigation renders consistently
- config pages support a fixed bottom footer
- list pages preserve the standard toolbar/table/footer frame

```ts
expect(screen.getByText('平台配置')).toBeInTheDocument();
expect(screen.getByText('通知管理')).toBeInTheDocument();
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/components/__tests__/settings-shell.spec.ts`

Expected: FAIL because the shell does not yet provide the new shared nav model.

**Step 3: Write minimal implementation**

Refactor the shell components so that:

- the settings left navigation is rendered centrally
- config pages and list pages use the same section chrome
- spacing, footer height, and internal scroll behavior match the established frontend baseline

**Step 4: Run test to verify it passes**

Run:

- `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/components/__tests__/settings-shell.spec.ts`
- `cd /mnt/d/workspace/OneAll/frontend && npx vue-tsc --noEmit`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/settings/components/SettingsPageShell.vue frontend/src/pages/settings/components/SettingsRepositoryShell.vue frontend/src/components/RepositoryPageShell.vue frontend/src/pages/settings/components/__tests__/settings-shell.spec.ts
git commit -m "refactor: normalize system settings shell behaviors"
```

### Task 7: Keep Users and Permissions Under a Shared Domain Label

**Files:**
- Modify: `frontend/src/pages/settings/Users.vue`
- Modify: `frontend/src/pages/settings/Permissions.vue`
- Modify: `frontend/src/pages/settings/PermissionRoleDetail.vue`
- Test: `frontend/src/pages/settings/__tests__/users-permissions-labels.spec.ts`

**Step 1: Write the failing test**

Add tests that assert the pages present themselves as part of `用户与权限` rather than unrelated standalone pages.

```ts
expect(screen.getByText('用户与权限')).toBeInTheDocument();
expect(screen.getByText('用户管理')).toBeInTheDocument();
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/__tests__/users-permissions-labels.spec.ts`

Expected: FAIL because the current pages still use old section-only wording.

**Step 3: Write minimal implementation**

Update:

- page titles
- breadcrumbs
- section subtitles

so users, roles, and permission pages all clearly belong to `用户与权限`.

Do not redesign workflows in this task; only normalize domain framing.

**Step 4: Run test to verify it passes**

Run:

- `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand frontend/src/pages/settings/__tests__/users-permissions-labels.spec.ts`
- `cd /mnt/d/workspace/OneAll/frontend && npx vue-tsc --noEmit`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/settings/Users.vue frontend/src/pages/settings/Permissions.vue frontend/src/pages/settings/PermissionRoleDetail.vue frontend/src/pages/settings/__tests__/users-permissions-labels.spec.ts
git commit -m "refactor: align users and permissions domain labels"
```

### Task 8: Regression Pass and Manual Verification

**Files:**
- Modify if needed: `frontend/src/router/index.ts`
- Modify if needed: affected settings pages under `frontend/src/pages/settings/`

**Step 1: Write the failing test**

Add or update a smoke test that mounts each settings route and verifies the header renders without crashing.

```ts
for (const route of settingsRoutes) {
  await router.push(route);
  expect(screen.getByText('系统设置')).toBeInTheDocument();
}
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand <settings smoke test file>`

Expected: FAIL if any route still points to removed labels or components.

**Step 3: Write minimal implementation**

Fix any leftover:

- route names
- redirects
- breadcrumbs
- stale labels
- page-shell assumptions

**Step 4: Run test to verify it passes**

Run:

- `cd /mnt/d/workspace/OneAll/frontend && npm test -- --runInBand <settings smoke test file>`
- `cd /mnt/d/workspace/OneAll/frontend && npx vue-tsc --noEmit`

Optional manual pass:

- open `/settings/platform`
- open `/settings/users`
- open `/settings/permissions`
- open `/settings/notifications`
- open `/settings/auth`

Expected: all pages render with coherent system-settings framing.

**Step 5: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/pages/settings
git commit -m "test: complete system settings redesign regression pass"
```

## Notes for Execution

- Do not move asset model or field administration back into system settings.
- Keep backend API changes minimal unless LDAP splitting requires a dedicated endpoint.
- If backend splitting is needed, add it as a follow-up task after frontend structure is stable.
- Preserve current permissions and authorization checks during renaming.
