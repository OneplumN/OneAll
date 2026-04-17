<template>
  <el-drawer
    v-model="visibleModel"
    title="节点详情"
    size="40%"
  >
    <div
      v-if="probe"
      class="runtime-panel"
    >
      <div class="runtime-header">
        <div>
          <p class="eyebrow">
            节点
          </p>
          <h3>{{ probe.name }}</h3>
          <p class="subtitle">
            状态：<el-tag
              :type="statusTagType(probe.status)"
              size="small"
            >
              {{ statusLabel(probe.status) }}
            </el-tag>
            <span class="divider">·</span>
            心跳：{{ probe.last_heartbeat_at ? heartbeatAgo(probe.last_heartbeat_at) : '未上报' }}
          </p>
        </div>
      </div>
      <section class="runtime-section">
        <h4>基础信息</h4>
        <el-descriptions
          :column="1"
          border
          size="small"
        >
          <el-descriptions-item label="节点 ID">
            <code class="probe-id">{{ probe.id }}</code>
          </el-descriptions-item>
          <el-descriptions-item label="IP">
            {{ probe.ip_address ?? '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="位置">
            {{ probe.location || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="网络类型">
            {{ networkTypeLabel(probe.network_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="支持协议">
            <el-space wrap>
              <el-tag
                v-for="proto in probe.supported_protocols"
                :key="proto"
                size="small"
              >
                {{ proto }}
              </el-tag>
            </el-space>
          </el-descriptions-item>
          <el-descriptions-item label="最近认证">
            {{ probe.last_authenticated_at ? formatAuth(probe.last_authenticated_at) : '未认证' }}
          </el-descriptions-item>
        </el-descriptions>
      </section>

      <section class="runtime-section">
        <h4>运行统计</h4>
        <el-descriptions
          :column="2"
          border
          size="small"
        >
          <el-descriptions-item label="运行时长">
            {{ uptimeDisplay(probe) }}
          </el-descriptions-item>
          <el-descriptions-item label="近窗口执行次数">
            {{ formatExecutions(probe) }}
          </el-descriptions-item>
          <el-descriptions-item label="失败 / 成功率">
            {{ formatFailureRate(probe) }}
          </el-descriptions-item>
          <el-descriptions-item label="平均响应时间">
            {{ formatAvgLatency(probe) }}
          </el-descriptions-item>
        </el-descriptions>
      </section>
    </div>
    <el-empty
      v-else
      description="请选择探针节点"
    />
  </el-drawer>
</template>

<script setup lang="ts">
import type { ProbeNodeRecord } from '@/features/probes/api/probeNodeApi';

const visibleModel = defineModel<boolean>('visible', { required: true });

defineProps<{
  probe: ProbeNodeRecord | null;
  heartbeatAgo: (value: string) => string;
  networkTypeLabel: (value: string) => string;
  statusLabel: (status: string) => string;
  statusTagType: (status: string) => string;
  formatAuth: (value: string) => string;
  uptimeDisplay: (probe: { id: string }) => string;
  formatExecutions: (probe: { id: string }) => string | number;
  formatFailureRate: (probe: { id: string }) => string;
  formatAvgLatency: (probe: { id: string }) => string;
}>();
</script>

<style scoped>
.eyebrow {
  margin: 0 0 4px;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-muted);
  letter-spacing: 0.5px;
}

.subtitle {
  margin: 4px 0 0;
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-subtitle);
}

.probe-id {
  font-family: 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: var(--oa-font-meta);
  background: var(--oa-bg-muted);
  border: 1px solid var(--oa-border-light);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  word-break: break-all;
}

.runtime-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.runtime-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.runtime-section h4 {
  margin: 0 0 0.5rem;
  font-weight: 600;
  font-size: var(--oa-font-section-title);
  color: var(--oa-text-primary);
}

.divider {
  color: var(--oa-text-muted);
  margin: 0 6px;
}

.runtime-panel :deep(.el-descriptions__label),
.runtime-panel :deep(.el-descriptions__label.is-bordered-label) {
  font-size: var(--oa-font-subtitle);
  font-weight: 500;
  color: var(--oa-text-secondary);
  line-height: 1.6;
}

.runtime-panel :deep(.el-descriptions__label .el-descriptions__cell-item),
.runtime-panel :deep(.el-descriptions__label.is-bordered-label .el-descriptions__cell-item) {
  font-size: var(--oa-font-subtitle) !important;
  font-weight: 500;
  color: var(--oa-text-secondary) !important;
}

.runtime-panel :deep(.el-descriptions__content),
.runtime-panel :deep(.el-descriptions__content.is-bordered-content) {
  font-size: var(--oa-font-base);
  color: var(--oa-text-primary);
  line-height: 1.65;
}

.runtime-panel :deep(.el-descriptions__content .el-descriptions__cell-item),
.runtime-panel :deep(.el-descriptions__content.is-bordered-content .el-descriptions__cell-item) {
  font-size: var(--oa-font-base) !important;
  color: var(--oa-text-primary) !important;
  line-height: 1.65;
}

.runtime-panel :deep(.el-descriptions__cell) {
  padding-top: 10px;
  padding-bottom: 10px;
}
</style>
