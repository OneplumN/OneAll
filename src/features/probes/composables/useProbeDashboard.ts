import type { EChartsOption } from 'echarts';
import { ElMessage } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';

import {
  fetchProbeHealth,
  fetchProbeMetricsHistory,
  listProbeNodes,
  type ProbeHealthItem,
  type ProbeMetricsHistoryResponse,
  type ProbeNodeRecord,
} from '@/features/probes/api/probeNodeApi';
import {
  buildCpuTrendOption,
  buildMemoryTrendOption,
  buildQueueTrendOption,
} from '@/features/probes/mappers/metricsChartOptions';
import { copyTextWithFallback } from '@/shared/utils/clipboard';

export function useProbeDashboard() {
  type ProbeNode = ProbeNodeRecord;

  const probes = ref<ProbeNode[]>([]);
  const loading = reactive({ nodes: false });
  const runtimeVisible = ref(false);
  const currentProbe = ref<ProbeNode | null>(null);
  const searchText = ref('');
  const healthById = reactive<Record<string, ProbeHealthItem | null>>({});
  const chartsProbe = ref<ProbeNode | null>(null);
  const metricsHistory = ref<ProbeMetricsHistoryResponse | null>(null);
  const loadingCharts = reactive({ metrics: false });

  const filteredProbes = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();
    if (!keyword) return probes.value;
    return probes.value.filter((probe) => {
      return (
        probe.name.toLowerCase().includes(keyword) ||
        (probe.ip_address ?? '').toLowerCase().includes(keyword) ||
        probe.id.toLowerCase().includes(keyword)
      );
    });
  });

  const cpuTrendOption = computed<EChartsOption | null>(() => buildCpuTrendOption(metricsHistory.value));
  const memoryTrendOption = computed<EChartsOption | null>(() => buildMemoryTrendOption(metricsHistory.value));
  const queueTrendOption = computed<EChartsOption | null>(() => buildQueueTrendOption(metricsHistory.value));

  const loadNodes = async () => {
    loading.nodes = true;
    try {
      const [nodes, healthResp] = await Promise.all([
        listProbeNodes(),
        fetchProbeHealth({ hours: 1, interval_minutes: 15 })
      ]);
      probes.value = nodes;

      Object.keys(healthById).forEach((key) => {
        delete healthById[key];
      });
      (healthResp.items || []).forEach((item) => {
        healthById[item.id] = item;
      });
    } catch (error) {
      ElMessage.error('探针节点加载失败');
    } finally {
      loading.nodes = false;
    }
  };

  const loadMetricsHistory = async (probeId: string) => {
    loadingCharts.metrics = true;
    try {
      metricsHistory.value = await fetchProbeMetricsHistory(probeId, { hours: 6, interval_minutes: 1 });
    } catch (error) {
      ElMessage.error('加载节点运行历史失败');
    } finally {
      loadingCharts.metrics = false;
    }
  };

  const handleRowClick = (probe: ProbeNode) => {
    chartsProbe.value = probe;
    void loadMetricsHistory(probe.id);
  };

  const openRuntime = (probe: ProbeNode) => {
    runtimeVisible.value = true;
    currentProbe.value = probe;
  };

  const copyNodeId = async (id: string) => {
    try {
      await copyTextWithFallback(id);
      ElMessage.success('节点 ID 已复制');
    } catch (error) {
      ElMessage.success('节点 ID 已复制');
    }
  };

  onMounted(() => {
    void loadNodes();
  });

  return {
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
    probes,
    queueTrendOption,
    runtimeVisible,
    searchText,
  };
}
