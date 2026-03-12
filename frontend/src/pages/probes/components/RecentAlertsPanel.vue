<template>
  <el-card shadow="never" class="panel-card recent-alerts" v-loading="loading">
    <template #header>
      <div class="card-header">
        <div>
          <h3>最近告警</h3>
          <p>近 10 条探针调度异常</p>
        </div>
        <div class="actions">
          <el-button text size="small" @click="$emit('refresh')">刷新</el-button>
          <el-button text size="small" @click="$emit('view-logs')">查看日志</el-button>
        </div>
      </div>
    </template>
    <el-empty v-if="!alerts.length && !loading" description="暂无告警" />
    <el-timeline v-else class="alert-list">
      <el-timeline-item
        v-for="item in alerts"
        :key="item.id"
        :type="severityType(item.severity)"
        :timestamp="formatTimestamp(item.occurred_at)"
      >
        <div class="alert-item">
          <div class="title">
            {{ item.schedule_name || '未知策略' }}
            <el-tag size="small" :type="severityType(item.severity)">
              {{ item.status }}
            </el-tag>
          </div>
          <p class="meta">
            探针：{{ item.probe_name || '未指定' }} · 连续失败 {{ item.threshold }} 次
          </p>
          <p class="message">{{ item.message || '未提供告警信息' }}</p>
        </div>
      </el-timeline-item>
    </el-timeline>
  </el-card>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';

import type { ProbeAlertRecord } from '@/services/probeAlertApi';

defineProps<{
  alerts: ProbeAlertRecord[];
  loading: boolean;
}>();

defineEmits<{
  (event: 'refresh'): void;
  (event: 'view-logs'): void;
}>();

const formatTimestamp = (value: string) => dayjs(value).format('MM-DD HH:mm');
const severityType = (severity: string) => {
  const normalized = severity?.toLowerCase?.() ?? '';
  if (normalized === 'critical') return 'danger';
  if (normalized === 'warning') return 'warning';
  return 'info';
};
</script>

<style scoped>
.recent-alerts .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.recent-alerts .card-header h3 {
  margin: 0;
}
.recent-alerts .card-header p {
  margin: 0;
  color: #909399;
  font-size: 0.85rem;
}
.actions {
  display: flex;
  gap: 0.25rem;
}
.alert-item {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.alert-item .title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}
.alert-item .meta {
  margin: 0;
  color: #909399;
  font-size: 0.85rem;
}
.alert-item .message {
  margin: 0;
  color: #303133;
}
</style>
