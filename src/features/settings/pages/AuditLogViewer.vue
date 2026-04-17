<template>
  <SettingsPageShell
    section-title="用户与权限"
    breadcrumb="审计日志"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
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
    </template>

    <el-alert
      v-if="error"
      type="error"
      show-icon
      :closable="false"
      class="oa-inline-alert"
    >
      {{ error }}
    </el-alert>

    <div class="oa-list-page">
      <div class="page-toolbar page-toolbar--panel">
        <div class="page-toolbar__left" />
        <div class="page-toolbar__right">
          <el-input
            v-model="filters.actor"
            placeholder="操作者 ID"
            clearable
            class="pill-input oa-input-sm"
            @keyup.enter="handleSearch"
          />
          <el-input
            v-model="filters.target_type"
            placeholder="目标类型（如 monitoring.request）"
            clearable
            class="pill-input oa-input-md"
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
            class="pill-input oa-input-range"
          />
          <el-button
            :loading="loading"
            @click="resetFilters"
          >
            重置
          </el-button>
          <el-button
            class="toolbar-button toolbar-button--primary"
            type="primary"
            :loading="loading"
            @click="handleSearch"
          >
            查询
          </el-button>
        </div>
      </div>

      <div class="oa-table-panel">
        <div class="oa-table-panel__card">
          <el-table
            v-loading="loading"
            :data="logs"
            class="oa-table"
            height="100%"
            stripe
            data-test="audit-log-table"
            empty-text="暂无日志"
          >
            <el-table-column
              prop="occurred_at"
              label="时间"
              width="180"
            >
              <template #default="{ row }">
                {{ formatDate(row.occurred_at) }}
              </template>
            </el-table-column>
            <el-table-column
              label="操作者"
              width="200"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span v-if="row.actor">
                  {{ row.actor.display_name || row.actor.username }}
                  <span
                    v-if="row.actor.username && row.actor.display_name"
                    class="oa-table-meta"
                  >（{{ row.actor.username }}）</span>
                </span>
                <span v-else>系统</span>
              </template>
            </el-table-column>
            <el-table-column
              prop="action"
              label="操作"
              min-width="220"
              show-overflow-tooltip
            />
            <el-table-column
              label="目标"
              min-width="240"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span>{{ row.target_type || '—' }}</span>
                <span
                  v-if="row.target_id"
                  class="oa-table-meta"
                > · ID: {{ row.target_id }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="结果"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  :type="tagType(row.result)"
                  size="small"
                >
                  {{ row.result }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="详情"
              width="120"
              fixed="right"
              align="center"
            >
              <template #default="{ row }">
                <el-button
                  text
                  size="small"
                  class="oa-table-action oa-table-action--primary"
                  @click="openDetail(row)"
                >
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="oa-panel-footer">
        <div class="oa-panel-footer__left">
          <div class="oa-panel-stats">
            共 {{ pagination.total }} 条
          </div>
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            class="repository-pagination__sizes"
            :total="pagination.total"
            :page-sizes="pageSizeOptions"
            layout="sizes"
            background
            :disabled="loading"
            data-test="audit-log-pagination-sizes"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
        <div class="oa-panel-footer__right">
          <el-pagination
            v-model:current-page="pagination.page"
            class="repository-pagination__pager"
            :page-size="pagination.page_size"
            :total="pagination.total"
            layout="prev, pager, next"
            background
            :disabled="loading"
            data-test="audit-log-pagination"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <AuditLogDetailDrawer
      v-model:visible="detailVisible"
      :log="activeLog"
      :format-date="formatDate"
      :tag-type="tagType"
      :format-json="formatJson"
      @copy="copyDetail"
    />
  </SettingsPageShell>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue';
import AuditLogDetailDrawer from '@/features/settings/components/AuditLogDetailDrawer.vue';
import { useAuditLogViewerPage } from '@/features/settings/composables/useAuditLogViewerPage';
import SettingsPageShell from '@/features/settings/components/SettingsPageShell.vue';

const {
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
} = useAuditLogViewerPage();
</script>

<style scoped>
@import '../styles/settings-detail.scss';
</style>
