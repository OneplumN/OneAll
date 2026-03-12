<template>
  <el-card shadow="hover" data-test="alert-summary">
    <template #header>
      <div class="card-header">
        <div>
          <span class="title">告警摘要</span>
          <span class="subtitle">近 24 小时内的拨测异常</span>
        </div>
        <slot name="actions" />
      </div>
    </template>

    <el-alert
      v-if="error"
      type="error"
      show-icon
      :closable="false"
      class="mb-2"
    >
      {{ error }}
    </el-alert>

    <el-skeleton v-if="loading" :rows="3" animated />

    <div v-else>
      <div class="breakdown" data-test="alert-breakdown">
        <div
          v-for="item in summary?.breakdown || []"
          :key="item.level"
          class="breakdown-item"
        >
          <span class="label">{{ levelName(item.level) }}</span>
          <span class="value">{{ item.count }}</span>
        </div>
        <div class="breakdown-item">
          <span class="label">总计</span>
          <span class="value">{{ summary?.total_alerts ?? 0 }}</span>
        </div>
      </div>

      <el-empty
        v-if="!summary || summary.items.length === 0"
        description="暂无异常告警"
        data-test="alert-empty"
      />

      <el-timeline v-else class="timeline" data-test="alert-items">
        <el-timeline-item
          v-for="item in summary.items"
          :key="item.id"
          :type="timelineType(item.severity)"
          :timestamp="formatDate(item.occurred_at)"
        >
          <div class="alert-item">
            <p class="alert-title">
              {{ item.target }}
              <el-tag size="small" :type="tagType(item.severity)">
                {{ levelName(item.severity) }}
              </el-tag>
            </p>
            <p class="alert-meta" v-if="item.probe">探针：{{ item.probe }}</p>
            <p class="alert-meta">状态：{{ item.status }}</p>
            <p class="alert-meta" v-if="item.message">备注：{{ item.message }}</p>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { DashboardAlertSummary } from '@/types/dashboard';

defineProps<{
  summary: DashboardAlertSummary | null;
  loading: boolean;
  error: string | null;
}>();

function levelName(level: DashboardAlertSummary['breakdown'][number]['level']): string {
  switch (level) {
    case 'critical':
      return '严重';
    case 'warning':
      return '警告';
    default:
      return '提示';
  }
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

function tagType(level: DashboardAlertSummary['breakdown'][number]['level']): string {
  switch (level) {
    case 'critical':
      return 'danger';
    case 'warning':
      return 'warning';
    default:
      return 'info';
  }
}

function timelineType(level: DashboardAlertSummary['breakdown'][number]['level']): string {
  switch (level) {
    case 'critical':
      return 'danger';
    case 'warning':
      return 'warning';
    default:
      return 'info';
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.title {
  font-weight: 600;
}

.subtitle {
  display: block;
  color: #909399;
  font-size: 0.875rem;
}

.breakdown {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.breakdown-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.label {
  color: #909399;
  font-size: 0.875rem;
}

.value {
  font-size: 1.5rem;
  font-weight: 600;
}

.timeline {
  margin-top: 1rem;
}

.alert-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.alert-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-weight: 600;
}

.alert-meta {
  margin: 0;
  color: #606266;
  font-size: 0.875rem;
}

.mb-2 {
  margin-bottom: 0.75rem;
}
</style>
