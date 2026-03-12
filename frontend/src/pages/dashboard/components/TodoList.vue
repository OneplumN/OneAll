<template>
  <el-card shadow="hover" data-test="todo-list">
    <template #header>
      <div class="card-header">
        <div>
          <span class="title">待办事项</span>
          <span class="subtitle">关注审批、探针与插件健康</span>
        </div>
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

    <el-skeleton v-if="loading" :rows="4" animated />

    <el-empty
      v-else-if="!summary || summary.items.length === 0"
      description="暂无待办事项"
      data-test="todo-empty"
    />

    <el-collapse v-else data-test="todo-items">
      <el-collapse-item
        v-for="bucket in summary.items"
        :key="bucket.id"
        :title="`${bucket.title}（${bucket.total}）`
      "
      >
        <p class="bucket-description">{{ bucket.description }}</p>
        <el-timeline v-if="bucket.items.length" class="timeline">
          <el-timeline-item
            v-for="item in bucket.items"
            :key="item.id"
            :timestamp="formatDate(item.created_at)"
            type="primary"
          >
            <div class="todo-entry">
              <span class="label">{{ item.label }}</span>
              <span v-if="item.metadata" class="meta">{{ formatMetadata(item.metadata) }}</span>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无条目" />
      </el-collapse-item>
    </el-collapse>
  </el-card>
</template>

<script setup lang="ts">
import type { DashboardTodoSummary } from '@/types/dashboard';

defineProps<{
  summary: DashboardTodoSummary | null;
  loading: boolean;
  error: string | null;
}>();

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

function formatMetadata(metadata: Record<string, string>): string {
  return Object.entries(metadata)
    .map(([key, val]) => `${key}: ${val}`)
    .join(' · ');
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

.bucket-description {
  margin: 0 0 0.5rem;
  color: #606266;
}

.todo-entry {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta {
  color: #909399;
  font-size: 0.85rem;
}

.mb-2 {
  margin-bottom: 0.75rem;
}

.timeline {
  margin-top: 0.5rem;
}
</style>
