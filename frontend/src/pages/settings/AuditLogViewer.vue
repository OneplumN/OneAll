<template>
  <SettingsPageShell section-title="日志" body-padding="0" :panel-bordered="false">
    <template #actions>
      <div class="refresh-card" @click="refresh">
        <el-icon class="refresh-icon" :class="{ spinning: loading }"><Refresh /></el-icon>
        <span>刷新</span>
      </div>
    </template>

    <el-alert v-if="error" type="error" show-icon :closable="false" class="mb-2">
      {{ error }}
    </el-alert>

    <div class="list-page">
      <div class="repository-filters">
        <div class="filters-left" />
        <div class="filters-right">
          <el-input
            v-model="filters.actor"
            placeholder="操作者 ID"
            clearable
            class="pill-input narrow-input"
            @keyup.enter="handleSearch"
          />
          <el-input
            v-model="filters.target_type"
            placeholder="目标类型（如 monitoring.request）"
            clearable
            class="pill-input wide-input"
            @keyup.enter="handleSearch"
          />
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            :shortcuts="dateShortcuts"
            :default-time="[defaultStartTime, defaultEndTime]"
            clearable
            class="pill-input date-input"
          />
          <el-button :loading="loading" @click="resetFilters">重置</el-button>
          <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
        </div>
      </div>

      <div class="repository-table">
        <div class="repository-table__card">
          <el-table
            v-loading="loading"
            :data="logs"
            height="100%"
            stripe
            data-test="audit-log-table"
            empty-text="暂无日志"
            :header-cell-style="tableHeaderStyle"
            :cell-style="tableCellStyle"
          >
            <el-table-column prop="occurred_at" label="时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.occurred_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作者" width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="row.actor">
                  {{ row.actor.display_name || row.actor.username }}
                  <span class="muted" v-if="row.actor.username && row.actor.display_name">（{{ row.actor.username }}）</span>
                </span>
                <span v-else>系统</span>
              </template>
            </el-table-column>
            <el-table-column prop="action" label="操作" min-width="220" show-overflow-tooltip />
            <el-table-column label="目标" min-width="240" show-overflow-tooltip>
              <template #default="{ row }">
                <span>{{ row.target_type || '—' }}</span>
                <span class="muted" v-if="row.target_id"> · ID: {{ row.target_id }}</span>
              </template>
            </el-table-column>
            <el-table-column label="结果" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="tagType(row.result)" size="small">{{ row.result }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="详情" width="120" fixed="right" align="center">
              <template #default="{ row }">
                <el-button text size="small" @click="openDetail(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="repository-table__footer">
        <div class="footer-left">
          <div class="repository-stats">共 {{ pagination.total }} 条</div>
          <el-pagination
            class="repository-pagination__sizes"
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="pagination.total"
            :page-sizes="pageSizeOptions"
            layout="sizes"
            background
            :disabled="loading"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
            data-test="audit-log-pagination-sizes"
          />
        </div>
        <div class="footer-right">
          <el-pagination
            class="repository-pagination__pager"
            v-model:current-page="pagination.page"
            :page-size="pagination.page_size"
            :total="pagination.total"
            layout="prev, pager, next"
            background
            :disabled="loading"
            @current-change="handlePageChange"
            data-test="audit-log-pagination"
          />
        </div>
      </div>
    </div>

    <el-drawer
      v-model="detailVisible"
      title="日志详情"
      size="560px"
      append-to-body
      destroy-on-close
    >
      <div v-if="activeLog" class="drawer-body">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="时间">{{ formatDate(activeLog.occurred_at) }}</el-descriptions-item>
          <el-descriptions-item label="操作者">
            <span v-if="activeLog.actor">
              {{ activeLog.actor.display_name || activeLog.actor.username }}
              <span class="muted" v-if="activeLog.actor.username && activeLog.actor.display_name">
                （{{ activeLog.actor.username }}）
              </span>
            </span>
            <span v-else>系统</span>
          </el-descriptions-item>
          <el-descriptions-item label="操作">{{ activeLog.action }}</el-descriptions-item>
          <el-descriptions-item label="目标">{{ activeLog.target_type || '—' }}{{ activeLog.target_id ? ` / ${activeLog.target_id}` : '' }}</el-descriptions-item>
          <el-descriptions-item label="结果">
            <el-tag :type="tagType(activeLog.result)" size="small">{{ activeLog.result }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="drawer-section">
          <div class="drawer-section__title">Metadata</div>
          <pre class="json-block">{{ formatJson(activeLog.metadata) }}</pre>
        </div>
      </div>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" plain :disabled="!activeLog" @click="copyDetail">复制 JSON</el-button>
        </div>
      </template>
    </el-drawer>
  </SettingsPageShell>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { ElMessage } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { computed, onMounted, reactive, ref } from 'vue';

import apiClient from '@/services/apiClient';
import SettingsPageShell from './components/SettingsPageShell.vue';

interface AuditLogActor {
  id: string;
  username: string;
  display_name: string;
}

interface AuditLogEntry {
  id: string;
  actor: AuditLogActor | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  result: string;
  metadata: Record<string, unknown> | null;
  occurred_at: string;
}

interface AuditLogPagination {
  page: number;
  page_size: number;
  total: number;
}

const logs = ref<AuditLogEntry[]>([]);
const pagination = reactive<AuditLogPagination>({ page: 1, page_size: 20, total: 0 });
const loading = ref(false);
const error = ref<string | null>(null);

const filters = reactive({
  actor: '',
  target_type: ''
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
  }
});

const pageSizeOptions = [10, 20, 50];

const defaultStartTime = new Date(2000, 0, 1, 0, 0, 0);
const defaultEndTime = new Date(2000, 0, 1, 23, 59, 59);

const tableHeaderStyle = () => ({
  background: 'var(--oa-bg-muted)',
  color: 'var(--oa-text-secondary)',
  fontWeight: 600,
  height: '44px'
});

const tableCellStyle = () => ({
  height: '44px',
  padding: '6px 8px'
});

const dateShortcuts = computed(() => [
  {
    text: '最近 24 小时',
    value: () => {
      const end = dayjs();
      const start = end.subtract(1, 'day');
      return [start.toDate(), end.toDate()];
    }
  },
  {
    text: '最近 7 天',
    value: () => {
      const end = dayjs();
      const start = end.subtract(7, 'day');
      return [start.toDate(), end.toDate()];
    }
  }
]);

async function fetchLogs(page = 1) {
  loading.value = true;
  error.value = null;
  try {
    const params: Record<string, unknown> = {
      page,
      page_size: pagination.page_size
    };

    if (filters.actor) params.actor = filters.actor;
    if (filters.target_type) params.target_type = filters.target_type;
    if (dateRange.value) {
      params.start = dateRange.value[0].toISOString();
      params.end = dateRange.value[1].toISOString();
    }

    const { data } = await apiClient.get<{ results: AuditLogEntry[]; pagination: AuditLogPagination }>(
      '/audit/logs',
      { params }
    );

    logs.value = data.results;
    pagination.page = Number(data.pagination.page) || 1;
    pagination.page_size = Number(data.pagination.page_size) || pagination.page_size;
    pagination.total = Number(data.pagination.total) || 0;
  } catch (err) {
    error.value = '无法加载操作日志，请稍后重试。';
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  fetchLogs(1);
}

function handlePageChange(page: number) {
  fetchLogs(page);
}

function handlePageSizeChange(size: number) {
  pagination.page_size = size;
  fetchLogs(1);
}

function resetFilters() {
  filters.actor = '';
  filters.target_type = '';
  dateRange.value = null;
  fetchLogs(1);
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
    await navigator.clipboard.writeText(formatJson(activeLog.value));
    ElMessage.success('已复制');
  } catch {
    ElMessage.error('复制失败，请手动选择复制');
  }
}

function refresh() {
  fetchLogs(pagination.page);
}

onMounted(() => {
  fetchLogs();
});
</script>

<style scoped>
.mb-2 {
  margin-bottom: 1rem;
}

.list-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.repository-filters {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.filters-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filters-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  flex-wrap: wrap;
}

.narrow-input {
  width: 180px;
}

.wide-input {
  width: 260px;
}

.date-input {
  width: 360px;
}

.pill-input :deep(.el-input__wrapper),
.pill-input :deep(.el-select__wrapper) {
  border-radius: 999px;
  padding-left: 0.85rem;
  background: var(--oa-filter-control-bg);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}

.repository-table {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--oa-bg-panel);
  padding: 0 16px 12px;
}

.repository-table__card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: none;
}

.repository-table__card :deep(.el-table) {
  flex: 1;
  overflow-x: hidden;
}

.repository-table__card :deep(.el-table__inner-wrapper) {
  border: none !important;
}

.repository-table__card :deep(.el-table__cell) {
  padding: 8px 10px;
}

.repository-table__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 0px 16px 12px;
  color: var(--oa-text-secondary);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-right {
  margin-left: auto;
}

.repository-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.muted {
  color: var(--oa-text-muted);
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.08);
  cursor: pointer;
  user-select: none;
}

.refresh-card:hover {
  background: rgba(15, 23, 42, 0.06);
}

.refresh-icon {
  transition: transform 0.35s ease;
}

.refresh-icon.spinning {
  animation: spinning 0.9s linear infinite;
}

@keyframes spinning {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drawer-section__title {
  font-weight: 600;
}

.json-block {
  margin: 0;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--oa-border-light);
  background: #0b1220;
  color: #e5e7eb;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 360px;
  overflow: auto;
}

.drawer-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}
</style>
