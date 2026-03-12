<template>
  <div class="history-page">
    <header class="page-header">
      <div class="page-title">
        <span class="header__title">拨测历史记录</span>
      </div>
      <div class="header-actions">
        <div class="refresh-card" @click="refresh">
          <el-icon class="refresh-icon" :class="{ spinning: loading }"><Refresh /></el-icon>
          <span>刷新</span>
        </div>
      </div>
    </header>

    <div class="page-body">
      <div class="filter-bar">
        <el-form :model="filterForm" label-width="70px" class="filters-inline">
          <el-form-item label="状态">
            <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 180px">
              <el-option
                v-for="option in statusOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="协议">
            <el-select v-model="filterForm.protocol" placeholder="全部" clearable style="width: 180px">
              <el-option
                v-for="option in protocolOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="目标">
            <el-input
              v-model="filterForm.target"
              placeholder="输入目标"
              clearable
              @keyup.enter="submitFilters"
              style="width: 220px"
            />
          </el-form-item>
          <el-form-item label="探针">
            <el-select
              v-model="filterForm.probe_id"
              placeholder="选择或输入探针"
              clearable
              filterable
              allow-create
              default-first-option
              style="width: 220px"
            >
              <el-option
                v-for="option in probeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="执行时间">
            <el-date-picker
              v-model="timeRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DDTHH:mm:ss[Z]"
              :shortcuts="dateShortcuts"
              unlink-panels
              style="width: 320px"
            />
          </el-form-item>
          <div class="filter-actions-inline">
            <el-button @click="resetFilters">重置</el-button>
            <el-button type="primary" @click="submitFilters">查询</el-button>
          </div>
        </el-form>
      </div>
      <div class="table-section">
        <div class="table-wrapper">
          <el-card shadow="never" class="table-card" :body-style="{ padding: '0', height: '100%' }">
            <el-table
              :data="items"
              v-loading="loading"
              class="history-table"
              empty-text="暂无拨测记录"
              stripe
              size="small"
              :header-cell-style="tableHeaderStyle"
              :cell-style="tableCellStyle"
              border
              height="100%"
            >
              <el-table-column label="目标" min-width="220">
                <template #default="{ row }">
                  {{ row.schedule?.target ?? '—' }}
                </template>
              </el-table-column>
              <el-table-column label="协议" width="120">
                <template #default="{ row }">
                  {{ row.schedule?.protocol ?? '—' }}
                </template>
              </el-table-column>
              <el-table-column label="状态" width="140">
                <template #default="{ row }">
                  <el-tag :type="statusTagType(row.status)" size="small">{{ translateStatus(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="response_time_ms" label="响应(ms)" width="140">
                <template #default="{ row }">
                  {{ row.response_time_ms ?? '--' }}
                </template>
              </el-table-column>
              <el-table-column prop="status_code" label="状态码" width="120">
                <template #default="{ row }">
                  {{ row.status_code ?? '--' }}
                </template>
              </el-table-column>
              <el-table-column label="探针节点" min-width="200">
                <template #default="{ row }">
                  <div v-if="row.probe">
                    <strong>{{ row.probe.name }}</strong>
                    <div class="probe-meta">{{ row.probe.location }} · {{ row.probe.network_type }}</div>
                  </div>
                  <span v-else>未指定</span>
                </template>
              </el-table-column>
              <el-table-column label="时间线" min-width="240">
                <template #default="{ row }">
                  <div class="time-col">
                    <span>调度：{{ formatDate(row.scheduled_at) }}</span>
                    <span v-if="row.started_at">开始：{{ formatDate(row.started_at) }}</span>
                    <span v-if="row.finished_at">完成：{{ formatDate(row.finished_at) }}</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>

        <div class="table-skeleton" v-if="loading">
          <el-skeleton v-for="n in 5" :key="n" animated :rows="3" />
        </div>

      </div>
    </div>

    <div class="page-footer" v-if="!loading">
      <div class="footer-left">
        <div class="table-total">共 {{ pagination.total_items }} 条</div>
        <el-pagination
          class="pager-sizes"
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total_items"
          :page-sizes="[10, 20, 50]"
          layout="sizes"
          background
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
      <div class="footer-right">
        <el-pagination
          class="pager-main"
          v-model:current-page="pagination.page"
          :page-size="pagination.page_size"
          :total="pagination.total_items"
          layout="prev, pager, next"
          background
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { Refresh, DataBoard, CircleCheck, WarningFilled, TrendCharts, Filter } from '@element-plus/icons-vue';
import {
  fetchProbeScheduleExecutions,
  type ProbeScheduleExecutionAggregates,
  type ProbeScheduleExecutionFilters,
  type ProbeScheduleExecutionListResponse,
  type ProbeScheduleExecutionRecord,
  type ProbeScheduleExecutionPagination
} from '@/services/probeScheduleExecutionApi';

const loading = ref(false);
const items = ref<ProbeScheduleExecutionRecord[]>([]);
const aggregates = reactive<ProbeScheduleExecutionAggregates>({
  total_count: 0,
  status_counts: {},
  average_response_time_ms: null,
  success_rate: null
});
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
const popoverVisible = ref(false);
const probeOptions = ref<{ label: string; value: string }[]>([]);
const timeRange = ref<string[] | null>(null);

const statusOptions = [
  { value: 'scheduled', label: '待执行' },
  { value: 'running', label: '执行中' },
  { value: 'succeeded', label: '成功' },
  { value: 'failed', label: '失败' },
  { value: 'missed', label: '错过执行' }
];

const protocolOptions = [
  { value: 'HTTP', label: 'HTTP' },
  { value: 'HTTPS', label: 'HTTPS' },
  { value: 'Telnet', label: 'Telnet' },
  { value: 'WSS', label: 'WebSocket Secure' },
  { value: 'TCP', label: 'TCP' },
  { value: 'CERTIFICATE', label: '证书检测' }
];

const statusCounts = computed(() => {
  const counts = aggregates.status_counts || {};
  return {
    succeeded: counts.succeeded ?? counts.SUCCEEDED ?? 0,
    failed: counts.failed ?? counts.FAILED ?? 0,
    timeout: counts.timeout ?? counts.TIMEOUT ?? 0,
    missed: counts.missed ?? counts.MISSED ?? 0
  };
});

const failedAndTimeout = computed(() => statusCounts.value.failed + statusCounts.value.timeout + statusCounts.value.missed);

function translateStatus(status: string) {
  switch (status) {
    case 'succeeded':
    case 'SUCCEEDED':
      return '成功';
    case 'failed':
    case 'FAILED':
      return '失败';
    case 'timeout':
    case 'TIMEOUT':
      return '超时';
    case 'missed':
    case 'MISSED':
      return '错过执行';
    case 'running':
    case 'RUNNING':
      return '执行中';
    case 'scheduled':
    case 'SCHEDULED':
      return '待执行';
    default:
      return status;
  }
}

function statusTagType(status: string) {
  if (status.toLowerCase() === 'succeeded') return 'success';
  if (status.toLowerCase() === 'failed') return 'danger';
  if (status.toLowerCase() === 'missed') return 'danger';
  if (status.toLowerCase() === 'timeout') return 'warning';
  if (status.toLowerCase() === 'running') return 'info';
  return 'info';
}

function formatDate(value?: string | null) {
  if (!value) return '--';
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss');
}

function formatAverage(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === '') return '--';
  return Number(value).toFixed(0);
}

function formatSuccessRate(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === '') return '--';
  const numberValue = typeof value === 'number' ? value : Number(value);
  return `${numberValue.toFixed(1)}%`;
}

async function loadHistory() {
  loading.value = true;
  try {
    const response = await fetchProbeScheduleExecutions(filterState.value);
    applyHistoryResponse(response);
  } catch (error) {
    ElMessage.error('加载拨测历史失败，请稍后重试');
  } finally {
    loading.value = false;
  }
}

function applyHistoryResponse(response: ProbeScheduleExecutionListResponse) {
  items.value = response.items;
  aggregates.total_count = response.aggregates.total_count;
  aggregates.status_counts = response.aggregates.status_counts;
  aggregates.average_response_time_ms = response.aggregates.average_response_time_ms ?? null;
  aggregates.success_rate = response.aggregates.success_rate ?? null;
  pagination.page = response.pagination.page;
  pagination.page_size = response.pagination.page_size;
  pagination.total_items = response.pagination.total_items;
  pagination.total_pages = response.pagination.total_pages;
  const probeSet = new Map<string, string>();
  response.items.forEach((row) => {
    if (row.probe?.name) {
      probeSet.set(row.probe.name, row.probe.name);
    }
  });
  probeOptions.value = Array.from(probeSet.entries()).map(([value, label]) => ({ value, label }));
}

function handlePageChange(page: number) {
  filterState.value = {
    ...filterState.value,
    page
  };
  loadHistory();
}

function handlePageSizeChange(size: number) {
  filterState.value = {
    ...filterState.value,
    page_size: size,
    page: 1
  };
  loadHistory();
}

const tableHeaderStyle = () => ({
  background: 'var(--oa-bg-muted)',
  fontWeight: 600,
  color: 'var(--oa-text-secondary)',
  height: '44px'
});

const tableCellStyle = () => ({
  padding: '8px 10px',
  fontSize: '13px'
});

function refresh() {
  loadHistory();
}

onMounted(() => {
  loadHistory();
});

const activeTags = computed(() => {
  const tags: { label: string; value: string }[] = [];
  if (filterState.value.status) {
    const match = statusOptions.find((opt) => opt.value === filterState.value.status);
    tags.push({ label: '状态', value: match?.label ?? filterState.value.status });
  }
  if (filterState.value.protocol) {
    const match = protocolOptions.find((opt) => opt.value === filterState.value.protocol);
    tags.push({ label: '协议', value: match?.label ?? filterState.value.protocol });
  }
  if (filterState.value.target) {
    tags.push({ label: '目标', value: filterState.value.target });
  }
  if (filterState.value.probe_id) {
    tags.push({ label: '探针', value: filterState.value.probe_id });
  }
  if (filterState.value.started_after && filterState.value.started_before) {
    tags.push({
      label: '执行时间',
      value: `${filterState.value.started_after?.slice(0, 10)} ~ ${filterState.value.started_before?.slice(0, 10)}`
    });
  }
  return tags;
});

const dateShortcuts = computed(() => [
  {
    text: '最近 24 小时',
    value: () => {
      const end = dayjs();
      const start = end.subtract(1, 'day');
      return [
        start.format('YYYY-MM-DDTHH:mm:ss[Z]'),
        end.format('YYYY-MM-DDTHH:mm:ss[Z]')
      ];
    }
  },
  {
    text: '最近 7 天',
    value: () => {
      const end = dayjs();
      const start = end.subtract(7, 'day');
      return [
        start.format('YYYY-MM-DDTHH:mm:ss[Z]'),
        end.format('YYYY-MM-DDTHH:mm:ss[Z]')
      ];
    }
  }
]);

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
  loadHistory();
  popoverVisible.value = false;
}

function resetFilters() {
  filterForm.target = '';
  filterForm.status = undefined;
  filterForm.protocol = undefined;
  filterForm.probe_id = undefined;
  filterForm.page_size = 20;
  timeRange.value = null;
  filterState.value = { page: 1, page_size: 20 };
  loadHistory();
  popoverVisible.value = false;
}
</script>

<style scoped>
.history-page {
  padding: 0 16px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.filter-bar {
  padding: 8px 0;
}

.filters-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
}

.filters-inline :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-actions-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filters-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 320px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--oa-border-light);
}

.header__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--oa-text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--oa-border-light);
  border-radius: 8px;
  background: var(--oa-bg-panel);
  color: var(--oa-text-primary);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
  box-shadow: var(--oa-shadow-sm);
}

.refresh-card:hover {
  border-color: var(--oa-border-color);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
}

.filter-card {
  cursor: pointer;
  background: var(--oa-color-primary);
  border-color: var(--oa-color-primary);
  color: #fff;
}

.filter-card:hover {
  border-color: var(--oa-color-primary-dark);
  background: var(--oa-color-primary);
  box-shadow: 0 6px 12px rgba(64, 158, 255, 0.16);
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

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  padding: 12px 14px;
  background: var(--oa-bg-panel);
  box-shadow: var(--oa-shadow-sm);
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-card__left {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: var(--oa-bg-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.stat-card__right {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 12px;
}

.stat-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--oa-bg-muted);
  color: var(--oa-text-muted);
  font-size: 18px;
}

.stat-icon.success {
  background: #e9f7ef;
  color: #22c55e;
}

.stat-icon.warning {
  background: #fff5e6;
  color: #f59e0b;
}

.stat-icon.danger {
  background: #fff2f2;
  color: #ef4444;
}

.stat-card .label {
  margin: 0;
  color: var(--oa-text-muted);
  font-size: 13px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sub-value {
  margin: 0;
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.stat-card .value {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.stat-badge {
  position: absolute;
  left: 6px;
  top: 6px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--oa-text-muted);
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.03);
}

.stat-badge.success {
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12);
}

.stat-badge.warning {
  background: #f59e0b;
  box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.12);
}

.stat-badge.danger {
  background: #ef4444;
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.12);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--oa-border-light);
}

.probe-meta {
  color: var(--oneall-text-secondary);
  font-size: 0.85rem;
}

.time-col {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.table-skeleton {
  padding: 12px 0;
  display: grid;
  gap: 12px;
}

.page-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  gap: 12px;
}

.table-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
}

.table-card {
  border: none;
  box-shadow: none;
  background: var(--oa-bg-panel);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.table-card :deep(.el-card__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.history-table {
  flex: 1;
}

.history-table :deep(.el-table__cell) {
  padding: 8px 10px;
  font-size: 13px;
}

.page-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 16px 12px;
  color: var(--oa-text-secondary);
  flex-wrap: wrap;
  border-top: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-right {
  display: flex;
  align-items: center;
  margin-left: auto;
}

.pager-sizes :deep(.el-input__wrapper) {
  padding: 0 10px;
}

.pager-main {
  display: flex;
  align-items: center;
}

.pager-main :deep(.el-pagination__sizes) {
  display: none;
}
</style>
