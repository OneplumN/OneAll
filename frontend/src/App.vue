<template>
  <a class="skip-link" href="#main-content">{{ t('common.skipToContent') }}</a>
  <router-view v-slot="{ Component, route }">
    <Suspense>
      <template #default>
        <component
          :is="layoutComponent(route)"
          id="main-content"
        >
          <component :is="Component" />
        </component>
      </template>
      <template #fallback>
        <component
          :is="layoutComponent(route)"
          id="main-content"
        >
          <PageLoader />
        </component>
      </template>
    </Suspense>
  </router-view>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

import MainLayout from '@/layouts/MainLayout.vue';
import PageLoader from '@/components/common/PageLoader.vue';
import { useBrandingStore } from '@/stores/branding';

const { t, locale } = useI18n();
const branding = useBrandingStore();

function layoutComponent(route: { meta?: Record<string, unknown> }) {
  return route.meta && route.meta.requiresAuth ? MainLayout : 'div';
}

onMounted(() => {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale.value;
  }
  branding.fetchBranding();
});
</script>

<style>
:root {
  color-scheme: light;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background-color: #f5f7fa;
  color: #303133;
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
