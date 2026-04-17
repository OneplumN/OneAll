<template>
  <div class="table-section">
    <el-card
      shadow="never"
      class="table-card"
      :body-style="{ padding: '0' }"
    >
      <div class="table-header">
        <div class="table-title">
          <el-icon><Document /></el-icon>
          <span>{{ title }}</span>
          <el-badge
            v-if="data.length"
            :value="data.length"
            class="ml-2"
          />
        </div>
        <div class="table-actions">
          <slot name="actions" />
          <el-button
            v-if="showClear && hasData"
            text
            size="small"
            @click="$emit('clear')"
          >
            清空
          </el-button>
        </div>
      </div>

      <el-table
        :data="data"
        :loading="loading"
        class="oa-table"
        stripe
        :empty-text="emptyText"
        @row-click="handleRowClick"
      >
        <slot />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Document } from '@element-plus/icons-vue';
import { computed } from 'vue';

interface Props {
  title?: string;
  data: any[];
  loading?: boolean;
  emptyText?: string;
  showClear?: boolean;
  clickable?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: '检测结果',
  loading: false,
  emptyText: '暂无检测记录',
  showClear: true,
  clickable: false
});

const emit = defineEmits<{
  clear: [];
  rowClick: [row: any];
}>();

const hasData = computed(() => props.data.length > 0);

const handleRowClick = (row: any) => {
  if (props.clickable) {
    emit('rowClick', row);
  }
};
</script>

<style scoped>
@import '../styles/detection-common.scss';

.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ml-2 {
  margin-left: 8px;
}

:deep(.el-table__row) {
  cursor: v-bind('clickable ? "pointer" : "default"');
}

:deep(.el-table__row:hover) {
  background-color: v-bind('clickable ? "var(--el-table-row-hover-bg-color)" : "inherit"');
}
</style>
