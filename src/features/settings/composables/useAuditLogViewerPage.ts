import dayjs from 'dayjs';
import { ElMessage } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';

import type {
  AuditLogEntry,
  AuditLogPagination,
} from '@/features/settings/api/settingsApi';
import { fetchAuditLogs } from '@/features/settings/api/settingsApi';
import { copyTextWithFallback } from '@/shared/utils/clipboard';

export function useAuditLogViewerPage() {
  const logs = ref<AuditLogEntry[]>([]);
  const pagination = reactive<AuditLogPagination>({ page: 1, page_size: 20, total: 0 });
  const loading = ref(false);
  const error = ref<string | null>(null);

  const filters = reactive({
    actor: '',
    target_type: '',
  });

  function coerceDate(value: unknown): Date | null {
    if (value instanceof Date) {
      return Number.isNaN(value.getTime()) ? null : value;
    }
    if (typeof value === 'number') {
      const parsed = new Date(value);
      return Number.isNaN(parsed.getTime()) ? null : parsed;
    }
    if (typeof value === 'string') {
      const candidate = value.includes(' ') && !value.includes('T') ? value.replace(' ', 'T') : value;
      const parsed = new Date(candidate);
      return Number.isNaN(parsed.getTime()) ? null : parsed;
    }
    return null;
  }

  const dateRangeRaw = ref<unknown>(null);
  const dateRange = computed<[Date, Date] | null>({
    get() {
      if (!dateRangeRaw.value) return null;
      if (!Array.isArray(dateRangeRaw.value) || dateRangeRaw.value.length !== 2) return null;
      const [startValue, endValue] = dateRangeRaw.value as [unknown, unknown];
      const startDate = coerceDate(startValue);
      const endDate = coerceDate(endValue);
      if (!startDate || !endDate) return null;
      return [startDate, endDate];
    },
    set(value) {
      dateRangeRaw.value = value;
    },
  });

  const pageSizeOptions = [10, 20, 50];
  const defaultStartTime = new Date(2000, 0, 1, 0, 0, 0);
  const defaultEndTime = new Date(2000, 0, 1, 23, 59, 59);

  const dateShortcuts = computed(() => [
    {
      text: '最近 24 小时',
      value: () => {
        const end = dayjs();
        const start = end.subtract(1, 'day');
        return [start.toDate(), end.toDate()];
      },
    },
    {
      text: '最近 7 天',
      value: () => {
        const end = dayjs();
        const start = end.subtract(7, 'day');
        return [start.toDate(), end.toDate()];
      },
    },
  ]);

  async function fetchLogs(page = 1) {
    loading.value = true;
    error.value = null;
    try {
      const params: Record<string, unknown> = {
        page,
        page_size: pagination.page_size,
      };

      if (filters.actor) params.actor = filters.actor;
      if (filters.target_type) params.target_type = filters.target_type;
      if (dateRange.value) {
        params.start = dateRange.value[0].toISOString();
        params.end = dateRange.value[1].toISOString();
      }

      const data = await fetchAuditLogs(params);
      logs.value = data.results;
      pagination.page = Number(data.pagination.page) || 1;
      pagination.page_size = Number(data.pagination.page_size) || pagination.page_size;
      pagination.total = Number(data.pagination.total) || 0;
    } catch {
      error.value = '无法加载操作日志，请稍后重试。';
    } finally {
      loading.value = false;
    }
  }

  function handleSearch() {
    void fetchLogs(1);
  }

  function handlePageChange(page: number) {
    void fetchLogs(page);
  }

  function handlePageSizeChange(size: number) {
    pagination.page_size = size;
    void fetchLogs(1);
  }

  function resetFilters() {
    filters.actor = '';
    filters.target_type = '';
    dateRange.value = null;
    void fetchLogs(1);
  }

  function formatDate(value: string): string {
    if (!value) return '--';
    const parsed = dayjs(value);
    return parsed.isValid() ? parsed.format('YYYY-MM-DD HH:mm:ss') : value;
  }

  function tagType(result: string): string {
    const normalized = result.toLowerCase();
    if (['success', 'ok', 'completed'].includes(normalized)) return 'success';
    if (['warning', 'partial'].includes(normalized)) return 'warning';
    return 'danger';
  }

  const detailVisible = ref(false);
  const activeLog = ref<AuditLogEntry | null>(null);

  function openDetail(entry: AuditLogEntry) {
    activeLog.value = entry;
    detailVisible.value = true;
  }

  function formatJson(value: unknown): string {
    if (!value) return '—';
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }

  async function copyDetail() {
    if (!activeLog.value) return;
    try {
      await copyTextWithFallback(formatJson(activeLog.value));
      ElMessage.success('已复制');
    } catch {
      ElMessage.error('复制失败，请手动选择复制');
    }
  }

  function refresh() {
    void fetchLogs(pagination.page);
  }

  onMounted(() => {
    void fetchLogs();
  });

  return {
    logs,
    pagination,
    loading,
    error,
    filters,
    dateRange,
    pageSizeOptions,
    defaultStartTime,
    defaultEndTime,
    dateShortcuts,
    handleSearch,
    handlePageChange,
    handlePageSizeChange,
    resetFilters,
    formatDate,
    tagType,
    detailVisible,
    activeLog,
    openDetail,
    formatJson,
    copyDetail,
    refresh,
  };
}
