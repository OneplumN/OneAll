<template>
  <div class="oneoff-shell">
    <div class="repository-header">
      <div class="repository-header__info">
        <span class="header__title">{{ rootTitle }}</span>
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
    rootTitle?: string;
    sectionTitle: string;
    breadcrumb?: string;
    bodyPadding?: string;
    panelBordered?: boolean;
  }>(),
  {
    rootTitle: '一次性检验',
    breadcrumb: '',
    bodyPadding: '0',
    panelBordered: true
  }
);
</script>

<style scoped>
.oneoff-shell {
  display: flex;
  flex-direction: column;
  padding: 0 16px 16px;
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

:slotted(.toolbar-button) {
  border-radius: 6px;
  padding: 0 16px;
  height: 32px;
  font-weight: 500;
}

:slotted(.toolbar-button--primary) {
  box-shadow: none;
}

:slotted(.refresh-card) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--oa-border-light);
  border-radius: 8px;
  background: var(--oa-bg-panel);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
  box-shadow: var(--oa-shadow-sm);
}

:slotted(.refresh-card:hover) {
  border-color: var(--oa-color-primary-light);
  box-shadow: 0 10px 18px rgba(64, 158, 255, 0.08);
  transform: translateY(-1px);
}

:slotted(.refresh-icon.spinning) {
  animation: spin 0.8s linear infinite;
}

:slotted(.refresh-card--disabled) {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
  box-shadow: none;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.page-panel {
  display: flex;
  flex-direction: column;
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
  overflow: visible;
  padding: v-bind(bodyPadding);
  box-sizing: border-box;
}

.page-panel__footer {
  padding: 12px 16px;
  border-top: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}
</style>
