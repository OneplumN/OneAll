<template>
  <div class="settings-page">
    <div class="repository-header">
      <div class="repository-header__info">
        <span class="header__title">系统设置</span>
        <span class="header__separator">/</span>
        <span class="header__subtitle">{{ sectionTitle }}</span>
        <template v-if="breadcrumb">
          <span class="header__separator">/</span>
          <span class="header__subtitle">{{ breadcrumb }}</span>
        </template>
      </div>
      <div class="repository-header__actions">
        <slot name="actions" />
      </div>
    </div>

    <section :class="['page-panel', { 'page-panel--borderless': !panelBordered }]">
      <div class="page-panel__body">
        <slot />
      </div>
      <footer v-if="$slots.footer" class="page-panel__footer">
        <slot name="footer" />
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    sectionTitle: string;
    breadcrumb?: string;
    bodyPadding?: string;
    panelBordered?: boolean;
  }>(),
  {
    breadcrumb: '',
    bodyPadding: '16px',
    panelBordered: true,
  }
);
</script>

<style scoped>
.settings-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 16px 0px;
  box-sizing: border-box;
  background: var(--oa-bg-panel);
}

.repository-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.repository-header__info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: var(--oa-text-secondary);
}

.header__title {
  font-weight: 600;
  color: var(--oa-text-primary);
}

.header__separator {
  color: var(--oa-text-muted);
  font-size: 13px;
}

.header__subtitle {
  color: var(--oa-text-secondary);
}

.repository-header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
  flex-wrap: wrap;
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

.page-panel--borderless {
  border: none;
  border-radius: 0;
}

.page-panel__body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: v-bind(bodyPadding);
  box-sizing: border-box;
}

.page-panel__footer {
  padding: 12px 16px;
  border-top: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}
</style>
