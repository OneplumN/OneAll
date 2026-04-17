<template>
  <el-dialog
    v-model="visibleModel"
    title="资产同步历史"
    width="700px"
  >
    <el-table
      v-loading="loading"
      :data="runs"
      class="oa-table sync-history-table"
    >
      <el-table-column
        prop="created_at"
        label="触发时间"
        min-width="160"
      >
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column
        prop="status"
        label="状态"
        width="120"
      >
        <template #default="{ row }">
          <el-tag
            size="small"
            :type="statusTagType(row.status)"
            effect="plain"
          >
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="mode"
        label="模式"
        width="80"
      />
      <el-table-column
        label="触发对象"
        min-width="160"
      >
        <template #default="{ row }">
          <span>{{ formatScope(row) }}</span>
        </template>
      </el-table-column>
      <el-table-column
        label="结果摘要"
        min-width="200"
      >
        <template #default="{ row }">
          <span>{{ formatSummary(row) }}</span>
        </template>
      </el-table-column>
    </el-table>
    <template #footer>
      <el-button @click="visibleModel = false">
        关闭
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import type { AssetSyncRun } from '@/features/assets/api/assetsApi';

const visibleModel = defineModel<boolean>('visible', { required: true });

defineProps<{
  loading: boolean;
  runs: AssetSyncRun[];
  formatDate: (value: string | null | undefined) => string;
  formatScope: (run: AssetSyncRun) => string;
  formatSummary: (run: AssetSyncRun) => string;
  statusTagType: (status: string) => string;
}>();
</script>
