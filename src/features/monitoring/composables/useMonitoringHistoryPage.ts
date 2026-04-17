import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';

import {
  fetchProbeScheduleExecutions,
  type ProbeScheduleExecutionFilters,
  type ProbeScheduleExecutionListResponse,
  type ProbeScheduleExecutionPagination,
  type ProbeScheduleExecutionRecord,
} from '@/features/monitoring/api/probeScheduleExecutionApi';
import { listProbeNodes } from '@/features/probes/api/probeNodeApi';
import { createHistoryDateShortcuts } from '@/features/monitoring/utils/monitoringHistoryPresentation';

export function useMonitoringHistoryPage() {
  const loading = ref(false);
  const items = ref<ProbeScheduleExecutionRecord[]>([]);
  const pagination = reactive<ProbeScheduleExecutionPagination>({
    page: 1,
    page_size: 20,
    total_items: 0,
    total_pages: 0
  });

  const filterState = ref<ProbeScheduleExecutionFilters>({
    page: 1,
    page_size: 20
  });

  const filterForm = reactive<ProbeScheduleExecutionFilters>({
    target: '',
    status: undefined,
    protocol: undefined,
    probe_id: undefined,
    page_size: 20
  });

  const probeOptions = ref<{ label: string; value: string }[]>([]);
  const timeRange = ref<string[] | null>(null);
  const dateShortcuts = computed(() => createHistoryDateShortcuts());

  async function loadHistory() {
    loading.value = true;
    try {
      applyHistoryResponse(await fetchProbeScheduleExecutions(filterState.value));
    } catch (error) {
      ElMessage.error('加载执行日志失败，请稍后重试');
    } finally {
      loading.value = false;
    }
  }

  async function loadProbeOptions() {
    try {
      const probes = await listProbeNodes();
      probeOptions.value = probes.map((probe) => ({
        value: probe.id,
        label: [probe.name, probe.location || '未设置', probe.status === 'online' ? '在线' : '离线'].join(' · ')
      }));
    } catch {
      probeOptions.value = [];
    }
  }

  function handlePageChange(page: number) {
    filterState.value = {
      ...filterState.value,
      page
    };
    void loadHistory();
  }

  function handlePageSizeChange(size: number) {
    filterState.value = {
      ...filterState.value,
      page_size: size,
      page: 1
    };
    void loadHistory();
  }

  function refresh() {
    void loadHistory();
  }

  function submitFilters() {
    const payload: ProbeScheduleExecutionFilters = {
      target: filterForm.target?.trim() || undefined,
      status: filterForm.status,
      protocol: filterForm.protocol,
      probe_id: filterForm.probe_id?.trim() || undefined,
      page: 1,
      page_size: filterForm.page_size ?? 20
    };

    if (timeRange.value && timeRange.value.length === 2) {
      payload.started_after = timeRange.value[0];
      payload.started_before = timeRange.value[1];
    } else {
      payload.started_after = undefined;
      payload.started_before = undefined;
    }

    filterState.value = payload;
    void loadHistory();
  }

  function resetFilters() {
    filterForm.target = '';
    filterForm.status = undefined;
    filterForm.protocol = undefined;
    filterForm.probe_id = undefined;
    filterForm.page_size = 20;
    timeRange.value = null;
    filterState.value = { page: 1, page_size: 20 };
    void loadHistory();
  }

  function applyHistoryResponse(response: ProbeScheduleExecutionListResponse) {
    items.value = response.items;
    pagination.page = response.pagination.page;
    pagination.page_size = response.pagination.page_size;
    pagination.total_items = response.pagination.total_items;
    pagination.total_pages = response.pagination.total_pages;
  }

  onMounted(() => {
    void loadProbeOptions();
    void loadHistory();
  });

  return {
    dateShortcuts,
    filterForm,
    handlePageChange,
    handlePageSizeChange,
    items,
    loading,
    pagination,
    probeOptions,
    refresh,
    resetFilters,
    submitFilters,
    timeRange,
  };
}
