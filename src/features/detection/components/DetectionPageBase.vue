<template>
  <OneOffPageShell
    :root-title="rootTitle"
    :section-title="title"
    body-padding="0"
    :panel-bordered="panelBordered"
  >
    <template #actions>
      <slot name="header-actions">
        <div
          v-if="refreshable"
          :class="['refresh-card', { 'refresh-card--disabled': refreshing }]"
          :aria-disabled="refreshing"
          @click="refreshing ? undefined : $emit('refresh')"
        >
          <el-icon
            class="refresh-icon"
            :class="{ spinning: refreshing }"
          >
            <Refresh />
          </el-icon>
          <span>{{ refreshText }}</span>
        </div>
      </slot>
    </template>
    <div class="detection-layout">
      <div class="detection-content">
        <el-alert
          v-if="error"
          type="error"
          :closable="false"
          show-icon
          class="mb-4"
        >
          {{ error }}
        </el-alert>

        <slot name="intro" />

        <el-card
          shadow="never"
          class="detection-card config-wrapper"
        >
          <div class="config-header">
            <div class="config-title">
              <el-icon><Setting /></el-icon>
              <span>{{ configTitle }}</span>
            </div>
          </div>

          <div
            :class="[
              'page-toolbar',
              'page-toolbar--panel',
              'config-toolbar',
              { 'config-toolbar--single': !$slots['header-right'] }
            ]"
          >
            <div class="page-toolbar__left">
              <slot name="header-left" />
            </div>
            <div
              v-if="$slots['header-right']"
              class="page-toolbar__right"
            >
              <slot name="header-right" />
            </div>
          </div>

          <div
            v-if="$slots.config"
            class="config-body"
          >
            <slot name="config" />
          </div>

          <footer
            v-if="$slots['config-footer']"
            class="config-footer"
          >
            <slot name="config-footer" />
          </footer>
        </el-card>

        <slot name="content" />
      </div>
    </div>
  </OneOffPageShell>
</template>

<script setup lang="ts">
import OneOffPageShell from './OneOffPageShell.vue';
import { Refresh, Setting } from '@element-plus/icons-vue';

interface Props {
  title: string;
  error?: string | null;
  configTitle?: string;
  panelBordered?: boolean;
  rootTitle?: string;
  refreshable?: boolean;
  refreshing?: boolean;
  refreshText?: string;
}

defineEmits<{
  (event: 'refresh'): void;
}>();

withDefaults(defineProps<Props>(), {
  error: null,
  configTitle: '检测配置',
  panelBordered: false,
  rootTitle: '一次性检验',
  refreshable: false,
  refreshing: false,
  refreshText: '刷新'
});
</script>

<style scoped>
@import '../styles/detection-common.scss';

.mb-4 {
  margin-bottom: 16px;
}

.config-wrapper :deep(.el-card__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.config-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 14px;
  color: var(--oa-text-primary);
}

.config-title :deep(.el-icon) {
  color: var(--el-color-primary);
}

.config-toolbar {
  border-bottom: 1px solid var(--oa-border-light);
}

.config-toolbar .page-toolbar__left {
  flex: 1 1 auto;
}

.config-toolbar--single .page-toolbar__left {
  width: 100%;
}

.config-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}
</style>
