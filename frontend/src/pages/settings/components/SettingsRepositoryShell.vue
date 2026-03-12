<template>
  <div class="settings-shell">
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

    <div class="repository-body">
      <aside class="repository-aside" :style="{ width: asideWidth }">
        <div class="repository-aside__scroll">
          <slot name="aside" />
        </div>
      </aside>

      <section class="repository-main">
        <div class="repository-main__scroll">
          <slot />
        </div>
        <div v-if="$slots.footer" class="repository-main__footer">
          <slot name="footer" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    sectionTitle: string;
    breadcrumb?: string;
    asideWidth?: string;
  }>(),
  {
    breadcrumb: '',
    asideWidth: '320px',
  }
);
</script>

<style scoped>
.settings-shell {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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

.repository-body {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
  border: 1px solid var(--oa-border-light);
  border-top: none;
  border-radius: 0 0 10px 10px;
}

.repository-aside {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--oa-bg-body);
  border-right: 1px solid var(--oa-border-light);
  min-height: 0;
  overflow: hidden;
}

.repository-aside__scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 12px;
}

.repository-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--oa-bg-panel);
}

.repository-main__scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 16px;
}

.repository-main__footer {
  padding: 12px 16px;
  border-top: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}
</style>
