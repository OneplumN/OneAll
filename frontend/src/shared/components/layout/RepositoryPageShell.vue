<template>
  <div :class="['repository-shell', { 'repository-shell--page-scroll': scrollMode === 'page' }]">
    <div class="repository-header">
      <div class="repository-header__info">
        <span class="header__title">{{ rootTitle }}</span>
        <template v-if="sectionTitle">
          <span class="header__separator">/</span>
          <span class="header__subtitle">{{ sectionTitle }}</span>
        </template>
        <template v-if="breadcrumb">
          <span class="header__separator">/</span>
          <span class="header__subtitle">{{ breadcrumb }}</span>
        </template>
        <slot name="info-extra" />
      </div>
      <div class="repository-header__actions">
        <slot name="actions" />
      </div>
    </div>

    <section :class="['page-panel', { 'page-panel--borderless': !panelBordered }]">
      <div class="page-panel__body">
        <slot />
      </div>
      <footer
        v-if="$slots.footer"
        class="page-panel__footer"
      >
        <slot name="footer" />
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    rootTitle: string;
    sectionTitle?: string;
    breadcrumb?: string;
    panelBordered?: boolean;
    scrollMode?: 'panel' | 'page';
    bodyPadding?: string;
    shellPadding?: string;
  }>(),
  {
    sectionTitle: '',
    breadcrumb: '',
    panelBordered: false,
    scrollMode: 'panel',
    bodyPadding: '16px',
    shellPadding: '0 16px 0',
  }
);
</script>

<style scoped>
.repository-shell {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--oa-bg-panel);
  padding: v-bind(shellPadding);
  box-sizing: border-box;
}

.repository-shell--page-scroll {
  height: auto;
  min-height: 100%;
  overflow: visible;
}

.repository-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  min-height: 64px;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
  box-sizing: border-box;
}

.repository-header__info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: var(--oa-text-secondary);
}

.header__title {
  font-size: var(--oa-font-heading);
  font-weight: 600;
  color: var(--oa-text-primary);
  line-height: 1.3;
}

.header__separator {
  color: var(--oa-text-muted);
  font-size: var(--oa-font-subtitle);
}

.header__subtitle {
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-subtitle);
  line-height: 1.5;
}

.repository-header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
  flex-wrap: wrap;
  min-height: 32px;
}

.page-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--oa-border-light);
  border-top: none;
  border-radius: 0 0 10px 10px;
  background: var(--oa-bg-panel);
}

.repository-shell--page-scroll .page-panel {
  overflow: visible;
}

.page-panel--borderless {
  border: none;
  border-radius: 0;
}

.page-panel__body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: v-bind(bodyPadding);
  box-sizing: border-box;
}

.repository-shell--page-scroll .page-panel__body {
  overflow: visible;
}

.page-panel__footer {
  padding: 12px 16px;
  border-top: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}
</style>
