<template>
  <div class="oa-table-panel">
    <div class="oa-table-panel__card probe-table-card">
      <el-table
        v-loading="loading"
        :data="rows"
        class="oa-table probe-table"
        stripe
        height="100%"
        @row-click="emit('rowClick', $event)"
      >
        <el-table-column
          prop="name"
          label="应用名称"
          min-width="220"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <div class="title-cell">
              <strong class="oa-table-title">{{ row.name }}</strong>
              <span class="oa-table-meta">
                {{ row.location || '未设置' }} · {{ networkTypeLabel(row.network_type) }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          prop="ip_address"
          label="IP 地址"
          width="160"
        >
          <template #default="{ row }">
            <span class="oa-table-meta">{{ row.ip_address ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="status"
          label="状态"
          width="120"
        >
          <template #default="{ row }">
            <el-tag
              :type="statusTagType(effectiveStatus(row))"
              size="small"
            >
              {{ statusLabel(effectiveStatus(row)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="资源"
          min-width="220"
        >
          <template #default="{ row }">
            <div class="resource-inline">
              <span>CPU {{ formatCpuUsage(row) }}</span>
              <span>内存 {{ formatMemoryUsage(row) }}</span>
              <span>队列 {{ formatQueueDepth(row) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          label="运行时长"
          width="180"
        >
          <template #default="{ row }">
            <span class="oa-table-meta">{{ uptimeDisplay(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="last_heartbeat_at"
          label="最后心跳"
          width="200"
        >
          <template #default="{ row }">
            <span class="oa-table-meta">
              {{ row.last_heartbeat_at ? heartbeatAgo(row.last_heartbeat_at) : '未上报' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="180"
          fixed="right"
          align="center"
        >
          <template #default="{ row }">
            <el-button
              size="small"
              link
              class="oa-table-action oa-table-action--primary"
              @click.stop="emit('openRuntime', row)"
            >
              详情
            </el-button>
            <el-button
              size="small"
              link
              class="oa-table-action oa-table-action--success"
              @click.stop="emit('copyNodeId', row.id)"
            >
              复制 ID
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty
      v-if="!loading && !rows.length"
      description="当前筛选下暂无探针节点"
    >
      <div class="empty-actions">
        <el-button
          text
          @click="emit('reload')"
        >
          重新加载
        </el-button>
      </div>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import type { ProbeNodeRecord } from '@/features/probes/api/probeNodeApi';

defineProps<{
  loading: boolean;
  rows: ProbeNodeRecord[];
  effectiveStatus: (probe: { id: string; status: string }) => string;
  formatCpuUsage: (probe: { id: string }) => string;
  formatMemoryUsage: (probe: { id: string }) => string;
  formatQueueDepth: (probe: { id: string }) => string;
  uptimeDisplay: (probe: { id: string }) => string;
  heartbeatAgo: (value: string) => string;
  networkTypeLabel: (value: string) => string;
  statusLabel: (status: string) => string;
  statusTagType: (status: string) => string;
}>();

const emit = defineEmits<{
  (event: 'rowClick', probe: ProbeNodeRecord): void;
  (event: 'openRuntime', probe: ProbeNodeRecord): void;
  (event: 'copyNodeId', id: string): void;
  (event: 'reload'): void;
}>();
</script>

<style scoped>
.probe-table-card {
  flex: 1;
  min-height: 0;
}

.title-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.resource-inline {
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-meta);
}

.empty-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}
</style>
