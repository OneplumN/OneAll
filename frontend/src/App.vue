<template>
  <a
    class="skip-link"
    href="#main-content"
  >
    {{ t('common.skipToContent') }}
  </a>
  <router-view v-slot="{ Component, route: currentRoute }">
    <Suspense>
      <template #default>
        <component
          :is="layoutComponent(currentRoute)"
          id="main-content"
        >
          <component :is="Component" />
        </component>
      </template>
      <template #fallback>
        <component
          :is="layoutComponent(currentRoute)"
          id="main-content"
        >
          <PageLoader />
        </component>
      </template>
    </Suspense>
  </router-view>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

import MainLayout from '@/layouts/MainLayout.vue';
import PageLoader from '@/shared/components/feedback/PageLoader';
import { useBrandingStore } from '@/app/stores/branding';

const { t, locale } = useI18n();
const branding = useBrandingStore();
const route = useRoute();
const groupLabelMap: Record<string, string> = {
  oneoff: '一次性检验',
  request: '工单申请',
  assets: '资产中心',
  tools: '运维工具',
  alerts: '监控与告警',
  settings: '系统设置',
  probes: '节点管理',
};

function layoutComponent(route: { meta?: Record<string, unknown> }) {
  return route.meta && route.meta.requiresAuth ? MainLayout : 'div';
}

onMounted(() => {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale.value;
  }
  branding.fetchBranding();
});

watch(
  () => locale.value,
  (value) => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = value;
    }
  },
);

watch(
  () => [branding.platformLogo, branding.platformName] as const,
  ([platformLogo, platformName]) => {
    if (typeof document === 'undefined') {
      return;
    }
    const head = document.head;
    let favicon = head.querySelector<HTMLLinkElement>('link[rel="icon"]');
    if (!favicon) {
      favicon = document.createElement('link');
      favicon.rel = 'icon';
      head.appendChild(favicon);
    }
    favicon.href = platformLogo || buildFallbackFavicon(platformName || 'OneAll');
  },
  { immediate: true },
);

watch(
  () => [route.fullPath, branding.platformName] as const,
  () => {
    if (typeof document === 'undefined') {
      return;
    }
    const base = branding.platformName || '多维运维平台';
    const navGroup = typeof route.meta?.navGroup === 'string' ? route.meta.navGroup : '';
    const navLabel = typeof route.meta?.navLabel === 'string' ? route.meta.navLabel : '';
    const explicitTitle = typeof route.meta?.title === 'string' ? route.meta.title : '';
    const groupLabel = navGroup ? groupLabelMap[navGroup] || '' : '';
    const pageTitle = explicitTitle || [groupLabel, navLabel].filter(Boolean).join(' - ');
    if (pageTitle) {
      document.title = `${pageTitle} · ${base}`;
    }
  },
  { immediate: true },
);

function buildFallbackFavicon(platformName: string): string {
  const token = (platformName || 'OneAll').trim().slice(0, 2).toUpperCase();
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
      <rect width="64" height="64" rx="16" fill="#0f172a" />
      <rect x="8" y="8" width="48" height="48" rx="12" fill="#2563eb" />
      <text x="32" y="39" font-size="20" text-anchor="middle" fill="#ffffff" font-family="Arial, sans-serif" font-weight="700">${token}</text>
    </svg>
  `;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}
</script>

<style>
:root {
  color-scheme: light;
}

html,
body,
#app {
  height: 100%;
  margin: 0;
}

.skip-link {
  position: absolute;
  top: -40px;
  left: 16px;
  z-index: 1000;
  padding: 8px 16px;
  background: #1d8cf8;
  color: #fff;
  border-radius: 4px;
  transition: top 0.2s ease;
}

.skip-link:focus {
  top: 16px;
  outline: 2px solid #fff;
}

main {
  min-height: 100%;
}
</style>
