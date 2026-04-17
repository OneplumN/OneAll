<template>
  <div class="results-section">
    <el-card
      shadow="never"
      class="results-card detection-card"
    >
      <div class="results-header">
        <div class="results-title">
          <el-icon><Document /></el-icon>
          <span>{{ title }}</span>
          <span
            v-if="$slots['title-extra']"
            class="results-title-extra"
          >
            <slot name="title-extra" />
          </span>
        </div>
        <div class="results-actions">
          <slot name="actions">
            <el-button
              text
              size="small"
              :disabled="!canClear"
              @click="$emit('clear')"
            >
              清空
            </el-button>
          </slot>
        </div>
      </div>

      <div
        v-if="$slots.description"
        class="results-description"
      >
        <slot name="description" />
      </div>

      <div
        v-if="$slots.notice"
        class="results-notice"
      >
        <slot name="notice" />
      </div>

      <div class="detection-table">
        <el-table
          :data="data"
          :loading="loading"
          class="oa-table"
          stripe
          :empty-text="emptyText"
        >
          <slot name="columns" />
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Document } from '@element-plus/icons-vue';

interface Props {
  title?: string;
  data: any[];
  loading?: boolean;
  emptyText?: string;
  canClear?: boolean;
}

interface Emits {
  clear: [];
}

const props = withDefaults(defineProps<Props>(), {
  title: '检测结果',
  loading: false,
  emptyText: '暂无检测记录',
  canClear: undefined
});

defineEmits<Emits>();

const hasData = computed(() => props.data.length > 0);
const canClear = computed(() => props.canClear ?? hasData.value);
</script>

<style scoped>
@import '../styles/detection-common.scss';

.results-title-extra {
  margin-left: 10px;
  font-size: var(--oa-font-meta);
  font-weight: 400;
  color: var(--oa-text-secondary);
  line-height: 1.4;
}

.results-description {
  padding: 12px 16px 0;
}

.results-notice {
  padding: 12px 16px 0;
}
</style>
