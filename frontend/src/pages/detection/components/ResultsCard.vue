<template>
  <el-card shadow="never" class="results-card detection-card">
    <div class="results-header">
      <div class="results-title">
        <el-icon><Document /></el-icon>
        <span>{{ title }}</span>
        <span v-if="$slots['title-extra']" class="results-title-extra">
          <slot name="title-extra" />
        </span>
      </div>
      <div class="results-actions">
        <slot name="actions" />
      </div>
    </div>

    <div v-if="$slots.description" class="results-description">
      <slot name="description" />
    </div>

    <div class="results-body">
      <slot />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { Document } from '@element-plus/icons-vue';

withDefaults(
  defineProps<{
    title?: string;
  }>(),
  {
    title: '结果'
  }
);
</script>

<style scoped>
@import '../styles/detection-common.scss';

.results-body {
  padding: 0 16px 16px;
}
</style>
