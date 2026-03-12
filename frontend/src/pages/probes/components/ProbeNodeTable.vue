<template>
  <el-card shadow="never" class="panel-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <div>
          <h3>节点健康</h3>
        </div>
        <el-button text size="small" @click="$emit('refresh')">刷新</el-button>
      </div>
    </template>
    <el-table :data="rows" size="small" class="node-table" stripe>
      <el-table-column label="节点" min-width="180">
        <template #default="{ row }">
          <div class="node-cell">
            <strong>{{ row.name }}</strong>
            <small>{{ row.location }}</small>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="心跳延迟" width="140">
        <template #default="{ row }">
          <span :class="{ 'text-danger': row.heartbeat_delay_seconds > 300 }">
            {{ formatDelay(row.heartbeat_delay_seconds) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="资源" min-width="200">
        <template #default="{ row }">
          <div class="resource-inline">
            <span>CPU {{ formatPercent(row.metrics?.cpu_usage) }}</span>
            <span>内存 {{ formatMemory(row.metrics?.memory_usage_mb) }}</span>
            <span>队列 {{ formatQueue(row.metrics?.task_queue_depth, row.metrics?.queue_capacity) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="策略数量" width="120">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ row.schedule_count }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button link size="small" type="primary" @click="$emit('inspect', row.id)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && !rows.length" description="暂无探针数据" />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import dayjs from 'dayjs';

interface ProbeRow {
  id: string;
  name: string;
  location: string;
  status: string;
  heartbeat_delay_seconds: number | null;
  metrics?: Record<string, number>;
  schedule_count: number;
}

const props = defineProps<{ rows: ProbeRow[]; loading: boolean }>();
const statusTag = (status: string) => {
  if (status === 'online') return 'success';
  if (status === 'maintenance') return 'warning';
  return 'info';
};
const formatDelay = (seconds: number | null) => {
  if (!seconds || seconds < 0) return '—';
  if (seconds < 60) return `${seconds.toFixed(0)} 秒`;
  const minutes = seconds / 60;
  if (minutes < 60) return `${minutes.toFixed(1)} 分钟`;
  const hours = minutes / 60;
  return `${hours.toFixed(1)} 小时`;
};
const formatPercent = (value?: number) => (typeof value === 'number' ? `${value.toFixed(0)}%` : '—');
const formatMemory = (value?: number) => (typeof value === 'number' ? `${value.toFixed(0)} MB` : '—');
const formatQueue = (depth?: number, capacity?: number) => {
  if (typeof depth !== 'number') return '--';
  if (typeof capacity === 'number' && capacity > 0) {
    return `${depth}/${capacity}`;
  }
  return `${depth}`;
};
</script>

<style scoped>
.node-table :deep(.el-table__cell) {
  padding: 10px 12px;
}
.node-cell {
  display: flex;
  flex-direction: column;
}
.node-cell strong {
  color: var(--oa-text-primary);
}
.node-cell small {
  color: var(--oa-text-muted);
}
.resource-inline {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  color: var(--oa-text-secondary);
}
.text-danger {
  color: var(--oa-color-danger);
}
</style>
