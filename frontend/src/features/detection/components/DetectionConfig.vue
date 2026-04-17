<template>
  <component
    :is="embedded ? 'section' : 'el-card'"
    v-bind="embedded ? {} : { shadow: 'never' }"
    :class="['config-card', { 'detection-card': !embedded, 'config-card--embedded': embedded }]"
  >
    <div class="card-title">
      <el-icon><Setting /></el-icon>
      <span>{{ title }}</span>
    </div>

    <div class="config-section">
      <slot name="config-items" />
    </div>
  </component>
</template>

<script setup lang="ts">
import { Setting } from '@element-plus/icons-vue';

interface Props {
  title?: string;
  embedded?: boolean;
}

withDefaults(defineProps<Props>(), {
  title: '检测配置',
  embedded: false
});
</script>

<style scoped>
@import '../styles/detection-common.scss';

.config-card {
  height: fit-content;
}

.config-card--embedded {
  border: none;
  border-radius: 0;
  background: transparent;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-sizing: border-box;
}

.config-card--embedded :deep(.config-item) {
  border: none;
  background: transparent;
  padding: 0;
}

.config-card--embedded :deep(.config-item__header) {
  margin-bottom: 6px;
}

.config-card--embedded :deep(.config-item__value) {
  color: var(--oa-text-primary);
}

.config-card--embedded :deep(.config-item--row) {
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.config-card--embedded :deep(.config-section) {
  padding: 12px;
  border-radius: 10px;
  background: var(--oa-bg-muted);
}
</style>
