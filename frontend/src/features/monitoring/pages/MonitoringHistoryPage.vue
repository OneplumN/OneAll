<template>
  <RepositoryPageShell
    root-title="监控与告警"
    section-title="执行日志"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <div class="history-header-actions">
        <div
          class="refresh-card"
          @click="refresh"
        >
          <el-icon
            class="refresh-icon"
            :class="{ spinning: loading }"
          >
            <Refresh />
          </el-icon>
          <span>刷新</span>
        </div>
      </div>
    </template>

    <div class="oa-list-page">
      <div class="page-toolbar page-toolbar--panel history-toolbar">
        <div class="page-toolbar__left" />
        <div class="page-toolbar__right history-toolbar__filters">
          <el-select
            v-model="filterForm.status"
            placeholder="状态"
            clearable
            class="pill-input narrow-select"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-select
            v-model="filterForm.protocol"
            placeholder="协议"
            clearable
            class="pill-input narrow-select"
          >
            <el-option
              v-for="option in protocolOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-input
            v-model="filterForm.target"
            placeholder="搜索目标 / URL"
            clearable
            class="pill-input history-filter-input"
            @keyup.enter="submitFilters"
          />
          <el-select
            v-model="filterForm.probe_id"
            placeholder="探针节点"
            clearable
            filterable
            class="pill-input history-filter-input"
          >
            <el-option
              v-for="option in probeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-date-picker
            v-model="timeRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DDTHH:mm:ss[Z]"
            :shortcuts="dateShortcuts"
            unlink-panels
            class="pill-input history-date-range"
          />
          <el-button
            class="toolbar-button"
            @click="resetFilters"
          >
            重置
          </el-button>
          <el-button
            class="toolbar-button toolbar-button--primary"
            type="primary"
            @click="submitFilters"
          >
            查询
          </el-button>
        </div>
      </div>

      <div class="oa-table-panel">
        <div class="oa-table-panel__card history-table-card">
          <el-table
            v-loading="loading"
            :data="items"
            class="oa-table history-table"
            empty-text="暂无执行记录"
            stripe
            height="100%"
          >
            <el-table-column
              label="监控策略"
              min-width="180"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span class="oa-table-title">{{ row.schedule?.name ?? '未关联策略' }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="目标"
              min-width="220"
            >
              <template #default="{ row }">
                <span class="oa-table-meta">{{ row.schedule?.target ?? '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="协议"
              width="120"
            >
              <template #default="{ row }">
                <span class="oa-table-meta">{{ row.schedule?.protocol ?? '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="状态"
              width="140"
            >
              <template #default="{ row }">
                <el-tag
                  :type="statusTagType(row.status)"
                  size="small"
                >
                  {{ translateStatus(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="response_time_ms"
              label="响应(ms)"
              width="140"
            >
              <template #default="{ row }">
                {{ row.response_time_ms ?? '--' }}
              </template>
            </el-table-column>
            <el-table-column
              prop="status_code"
              label="状态码"
              width="120"
            >
              <template #default="{ row }">
                {{ row.status_code ?? '--' }}
              </template>
            </el-table-column>
            <el-table-column
              label="探针节点"
              min-width="200"
            >
              <template #default="{ row }">
                <div v-if="row.probe">
                  <strong>{{ row.probe.name }}</strong>
                  <div class="oa-table-meta">
                    {{ row.probe.location }} · {{ row.probe.network_type }}
                  </div>
                </div>
                <span v-else>未指定</span>
              </template>
            </el-table-column>
            <el-table-column
              label="结果摘要"
              min-width="260"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span class="oa-table-meta">{{ summarizeMessage(row.message) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="时间线"
              min-width="240"
            >
              <template #default="{ row }">
                <div class="time-col">
                  <span>调度：{{ formatDate(row.scheduled_at) }}</span>
                  <span v-if="row.started_at">开始：{{ formatDate(row.started_at) }}</span>
                  <span v-if="row.finished_at">完成：{{ formatDate(row.finished_at) }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <template #footer>
      <div
        v-if="!loading"
        class="oa-panel-footer"
      >
        <div class="oa-panel-footer__left">
          <div class="oa-panel-stats">
            共 {{ pagination.total_items }} 条
          </div>
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            class="pager-sizes"
            :total="pagination.total_items"
            :page-sizes="[10, 20, 50]"
            layout="sizes"
            background
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
        <div class="oa-panel-footer__right">
          <el-pagination
            v-model:current-page="pagination.page"
            class="pager-main"
            :page-size="pagination.page_size"
            :total="pagination.total_items"
            layout="prev, pager, next"
            background
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </template>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue';
import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import { useMonitoringHistoryPage } from '@/features/monitoring/composables/useMonitoringHistoryPage';
import {
  executionStatusTagType as statusTagType,
  formatExecutionDate as formatDate,
  monitoringHistoryProtocolOptions as protocolOptions,
  monitoringHistoryStatusOptions as statusOptions,
  summarizeExecutionMessage as summarizeMessage,
  translateExecutionStatus as translateStatus,
} from '@/features/monitoring/utils/monitoringHistoryPresentation';

const {
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
} = useMonitoringHistoryPage();
</script>

<style scoped>
.history-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.history-toolbar__filters {
  gap: 12px;
}

.history-filter-input {
  width: 220px;
}

.history-date-range {
  width: 320px;
}

.history-table-card {
  flex: 1;
  min-height: 0;
}

.time-col {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-meta);
}

.history-table {
  flex: 1;
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

@media (max-width: 1280px) {
  .history-toolbar__filters {
    flex-wrap: wrap;
  }
}
</style>
