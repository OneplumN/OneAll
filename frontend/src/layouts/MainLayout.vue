<template>
  <div class="layout" :style="{ '--aside-width': asideWidth }">
    <header class="layout__top">
      <div class="top-brand">
        <div class="brand">
          <div class="brand__logo">
            <img v-if="branding.platformLogo" class="logo-image" :src="branding.platformLogo" alt="logo" />
            <div v-else class="logo-icon">OA</div>
          </div>
          <div class="brand__text">
            <span class="brand__title">{{ branding.platformName }}</span>
            <small class="brand__subtitle">控制台</small>
          </div>
        </div>
      </div>
      <div class="top-nav-wrapper">
         <el-menu
          :key="activeGroup?.key ?? 'top-nav'"
          mode="horizontal"
          :default-active="activeGroup?.key"
          class="layout__top-menu"
          :ellipsis="false"
          @select="handleTopSelect"
        >
          <el-menu-item
            v-for="item in topMenuItems"
            :key="item.key"
            :index="item.key"
          >
            {{ item.label }}
          </el-menu-item>
        </el-menu>
      </div>

      <div class="top-right">
        <el-tooltip
          placement="bottom"
          :content="isDarkTheme ? '切换浅色模式' : '切换深色模式'"
        >
          <button
            type="button"
            class="theme-toggle"
            :aria-label="isDarkTheme ? '切换浅色模式' : '切换深色模式'"
            @click="toggleTheme"
          >
            <el-icon class="theme-toggle__icon">
              <component :is="isDarkTheme ? Sunny : Moon" />
            </el-icon>
          </button>
        </el-tooltip>

        <el-dropdown trigger="click" @command="handleUserCommand">
          <div class="user-info">
            <el-avatar shape="circle" :size="32" class="user-info__avatar">
              {{ userInitial }}
            </el-avatar>
            <div class="user-info__text">
              <span class="user-info__name">{{ userName }}</span>
            </div>
            <el-icon class="user-info__chevron">
              <ArrowDown />
            </el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu class="user-dropdown">
              <div class="user-dropdown__header">
                <div class="user-name">{{ userName }}</div>
                <div class="user-role">{{ userRole }}</div>
              </div>
              <el-dropdown-item command="profile" :icon="User">个人资料</el-dropdown-item>
              <el-dropdown-item divided command="logout" :icon="SwitchButton">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <div class="layout__below">
      <aside
        v-if="hasSideNav"
        class="layout__aside"
        :style="{ width: asideWidth }"
      >
        <div class="layout__aside-scroll">
          <el-menu
            :default-active="activeSidePath"
            :collapse="isCollapsed"
            :collapse-transition="false"
            class="layout__menu"
            router
          >
            <template v-if="sideNavItems.length">
              <template v-for="item in sideNavItems" :key="item.key">
                <el-tooltip
                  v-if="item.path"
                  :key="item.key"
                  class="nav-entry__tooltip"
                  effect="dark"
                  placement="right"
                  :content="item.label"
                  :disabled="!isCollapsed"
                  popper-class="layout__nav-tooltip-popper"
                >
                  <el-menu-item
                    :index="item.path"
                    class="nav-entry"
                  >
                    <div v-if="item.icon" class="nav-entry__icon">
                      <component :is="item.icon" />
                    </div>
                    <div v-else class="nav-entry__badge">{{ item.badge }}</div>
                    <span class="nav-entry__label">{{ item.label }}</span>
                  </el-menu-item>
                </el-tooltip>
                <template v-if="item.children?.length && !isCollapsed">
                  <div class="nav-group-title">{{ item.label }}</div>
                  <el-menu-item
                    v-for="child in item.children"
                    :key="child.key"
                    :index="child.path"
                    class="nav-entry nav-entry--child"
                  >
                    <div
                      v-if="child.icon"
                      class="nav-entry__icon nav-entry__icon--child"
                    >
                      <component :is="child.icon" />
                    </div>
                    <span class="nav-entry__label">{{ child.label }}</span>
                  </el-menu-item>
                </template>
              </template>
            </template>
            <template v-else>
              <el-menu-item :index="activeTopPath" class="nav-entry">
                <div class="nav-entry__badge">{{ badgeFromLabel(activeGroup?.label || '首页') }}</div>
                <span class="nav-entry__label">{{ activeGroup?.label || '首页' }}</span>
              </el-menu-item>
            </template>
          </el-menu>
        </div>

        <div class="aside__footer">
          <el-button
            class="layout__toggle"
            text
            @click="toggleCollapse"
          >
            <el-icon>
              <component :is="isCollapsed ? Expand : Fold" />
            </el-icon>
          </el-button>
        </div>
      </aside>

      <main
        :class="[
          'layout__main',
          {
            'layout__main--flat': isFlatContent,
            'layout__main--full': !hasSideNav,
            'layout__main--no-scroll': lockMainScroll
          }
        ]"
        :style="mainPaddingStyle"
      >
        <div
          :class="['layout__content-wrapper', { 'layout__content-wrapper--flat': isFlatContent }]"
          :style="contentPaddingStyle"
        >
          <div :class="['layout__content', { 'layout__content--flat': isFlatContent }]">
            <PluginAvailabilityGate
              :plugin-type="currentPluginType"
              :script-plugin="currentScriptPlugin"
              message="该功能暂未开放，正在建设中"
            >
              <transition name="fade-slide" mode="out-in">
                <slot />
              </transition>
            </PluginAvailabilityGate>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue';
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import {
  ArrowDown,
  Bell,
  Brush,
  Collection,
  CollectionTag,
  Compass,
  Connection,
  DataAnalysis,
  DataBoard,
  DataLine,
  Document,
  DocumentAdd,
  DocumentChecked,
  Expand,
  Fold,
  Grid,
  Histogram,
  Link,
  Lock,
  Monitor,
  Notebook,
  Operation,
  Reading,
  Setting,
  SwitchButton,
  Moon,
  Sunny,
  Timer,
  Tools,
  TrendCharts,
  User
} from '@element-plus/icons-vue';
import { storeToRefs } from 'pinia';

import { NAV_GROUPS } from '@/router';
import { useAppStore } from '@/stores/app';
import { useSessionStore } from '@/stores/session';
import { useBrandingStore } from '@/stores/branding';
import { useThemeStore } from '@/stores/theme';
import { usePluginConfigStore } from '@/stores/pluginConfigs';
import { useCodeDirectoryStore } from '@/stores/codeDirectories';
import PluginAvailabilityGate from '@/components/PluginAvailabilityGate.vue';

type SideNavEntry = {
  key: string;
  label: string;
  path: string;
  badge: string;
  icon?: Component;
  children?: SideNavEntry[];
};

const route = useRoute();
const router = useRouter();
const collapseState = ref<Record<string, boolean>>({});
const appStore = useAppStore();
const sessionStore = useSessionStore();
const branding = useBrandingStore();
const themeStore = useThemeStore();
const pluginConfigStore = usePluginConfigStore();
const codeDirectoryStore = useCodeDirectoryStore();
const { user, accessToken } = storeToRefs(sessionStore);
const { mode: themeMode } = storeToRefs(themeStore);

const isDarkTheme = computed(() => themeMode.value === 'dark');

function toggleTheme() {
  themeStore.toggle();
}

const isCollapsed = computed(() => collapseState.value[activeGroup.value?.key ?? 'default'] ?? false);
const canAccess = (permission?: string) => sessionStore.hasPermission(permission);

const contentPaddingStyle = computed(() => {
  const overridePadding = route.meta?.contentPadding as string | undefined;
  if (isFlatContent.value) {
    return {};
  }
  if (overridePadding) {
    return { padding: overridePadding };
  }
  return { padding: '24px' };
});

const mainPaddingStyle = computed(() => {
  if (isFlatContent.value) return {};
  const overridePadding = route.meta?.contentPadding as string | undefined;
  if (overridePadding) return {};
  return { padding: '24px' };
});
const canAccessGroup = (group: typeof NAV_GROUPS[number]) => !group.permission || canAccess(group.permission);

const accessibleGroups = computed(() => {
  const filtered = NAV_GROUPS.filter(canAccessGroup);
  return filtered.length ? filtered : NAV_GROUPS;
});

const isItemVisible = (item: any) => {
  if (item.hidden) return false;
  if (item.permission && !canAccess(item.permission)) return false;
  return true;
};

const firstPathForItem = (item: any) => {
  if (!item || !isItemVisible(item)) return undefined;
  if (item.path) return item.path;
  const child = item.children?.find((child: any) => isItemVisible(child)) ?? item.children?.find((child: any) => canAccess(child.permission));
  return child?.path;
};

const firstVisiblePath = (groupKey: string) => {
  const group = NAV_GROUPS.find((item) => item.key === groupKey);
  const target = group?.items.find(isItemVisible) ?? group?.items[0];
  return firstPathForItem(target) ?? '/';
};

const topMenuItems = computed(() =>
  accessibleGroups.value.map((group) => ({ key: group.key, label: group.label, path: firstVisiblePath(group.key) }))
);

const activeGroup = computed(() => {
  // 优先使用路由 meta 声明的 navGroup，避免不同前缀的误判
  const metaGroup = (route.meta as any)?.navGroup as string | undefined;
  if (metaGroup) {
    const found = accessibleGroups.value.find((group) => group.key === metaGroup);
    if (found) return found;
  }

  const path = route.path;
  return (
    accessibleGroups.value.find((group) =>
      group.items.some((item) => {
        if (item.hidden) return false;
        if (item.path) return path.startsWith(item.path);
        return item.children?.some((child) => !child.hidden && child.path && path.startsWith(child.path));
      })
    ) ?? accessibleGroups.value[0]
  );
});

const activeTopPath = computed(() => {
  const target = activeGroup.value?.items.find(isItemVisible)
    ?? activeGroup.value?.items[0];
  return firstPathForItem(target) ?? '/';
});

const badgeFromLabel = (label: string) => {
  if (!label) return '#';
  const alphanumeric = label.match(/[A-Za-z0-9]/);
  if (alphanumeric && alphanumeric[0]) {
    return alphanumeric[0].toUpperCase();
  }
  return label.charAt(0);
};

const SIDE_NAV_ICONS: Record<string, Component> = {
  '/monitoring/overview': DataLine,
  '/monitoring/probes': Monitor,
  '/monitoring/zabbix': DataBoard,
  '/monitoring/prometheus': TrendCharts,
  '/oneoff/domain': Operation,
  '/oneoff/certificate': DocumentChecked,
  '/oneoff/cmdb': CollectionTag,
  '/monitoring/request': DocumentAdd,
  '/analytics/detection': Histogram,
  '/analytics/assets': DataAnalysis,
  '/assets/domain': Notebook,
  '/assets/zabbix': Grid,
  '/assets/ipmp': DataAnalysis,
  '/assets/workorder-hosts': Collection,
  '/tools/ip-regex': Tools,
  '/tools/account-sync': Link,
  '/tools/grafana-sync': TrendCharts,
  '/code/repository': Reading,
  '/integrations': Connection,
  '/integrations/monitoring': Monitor,
  '/integrations/detection': Operation,
  '/integrations/reports': Histogram,
  '/integrations/assets': Grid,
  '/integrations/tools': Tools,
  '/probes/nodes': Compass,
  '/probes/schedules': Timer,
  '/probes/logs': Document,
  '/knowledge': Reading,
  '/settings/users': User,
  '/settings/permissions': Lock,
  '/settings/logs': Document,
  '/settings/alerts': Bell,
  '/settings/theme': Brush,
  '/settings/system': Setting
};

const resolveNavIcon = (path?: string) => {
  if (!path) return undefined;
  return SIDE_NAV_ICONS[path];
};

const buildChildEntries = (node: any): SideNavEntry[] | undefined => {
  if (!node.children?.length) return undefined;
  const nodes = node.children
    .filter((child: any) => isItemVisible(child) && Boolean(child.path))
    .map((child: any) => ({
      key: child.path!,
      label: child.label,
      path: child.path!,
      badge: badgeFromLabel(child.label),
      icon: resolveNavIcon(child.path),
    }));
  return nodes.length ? nodes : undefined;
};

const sideNavItems = computed<SideNavEntry[]>(() => {
  const group = activeGroup.value;
  if (!group) return [];
  const entries: SideNavEntry[] = [];
  group.items.forEach((item) => {
    if (!isItemVisible(item)) return;
    if (item.children?.length) {
      item.children
        .filter((child: any) => isItemVisible(child) && Boolean(child.path))
        .forEach((child: any) => {
          entries.push({
            key: child.path!,
            label: child.label,
            path: child.path!,
            badge: badgeFromLabel(child.label),
            icon: resolveNavIcon(child.path),
            children: buildChildEntries(child),
          });
        });
      return;
    }
    if (item.path) {
      entries.push({
        key: item.path,
        label: item.label,
        path: item.path,
        badge: badgeFromLabel(item.label),
        icon: resolveNavIcon(item.path),
        children: buildChildEntries(item),
      });
    }
  });
  if (group.key === 'code' && codeDirectoryStore.directories.length) {
    codeDirectoryStore.directories.forEach((directory) => {
      entries.push({
        key: `/code/repository/${directory.key}`,
        label: directory.title,
        path: `/code/repository/${directory.key}`,
        badge: badgeFromLabel(directory.title),
      });
    });
  }
  return entries;
});

const hasSideNav = computed(() => !((route.meta as any)?.hideSideNav));

const activeSidePath = computed(() => {
  const current = route.path;
  for (const item of sideNavItems.value) {
    if (current.startsWith(item.path)) return item.path;
    const child = item.children?.find((child) => current.startsWith(child.path));
    if (child) return child.path;
  }
  const first = sideNavItems.value[0];
  if (first) {
    if (first.path) return first.path;
    if (first.children?.length) return first.children[0].path;
  }
  return activeTopPath.value;
});

const asideWidth = computed(() => {
  if (!hasSideNav.value) return '0px';
  return isCollapsed.value ? '72px' : '240px';
});

const currentPluginType = computed(() => route.meta.pluginType as string | undefined);
const currentScriptPlugin = computed(() => route.meta.scriptPlugin as string | undefined);
const isFlatContent = computed(() => Boolean(route.meta?.layoutFlat));
const lockMainScroll = computed(() => Boolean(route.meta?.lockMainScroll) || appStore.mainScrollLocked);

const userName = computed(() => user.value?.display_name || user.value?.username || '访客');
const userInitial = computed(() => userName.value.slice(0, 1).toUpperCase());
const userRole = computed(() => (user.value?.roles?.[0] ? user.value.roles[0] : '当前用户'));

onMounted(() => {
  pluginConfigStore.fetchPluginConfigs().catch(() => undefined);
});

onMounted(() => {
  if (!user.value && accessToken.value) {
    sessionStore.fetchProfile().catch(() => undefined);
  }
  pluginConfigStore.fetchPluginConfigs();
});

onMounted(() => {
  if (!codeDirectoryStore.directories.length) {
    codeDirectoryStore.fetchDirectories().catch(() => undefined);
  }
});

function handleUserCommand(command: string) {
  if (command === 'logout') {
    sessionStore.logout();
    router.push('/login');
    return;
  }
  if (command === 'profile') {
    router.push('/profile');
  }
}

function toggleCollapse() {
  if (!activeGroup.value) return;
  collapseState.value = {
    ...collapseState.value,
    [activeGroup.value.key]: !isCollapsed.value,
  };
}

function handleTopSelect(key: string) {
  const group = NAV_GROUPS.find((item) => item.key === key);
  const target = group?.items.find((item) => !item.hidden) ?? group?.items[0];
  if (target) {
    const path = target.path || target.children?.find((child) => !child.hidden)?.path;
    if (path) {
      router.push(path);
    }
  }
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--oa-bg-body);
  overflow: hidden;
}

.layout__below {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.layout__aside {
  flex-shrink: 0;
  background: var(--oa-bg-surface);
  border-right: 1px solid var(--oa-border-light);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.layout__aside-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 0;
}

/* Custom Scrollbar for sidebar */
.layout__aside-scroll::-webkit-scrollbar {
  width: 4px;
}

.layout__aside-scroll::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 4px;
}

.layout__aside-scroll:hover::-webkit-scrollbar-thumb {
  background: var(--oa-border-light);
}

.layout__menu {
  border-right: none;
  background: transparent;
}

.layout__menu :deep(.el-menu-item) {
  height: 40px;
  line-height: 40px;
  border-radius: 6px;
  margin-bottom: 4px;
  color: var(--oa-text-secondary);
  font-weight: 500;
}

.layout__menu :deep(.el-menu-item:hover) {
  background-color: var(--oa-bg-muted);
  color: var(--oa-text-primary);
}

.layout__menu :deep(.el-menu-item.is-active) {
  background-color: #eff6ff; /* Blue 50 */
  color: var(--oa-color-primary);
}

.nav-entry {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-entry__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  width: 20px;
  color: var(--oa-text-muted);
  transition: color 0.2s;
}

.layout__menu :deep(.el-menu-item.is-active) .nav-entry__icon {
  color: var(--oa-color-primary);
}

.nav-entry__label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-group-title {
  padding: 16px 12px 8px;
  font-size: 11px;
  text-transform: uppercase;
  color: var(--oa-text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
}

.aside__footer {
  padding: 12px;
  border-top: 1px solid var(--oa-border-color);
  display: flex;
  justify-content: flex-end;
}

.layout__toggle {
  width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--oa-text-muted);
}

.layout__toggle:hover {
  color: var(--oa-text-primary);
  background: var(--oa-bg-muted);
}

.layout__top {
  height: 64px;
  background: var(--oa-bg-panel);
  border-bottom: 1px solid var(--oa-border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 10;
}

.top-nav-wrapper {
  flex: 1;
  min-width: 0;
}

.layout__top-menu {
  border-bottom: none;
  background: transparent;
}

.layout__top-menu :deep(.el-menu-item) {
  height: 64px;
  line-height: 64px;
  font-weight: 500;
  color: var(--oa-text-secondary);
  background: transparent !important;
  border-bottom: 2px solid transparent;
}

.layout__top-menu :deep(.el-menu-item:hover) {
  color: var(--oa-text-primary);
}

.layout__top-menu :deep(.el-menu-item.is-active) {
  color: var(--oa-text-primary);
  border-bottom-color: var(--oa-color-primary);
}

.top-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-toggle {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  border: 1px solid var(--oa-border-color);
  background: var(--oa-bg-panel);
  color: var(--oa-text-primary);
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.theme-toggle:hover {
  background: var(--oa-bg-muted);
  border-color: var(--oa-border-color-dark);
  transform: translateY(-1px);
}

.theme-toggle__icon {
  font-size: 16px;
}

.top-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 220px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
  white-space: nowrap;
}

.brand__logo {
  flex-shrink: 0;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--oa-color-primary), var(--oa-color-primary-dark));
  border-radius: 8px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
}

.logo-image {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  object-fit: cover;
  display: block;
}

.brand__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.1;
}

.brand__title {
  font-size: 18px;
  font-weight: 700;
  color: var(--oa-text-primary);
  letter-spacing: -0.02em;
}

.brand__subtitle {
  font-size: 12px;
  color: var(--oa-text-muted);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-info:hover {
  background: var(--oa-bg-muted);
}

.user-info__avatar {
  background: #eff6ff;
  color: var(--oa-color-primary);
  font-weight: 600;
  font-size: 13px;
}

.user-info__name {
  font-size: 14px;
  font-weight: 500;
  color: var(--oa-text-primary);
}

.user-info__chevron {
  font-size: 12px;
  color: var(--oa-text-muted);
}

.layout__main {
  flex: 1;
  min-width: 0;
  padding: 0;
  background: var(--oa-bg-body);
  overflow-y: auto;
  scrollbar-gutter: stable;
  box-sizing: border-box;
}

.layout__main--no-scroll {
  overflow: hidden;
}

.layout__main--full {
  margin-left: 0;
}

.layout__main--flat {
  padding: 0;
  background: var(--oa-bg-panel);
}

.layout__content-wrapper {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0;
}

.layout__content-wrapper--flat {
  max-width: 100%;
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.layout__content {
  background: transparent;
  border-radius: 0;
  padding: 0;
}

.layout__content--flat {
  padding: 0;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* Transitions */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.user-dropdown__header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--oa-border-color);
  margin-bottom: 4px;
}

.user-name {
  font-weight: 600;
  color: var(--oa-text-primary);
}

.user-role {
  font-size: 12px;
  color: var(--oa-text-muted);
  margin-top: 2px;
}
</style>
