<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    width="640px"
  >
    <div
      v-if="record"
      class="detail-dialog"
    >
      <el-descriptions
        :column="2"
        border
        size="small"
        class="asset-detail-descriptions"
      >
        <el-descriptions-item label="名称">
          {{ displayName || record.name }}
        </el-descriptions-item>
        <el-descriptions-item label="来源">
          {{ record.source }}
        </el-descriptions-item>
        <el-descriptions-item label="External ID">
          {{ record.external_id }}
        </el-descriptions-item>
        <el-descriptions-item label="资产状态">
          {{ formatSyncStatus(record.sync_status) }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(record.created_at) || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="修改时间">
          {{ formatDate(record.updated_at) || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider class="asset-detail-divider">
        模型字段
      </el-divider>
      <el-descriptions
        :column="2"
        size="small"
        class="asset-detail-descriptions asset-detail-descriptions--plain"
      >
        <el-descriptions-item
          v-for="column in columns"
          :key="column.key"
          :label="column.label"
        >
          {{ formatRowValue(detailRow, column.key) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
    <template #footer>
      <el-button @click="visibleModel = false">
        关闭
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import type { AssetRecord } from '@/features/assets/api/assetsApi';

type AssetRecordDetailColumn = {
  key: string;
  label: string;
};

const visibleModel = defineModel<boolean>('visible', { required: true });

withDefaults(
  defineProps<{
    title?: string;
    record: AssetRecord | null;
    detailRow: any;
    columns: AssetRecordDetailColumn[];
    displayName?: string;
    formatSyncStatus: (value: string | null | undefined) => string;
    formatDate: (value: string | null | undefined) => string;
    formatRowValue: (row: any, key: string) => string;
  }>(),
  {
    title: '资产详情',
    displayName: '',
  }
);
</script>

<style scoped>
.detail-dialog {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-dialog :deep(.el-descriptions__label),
.detail-dialog :deep(.el-descriptions__label.is-bordered-label) {
  font-size: var(--oa-font-subtitle);
  font-weight: 500;
  color: var(--oa-text-secondary);
  line-height: 1.6;
}

.detail-dialog :deep(.el-descriptions__label .el-descriptions__cell-item),
.detail-dialog :deep(.el-descriptions__label.is-bordered-label .el-descriptions__cell-item) {
  font-size: var(--oa-font-subtitle) !important;
  font-weight: 500;
  color: var(--oa-text-secondary) !important;
}

.detail-dialog :deep(.el-descriptions__content),
.detail-dialog :deep(.el-descriptions__content.is-bordered-content) {
  font-size: var(--oa-font-base);
  color: var(--oa-text-primary);
  line-height: 1.65;
}

.detail-dialog :deep(.el-descriptions__content .el-descriptions__cell-item),
.detail-dialog :deep(.el-descriptions__content.is-bordered-content .el-descriptions__cell-item) {
  font-size: var(--oa-font-base) !important;
  color: var(--oa-text-primary) !important;
  line-height: 1.65;
}

.detail-dialog :deep(.el-descriptions__cell) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.asset-detail-divider :deep(.el-divider__text) {
  font-size: var(--oa-font-subtitle);
  font-weight: 600;
  color: var(--oa-text-primary);
}
</style>
