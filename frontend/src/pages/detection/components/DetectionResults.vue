<template>
  <div class="results-section">
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
          <slot name="actions">
            <el-button
              text
              size="small"
              :disabled="!hasData"
              @click="$emit('clear')"
            >
              清空
            </el-button>
          </slot>
        </div>
      </div>

      <div v-if="$slots.description" class="results-description">
        <slot name="description" />
      </div>

      <div class="detection-table">
        <el-table
          :data="data"
          :loading="loading"
          stripe
          :empty-text="emptyText"
          :header-cell-style="tableHeaderStyle"
          :cell-style="tableCellStyle"
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
import { getTableHeaderStyle, getTableCellStyle } from '../utils/detectionUtils';

interface Props {
  title?: string;
  data: any[];
  loading?: boolean;
  emptyText?: string;
}

interface Emits {
  clear: [];
}

const props = withDefaults(defineProps<Props>(), {
  title: '检测结果',
  loading: false,
  emptyText: '暂无检测记录'
});

defineEmits<Emits>();

const hasData = computed(() => props.data.length > 0);
const tableHeaderStyle = getTableHeaderStyle;
const tableCellStyle = getTableCellStyle;
</script>

<style scoped>
@import '../styles/detection-common.scss';

.results-title-extra {
  margin-left: 10px;
  font-size: 12px;
  font-weight: 400;
  color: var(--oa-text-secondary);
  line-height: 1.4;
}

.results-description {
  padding: 12px 16px 0;
}
</style>
