<template>
  <PageWrapper :loading="loading.nodes">
    <RepositoryPageShell
      root-title="监控与告警"
      section-title="节点"
      body-padding="0"
      :panel-bordered="false"
    >
      <template #actions>
        <div class="probe-header-actions">
          <div
            class="refresh-card"
            @click="loadNodes"
          >
            <el-icon
              class="refresh-icon"
              :class="{ spinning: loading.nodes }"
            >
              <Refresh />
            </el-icon>
            <span>刷新</span>
          </div>
        </div>
      </template>

      <div class="oa-list-page">
        <div class="page-toolbar page-toolbar--panel">
          <div class="page-toolbar__right">
            <el-input
              v-model="searchText"
              placeholder="搜索名称 / IP / ID"
              clearable
              class="search-input pill-input search-input--compact"
            />
          </div>
        </div>

        <div class="oa-table-panel">
          <ProbeNodeTable
            :loading="loading.nodes"
            :rows="filteredProbes"
            :effective-status="effectiveStatus"
            :format-cpu-usage="formatCpuUsage"
            :format-memory-usage="formatMemoryUsage"
            :format-queue-depth="formatQueueDepth"
            :uptime-display="uptimeDisplay"
            :heartbeat-ago="heartbeatAgo"
            :network-type-label="networkTypeLabel"
            :status-label="statusLabel"
            :status-tag-type="statusTagType"
            @row-click="handleRowClick"
            @open-runtime="openRuntime"
            @copy-node-id="copyNodeId"
            @reload="loadNodes"
          />

          <section
            v-if="chartsProbe && hasHealthSummary"
            class="probe-health-section"
          >
            <header class="health-header">
              <div>
                <h3 class="health-title">
                  节点资源趋势 · {{ chartsProbe.name }}
                </h3>
                <p class="health-subtitle">
                  当前 CPU / 内存 / 队列快照
                </p>
              </div>
            </header>
            <div class="health-charts">
              <div class="chart-column">
                <h4 class="chart-title">
                  CPU 利用率（近 6 小时）
                </h4>
                <BaseChart
                  :option="cpuTrendOption"
                  :height="200"
                />
              </div>
              <div class="chart-column">
                <h4 class="chart-title">
                  内存使用（近 6 小时）
                </h4>
                <BaseChart
                  :option="memoryTrendOption"
                  :height="200"
                />
              </div>
              <div class="chart-column">
                <h4 class="chart-title">
                  队列深度（近 6 小时）
                </h4>
                <BaseChart
                  :option="queueTrendOption"
                  :height="200"
                />
              </div>
            </div>
          </section>
        </div>
      </div>
    </RepositoryPageShell>

    <ProbeRuntimeDrawer
      v-model:visible="runtimeVisible"
      :probe="currentProbe"
      :heartbeat-ago="heartbeatAgo"
      :network-type-label="networkTypeLabel"
      :status-label="statusLabel"
      :status-tag-type="statusTagType"
      :format-auth="formatAuth"
      :uptime-display="uptimeDisplay"
      :format-executions="formatExecutions"
      :format-failure-rate="formatFailureRate"
      :format-avg-latency="formatAvgLatency"
    />
  </PageWrapper>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Refresh } from '@element-plus/icons-vue';
import PageWrapper from '@/shared/components/layout/PageWrapper';
import BaseChart from '@/features/probes/components/BaseChart.vue';
import ProbeNodeTable from '@/features/probes/components/ProbeNodeTable.vue';
import ProbeRuntimeDrawer from '@/features/probes/components/ProbeRuntimeDrawer.vue';
import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import { useProbeDashboard } from '@/features/probes/composables/useProbeDashboard';
import {
  effectiveStatus as resolveEffectiveStatus,
  formatAuthTime as formatAuth,
  formatAvgLatency as formatProbeAvgLatency,
  formatCpuUsage as formatProbeCpuUsage,
  formatExecutions as formatProbeExecutions,
  formatFailureRate as formatProbeFailureRate,
  formatMemoryUsage as formatProbeMemoryUsage,
  formatQueueDepth as formatProbeQueueDepth,
  hasHealthSummary as resolveHasHealthSummary,
  heartbeatAgo,
  networkTypeLabel,
  statusLabel,
  statusTagType,
  uptimeDisplay as formatProbeUptime
} from '@/features/probes/utils/probeNodePresentation';
const {
  chartsProbe,
  copyNodeId,
  cpuTrendOption,
  currentProbe,
  filteredProbes,
  handleRowClick,
  healthById,
  loadNodes,
  loading,
  memoryTrendOption,
  openRuntime,
  queueTrendOption,
  runtimeVisible,
  searchText,
} = useProbeDashboard();

const formatCpuUsage = (probe: { id: string }) => formatProbeCpuUsage(probe.id, healthById);
const formatMemoryUsage = (probe: { id: string }) => formatProbeMemoryUsage(probe.id, healthById);
const formatQueueDepth = (probe: { id: string }) => formatProbeQueueDepth(probe.id, healthById);
const effectiveStatus = (probe: { id: string; status: string }) => resolveEffectiveStatus(probe, healthById);
const uptimeDisplay = (probe: { id: string }) => formatProbeUptime(probe.id, healthById);
const formatExecutions = (probe: { id: string }) => formatProbeExecutions(probe.id, healthById);
const formatFailureRate = (probe: { id: string }) => formatProbeFailureRate(probe.id, healthById);
const formatAvgLatency = (probe: { id: string }) => formatProbeAvgLatency(probe.id, healthById);
const hasHealthSummary = computed(() => resolveHasHealthSummary(healthById));
</script>

<style scoped>
.probe-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.probe-health-section {
  margin-top: 16px;
  padding: 16px;
  border-radius: 8px;
  background: var(--oa-bg-panel);
  box-shadow: var(--oa-shadow-sm);
}

.health-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 12px;
}

.health-title {
  margin: 0;
  font-size: var(--oa-font-section-title);
  font-weight: 600;
  color: var(--oa-text-primary);
}

.health-subtitle {
  margin: 4px 0 0;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.health-charts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.chart-column {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chart-title {
  margin: 0;
  font-size: var(--oa-font-subtitle);
  font-weight: 500;
  color: var(--oa-text-primary);
}

@media (max-width: 1024px) {
  .health-charts {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .probe-header-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
