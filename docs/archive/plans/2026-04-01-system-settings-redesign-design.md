# System Settings Redesign Design

**Date:** 2026-04-01

## Background

The current `系统设置` domain mixes two different product models:

- `全局设置` is a dense configuration form that contains platform basics, LDAP, thresholds, notification settings, and asset-related settings in one page.
- `用户` and `告警` already behave like operational admin workspaces with list, filter, table, and detail flows.

This creates a domain-definition problem rather than a visual problem. The same area is simultaneously used as:

- a platform configuration center
- an operational administration center

That mismatch makes the settings area difficult to extend cleanly.

## Goal

Refactor `系统设置` into a stable **platform administration domain** that only carries platform-level governance capabilities.

The redesign should:

- remove the "global settings mega-form" pattern
- keep system-level configuration and administration inside the domain
- keep business-domain configuration out of system settings
- make existing pages feel like one coherent settings workspace

## Domain Boundary

`系统设置` should own only platform-level concerns:

1. `平台配置`
2. `用户与权限`
3. `通知管理`
4. `认证接入`

The following do **not** belong in `系统设置`:

- asset model management
- asset field management
- asset sync scripts
- asset unique-key rules

Those remain inside `资产中心`, where they already belong as asset-domain metadata management.

## Information Architecture

The system settings left navigation should be reduced to four top-level items:

1. `平台配置`
2. `用户与权限`
3. `通知管理`
4. `认证接入`

### 1. 平台配置

Owns true platform-wide defaults and branding:

- platform name
- platform logo
- default timezone
- theme
- global alert escalation threshold
- default certificate thresholds

This page replaces the current overloaded `全局设置` page.

### 2. 用户与权限

Owns identity and authorization administration:

- user management
- role templates
- permission matrix

Current `Users.vue` becomes the first page under this area.
Current `Permissions.vue` and `PermissionRoleDetail.vue` remain in this area.

### 3. 通知管理

Owns notification infrastructure, not monitoring business events:

- notification channels
- notification templates
- default notification configuration

Current `Alerts.vue`, `AlertTemplates.vue`, and `AlertChannelDetail.vue` remain here, but the domain wording must change from `告警` to `通知管理` to avoid conflict with the monitoring/alerts domain.

### 4. 认证接入

Owns external authentication and directory integration:

- LDAP configuration
- default LDAP role mapping
- LDAP sync entry points

LDAP must be split out of the current `全局设置` page and become its own page.

## Page Model

The settings domain should support only two page types.

### List-type pages

Used for:

- users
- roles
- permission list
- notification channels
- templates
- audit logs

Shared layout:

- top header + action area
- single-row toolbar
- centered table panel
- bottom stats / pagination

### Configuration-type pages

Used for:

- platform configuration
- LDAP configuration
- default notification configuration

Shared layout:

- settings navigation on the left
- single main form workspace on the right
- fixed bottom action bar

This intentionally removes the current mixed tab-and-card mega-form pattern.

## Existing Page Migration

### Keep and Reframe

- `frontend/src/pages/settings/Users.vue`
  - stays under `用户与权限`
- `frontend/src/pages/settings/Permissions.vue`
  - stays under `用户与权限`
- `frontend/src/pages/settings/PermissionRoleDetail.vue`
  - stays under `用户与权限`
- `frontend/src/pages/settings/AuditLogViewer.vue`
  - remains a system settings utility page; it can stay under `用户与权限` or remain hidden from primary nav in this phase
- `frontend/src/pages/settings/Alerts.vue`
  - becomes `通知渠道`
- `frontend/src/pages/settings/AlertTemplates.vue`
  - becomes `通知模板`
- `frontend/src/pages/settings/AlertChannelDetail.vue`
  - remains detail/config page for a notification channel

### Split and Replace

- `frontend/src/pages/settings/SystemSettings.vue`
  - slim down into `平台配置`
  - remove LDAP and asset-related settings

### New Page

- new LDAP settings page under `认证接入`
  - receives LDAP config fields and sync actions now embedded inside `SystemSettings.vue`

## Naming Rules

The following naming changes are required to stabilize domain language:

- `全局设置` -> `平台配置`
- `告警` inside system settings -> `通知管理`
- `告警通道` in system settings context -> `通知渠道`

This is important because the platform already has a separate alerts domain for monitoring events and strategies.

## Navigation Strategy

This redesign does not reopen top-level platform navigation.

The top navigation remains unchanged.
Only the structure inside the `系统设置` domain is refactored.

That keeps the platform IA stable while cleaning up the settings subdomain.

## Delivery Strategy

Implementation should proceed in this order:

1. refactor the settings navigation shell
2. split `平台配置` from the current global settings page
3. split `认证接入` into its own LDAP page
4. rename and normalize `通知管理`
5. keep `用户与权限` in place and tighten naming/layout consistency

## Risks

### 1. Concept drift

If labels are only partially updated, users will still see:

- `全局设置`
- `告警`
- `通知管理`

at the same time. That would recreate confusion immediately.

### 2. Route inconsistency

If routes, page headers, nav labels, and detail-page breadcrumbs are not updated together, the redesign will feel like a patch instead of a coherent subsystem.

### 3. Boundary regression

Asset-related model management must not be reintroduced into system settings later. That would break the domain boundary again.

## Non-Goals

This redesign does not include:

- redesigning top-level platform navigation
- moving asset metadata management back into system settings
- redesigning monitoring/alerts/probes information architecture
- changing backend settings APIs beyond what is needed to split pages cleanly

## Recommended First Execution Slice

The highest-value first slice is:

1. rebuild the system settings shell and left navigation
2. convert `SystemSettings.vue` into `平台配置`

That immediately changes the settings domain from a mixed configuration area into a structured platform administration area while keeping risk low.
