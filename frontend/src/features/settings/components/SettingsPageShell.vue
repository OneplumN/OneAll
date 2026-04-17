<template>
  <RepositoryPageShell
    root-title="系统设置"
    :section-title="sectionTitle"
    :breadcrumb="breadcrumb"
    :body-padding="bodyPadding"
    :panel-bordered="panelBordered"
    :scroll-mode="scrollMode"
  >
    <template #actions>
      <slot name="actions" />
    </template>
    <div
      v-if="secondaryNavItems.length"
      class="settings-secondary-nav"
    >
      <button
        v-for="item in secondaryNavItems"
        :key="item.path"
        type="button"
        class="settings-secondary-nav__item"
        :class="{ 'is-active': isSecondaryActive(item) }"
        @click="goSecondary(item.path)"
      >
        {{ item.label }}
      </button>
    </div>
    <slot />
    <template
      v-if="$slots.footer"
      #footer
    >
      <slot name="footer" />
    </template>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import { SETTINGS_SECONDARY_NAV_ITEMS, type SettingsSecondaryNavItem } from '@/features/settings/config/navigation';
import { useSessionStore } from '@/app/stores/session';

const props = withDefaults(
  defineProps<{
    sectionTitle: string;
    breadcrumb?: string;
    bodyPadding?: string;
    panelBordered?: boolean;
    scrollMode?: 'panel' | 'page';
  }>(),
  {
    breadcrumb: '',
    bodyPadding: '16px',
    panelBordered: true,
    scrollMode: 'panel',
  }
);

const route = useRoute();
const router = useRouter();
const sessionStore = useSessionStore();

const secondaryNavItems = computed(() =>
  (SETTINGS_SECONDARY_NAV_ITEMS[props.sectionTitle] || []).filter(
    (item) => !item.permission || sessionStore.hasPermission(item.permission)
  )
);

const isSecondaryActive = (item: SettingsSecondaryNavItem) => {
  const activePaths = item.activePaths || [item.path];
  return activePaths.some((path) => route.path.startsWith(path));
};

const goSecondary = (path: string) => {
  if (route.path === path) return;
  router.push(path);
};
</script>

<style scoped>
.settings-secondary-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 0 16px 12px;
}

.settings-secondary-nav__item {
  border: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
  color: var(--oa-text-secondary);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: var(--oa-font-subtitle);
  line-height: 1.2;
  cursor: pointer;
  transition: border-color 0.15s ease, color 0.15s ease, background-color 0.15s ease;
}

.settings-secondary-nav__item:hover {
  border-color: var(--oa-color-primary-light);
  color: var(--oa-color-primary);
}

.settings-secondary-nav__item.is-active {
  border-color: var(--oa-color-primary);
  background: color-mix(in srgb, var(--oa-color-primary) 8%, white);
  color: var(--oa-color-primary);
  font-weight: 600;
}
</style>
