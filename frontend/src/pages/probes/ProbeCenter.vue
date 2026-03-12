<template>
  <div class="probe-center-page">
    <header class="page-heading">
      <div class="heading-title">
        <span class="header__title">探针中心</span>
      </div>
      <div class="heading-actions">
        <el-button class="toolbar-button" @click="goTo('/probes/nodes')">节点管理</el-button>
        <el-button class="toolbar-button" @click="goTo('/probes/schedules')">调度管理</el-button>
        <div class="refresh-card" @click="loadAll">
          <el-icon class="refresh-icon" :class="{ spinning: isLoading }"><Refresh /></el-icon>
          <span>刷新</span>
        </div>
      </div>
    </header>

    <ProbeSummaryGrid :cards="summaryCards" />

    <el-row :gutter="16" class="panel-grid">
      <el-col :lg="12" :md="24" :xs="24">
        <ProbeNodeTable
          :rows="nodeRows"
          :loading="loading.nodes"
          @refresh="fetchNodes"
          @inspect="goToNode"
        />
      </el-col>
      <el-col :lg="12" :md="24" :xs="24">
        <ExecutionStatusPanel
          :records="recentExecutions"
          :aggregations="statusAggregations"
          :total-count="executionTotal"
          @refresh="fetchExecutions"
        />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="panel-grid">
      <el-col :lg="12" :md="24" :xs="24">
        <CriticalNodesPanel
          :loading="loading.nodes"
          :latency-nodes="latencyRanking"
          :failure-nodes="failureRanking"
        />
      </el-col>
      <el-col :lg="12" :md="24" :xs="24">
        <el-card shadow="never" class="panel-card" v-loading="loading.schedules">
          <template #header>
            <div class="card-header">
              <div>
                <h3>策略概况</h3>
              </div>
              <el-button text size="small" @click="goTo('/probes/schedules')">调度管理</el-button>
            </div>
          </template>
          <ul class="strategy-list">
            <li>总策略：{{ schedules.length }} 条</li>
            <li>手工调度：{{ manualSchedules }} 条</li>
            <li>自动调度：{{ schedules.length - manualSchedules }} 条</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>

  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { ElMessage } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Refresh } from '@element-plus/icons-vue';

import ProbeSummaryGrid from './components/ProbeSummaryGrid.vue';
import ProbeNodeTable from './components/ProbeNodeTable.vue';
import CriticalNodesPanel from './components/CriticalNodesPanel.vue';
import ExecutionStatusPanel from './components/ExecutionStatusPanel.vue';
import apiClient from '@/services/apiClient';
import { listProbeSchedules, type ProbeScheduleRecord } from '@/services/probeScheduleApi';
import { fetchProbeScheduleExecutions } from '@/services/probeScheduleExecutionApi';
import type { ProbeScheduleExecutionRecord, ProbeScheduleExecutionAggregates } from '@/services/probeScheduleExecutionApi';
import { fetchProbeRuntime, type ProbeRuntimePayload } from '@/services/probeNodeApi';

interface ProbeNode {
  id: string;
  name: string;
  location: string;
  network_type: string;
  status: string;
  last_heartbeat_at: string | null;
}

const router = useRouter();
const nodes = ref<ProbeNode[]>([]);
const schedules = ref<ProbeScheduleRecord[]>([]);
const executions = ref<ProbeScheduleExecutionRecord[]>([]);
const aggregates = ref<ProbeScheduleExecutionAggregates | null>(null);
const runtimeByNode = reactive<Record<string, ProbeRuntimePayload | null>>({});
const loading = reactive({ nodes: false, schedules: false, executions: false, runtimes: false });

const fetchNodes = async () => {
  loading.nodes = true;
  try {
    const { data } = await apiClient.get<ProbeNode[]>('/probes/nodes/');
    nodes.value = data;
    await fetchNodeRuntimes(data);
  } catch (error) {
    ElMessage.error('探针节点加载失败');
  } finally {
    loading.nodes = false;
  }
};

const fetchNodeRuntimes = async (nodeList: ProbeNode[]) => {
  loading.runtimes = true;
  try {
    await Promise.all(
      nodeList.map(async (node) => {
        try {
          const runtime = await fetchProbeRuntime(node.id);
          runtimeByNode[node.id] = runtime;
        } catch {
          runtimeByNode[node.id] = null;
        }
      })
    );
  } finally {
    loading.runtimes = false;
  }
};

const fetchSchedules = async () => {
  loading.schedules = true;
  try {
    schedules.value = await listProbeSchedules();
  } catch (error) {
    ElMessage.error('调度策略加载失败');
  } finally {
    loading.schedules = false;
  }
};

const fetchExecutions = async () => {
  loading.executions = true;
  try {
    const response = await fetchProbeScheduleExecutions({ page: 1, page_size: 10 });
    executions.value = response.items;
    aggregates.value = response.aggregates;
  } catch (error) {
    ElMessage.error('执行记录加载失败');
  } finally {
    loading.executions = false;
  }
};

const loadAll = () => {
  fetchNodes();
  fetchSchedules();
  fetchExecutions();
};

onMounted(loadAll);

const isLoading = computed(() => loading.nodes || loading.schedules || loading.executions || loading.runtimes);

const summaryCards = computed(() => {
  const totalNodes = nodes.value.length;
  const onlineNodes = nodes.value.filter((n) => n.status === 'online').length;
  const offlineNodes = totalNodes - onlineNodes;
  const totalExecutions = aggregates.value?.total_count ?? 0;
  const successRate = aggregates.value ? `${(aggregates.value.success_rate ?? 0).toFixed(1)}%` : '--';
  return [
    { label: '探针总数', value: totalNodes, description: `在线 ${onlineNodes} 个` },
    { label: '离线/异常', value: offlineNodes, description: '需关注心跳' },
    { label: '近 24h 执行', value: totalExecutions, description: '调度执行次数' },
    { label: '成功率', value: successRate, description: '近 24h' },
  ];
});

const nodeRows = computed(() => {
  return nodes.value.map((node) => {
    const runtime = runtimeByNode[node.id];
    const delaySeconds = runtime?.heartbeat_delay_seconds ?? (node.last_heartbeat_at ? dayjs().diff(dayjs(node.last_heartbeat_at), 'second') : null);
    const metrics = runtime?.resource_metrics as Record<string, number> | undefined;
    const queueDepth = Number(runtime?.resource_metrics?.task_queue_depth ?? runtime?.resource_metrics?.queue_depth ?? 0);
    const queueCapacity = Number(runtime?.resource_metrics?.queue_capacity ?? runtime?.resource_metrics?.capacity ?? 0);
    const enrichedMetrics: Record<string, number> = {
      ...(metrics as Record<string, number> | undefined),
      task_queue_depth: queueDepth,
      queue_capacity: queueCapacity,
    };
    return {
      id: node.id,
      name: node.name,
      location: node.location,
      status: node.status,
      heartbeat_delay_seconds: delaySeconds,
      metrics: enrichedMetrics,
      schedule_count: schedules.value.filter((s) => s.probes.some((p) => p.id === node.id)).length,
    };
  });
});

const latencyRanking = computed(() =>
  nodeRows.value
    .filter((n) => n.heartbeat_delay_seconds)
    .sort((a, b) => (b.heartbeat_delay_seconds ?? 0) - (a.heartbeat_delay_seconds ?? 0))
    .slice(0, 5),
);

const failureRanking = computed(() => {
  const failureMap = new Map<string, { id: string; name: string; failed: number }>();
  executions.value
    .filter((item) => item.status === 'failed' || item.status === 'missed')
    .forEach((item) => {
      if (!item.probe) return;
      const current = failureMap.get(item.probe.id) || { id: item.probe.id, name: item.probe.name, failed: 0 };
      current.failed += 1;
      failureMap.set(item.probe.id, current);
    });
  return Array.from(failureMap.values()).sort((a, b) => b.failed - a.failed).slice(0, 5);
});

const recentExecutions = computed(() => executions.value.slice(0, 5));
const statusAggregations = computed(() => {
  const counts = aggregates.value?.status_counts || {};
  return {
    succeeded: counts.succeeded ?? counts.SUCCEEDED ?? 0,
    failed: counts.failed ?? counts.FAILED ?? 0,
    missed: counts.missed ?? counts.MISSED ?? 0,
  };
});
const executionTotal = computed(() => aggregates.value?.total_count ?? 0);
const manualSchedules = computed(
  () => schedules.value.filter((s) => s.source_type === 'manual').length
);

const goTo = (path: string) => router.push(path);
const goToNode = (id: string) => router.push('/probes/nodes');
</script>

<style scoped>
.probe-center-page {
  width: 100%;
  padding: 0 16px 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
  border-radius: 12px;
}

.heading-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.header__title {
  font-weight: 600;
  color: var(--oa-text-primary);
  font-size: 14px;
}

.heading-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-left: auto;
}

.toolbar-button {
  border-radius: 8px;
  height: 32px;
  padding: 0 12px;
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--oa-border-light);
  border-radius: 8px;
  background: var(--oa-bg-panel);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
  box-shadow: var(--oa-shadow-sm);
  user-select: none;
}

.refresh-card:hover {
  border-color: var(--oa-color-primary-light);
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.12);
  transform: translateY(-1px);
}

.refresh-icon.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.panel-grid {
  width: 100%;
}

.probe-center-page :deep(.panel-card) {
  border-radius: 12px;
  border: 1px solid var(--oa-border-color);
  box-shadow: var(--oa-shadow-sm);
  overflow: hidden;
}

.probe-center-page :deep(.panel-card .el-card__header) {
  padding: 14px 16px;
  border-bottom: 1px solid var(--oa-border-light);
  margin: 0;
}

.probe-center-page :deep(.panel-card .el-card__body) {
  padding: 16px;
}
.probe-center-page :deep(.card-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.probe-center-page :deep(.card-header h3) {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--oa-text-primary);
}
.probe-center-page :deep(.card-header p) {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--oa-text-secondary);
}
.strategy-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
@media (max-width: 768px) {
  .page-heading {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
