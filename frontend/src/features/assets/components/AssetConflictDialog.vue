<template>
  <el-dialog
    v-model="visibleModel"
    title="冲突详情"
    width="640px"
  >
    <div
      v-if="record"
      class="conflict-dialog"
    >
      <el-descriptions
        :column="1"
        border
        size="small"
      >
        <el-descriptions-item label="来源">
          {{ record.source }}
        </el-descriptions-item>
        <el-descriptions-item label="External ID">
          {{ record.external_id }}
        </el-descriptions-item>
        <el-descriptions-item label="名称">
          {{ record.name }}
        </el-descriptions-item>
        <el-descriptions-item label="系统名称">
          {{ record.system_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="当前状态">
          {{ formatSyncStatus(record.sync_status) }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>冲突记录</el-divider>
      <div v-if="conflictLog.length">
        <el-alert
          v-for="(entry, index) in conflictLog"
          :key="index"
          :title="entry.type === 'canonical_duplicate' ? '业务唯一键冲突' : entry.type"
          type="warning"
          :closable="false"
          class="conflict-entry"
        >
          <template #default>
            <div v-if="entry.asset_type">
              资产类型：{{ entry.asset_type }}
            </div>
            <div v-if="entry.canonical_key">
              业务唯一键：{{ entry.canonical_key }}
            </div>
            <div v-if="entry.anchor">
              对齐主记录 ID：{{ entry.anchor }}
            </div>
            <div v-if="entry.sources && entry.sources.length">
              涉及来源：{{ entry.sources.join(' / ') }}
            </div>
            <div v-if="entry.duplicates && entry.duplicates.length">
              冲突记录 ID 列表：{{ entry.duplicates.join(', ') }}
            </div>
            <div v-if="entry.fields && entry.fields.length">
              缺失字段：{{ entry.fields.join(', ') }}
            </div>
          </template>
        </el-alert>
      </div>
      <el-empty
        v-else
        description="暂无冲突记录详情"
      />
    </div>
    <template #footer>
      <el-button @click="visibleModel = false">
        关闭
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { AssetRecord } from '@/features/assets/api/assetsApi';

const visibleModel = defineModel<boolean>('visible', { required: true });

const props = defineProps<{
  record: AssetRecord | null;
  formatSyncStatus: (value: string | null | undefined) => string;
}>();

const conflictLog = computed(() => {
  const items = (props.record?.metadata as any)?.conflict_log;
  return Array.isArray(items) ? items : [];
});
</script>

<style scoped>
.conflict-dialog {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.conflict-entry {
  margin-bottom: 8px;
}
</style>
