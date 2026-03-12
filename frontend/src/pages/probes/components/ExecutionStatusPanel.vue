<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <div>
          <h3>执行概况</h3>
        </div>
        <el-button text size="small" @click="$emit('refresh')">刷新</el-button>
      </div>
    </template>
    <div class="status-grid">
      <div class="status-card" v-for="item in statusCards" :key="item.label">
        <p>{{ item.label }}</p>
        <h3>{{ item.value }}</h3>
        <small>{{ item.hint }}</small>
      </div>
    </div>
    <el-table :data="records" size="small" class="status-table" empty-text="暂无执行记录" stripe>
      <el-table-column label="节点" min-width="160">
        <template #default="{ row }">
          <strong>{{ row.probe?.name ?? '—' }}</strong>
        </template>
      </el-table-column>
      <el-table-column label="策略" min-width="200">
        <template #default="{ row }">
          {{ row.schedule?.name ?? '—' }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="调度时间" min-width="180">
        <template #default="{ row }">
          {{ formatTime(row.scheduled_at) }}
        </template>
      </el-table-column>
      <el-table-column label="耗时(ms)" width="120">
        <template #default="{ row }">
          {{ row.response_time_ms ?? '—' }}
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { computed } from 'vue';

interface ExecutionRecord {
  id: string;
  status: string;
  scheduled_at?: string;
  response_time_ms?: number | null;
  probe?: { id: string; name: string } | null;
  schedule?: { id: string; name: string } | null;
}

const props = defineProps<{ records: ExecutionRecord[]; aggregations: Record<string, number>; totalCount: number }>();
const statusTag = (status: string) => {
  const normalized = status.toLowerCase();
  if (normalized === 'succeeded') return 'success';
  if (normalized === 'failed') return 'danger';
  if (normalized === 'missed') return 'warning';
  if (normalized === 'running') return 'info';
  return 'info';
};
const formatTime = (value?: string) => (value ? dayjs(value).format('MM-DD HH:mm') : '—');
const statusCards = computed(() => [
  { label: '总执行', value: props.totalCount, hint: '近 24 小时' },
  { label: '成功', value: props.aggregations.succeeded ?? 0, hint: '状态 success' },
  { label: '失败', value: props.aggregations.failed ?? 0, hint: '状态 failed' },
  { label: '错过', value: props.aggregations.missed ?? 0, hint: '调度未响应' }
]);
</script>

<style scoped>
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.status-card {
  border: 1px solid var(--oa-border-color);
  border-radius: 10px;
  padding: 12px;
  background: var(--oa-bg-muted);
}
.status-card p {
  margin: 0;
  color: var(--oa-text-secondary);
  font-size: 12px;
}
.status-card h3 {
  margin: 6px 0 2px;
  font-size: 18px;
  font-weight: 600;
  color: var(--oa-text-primary);
}
.status-card small {
  color: var(--oa-text-muted);
  font-size: 12px;
}
.status-table {
  margin-top: 0.5rem;
}
</style>
