<template>
  <section class="overview-panel">
    <div class="overview-panel__header">
      <div class="overview-panel__heading">
        <h2 class="overview-panel__title overview-panel__title--sm">
          {{ selectedSystem?.system_name ?? '选择系统查看明细' }}
        </h2>
      </div>

      <div
        v-if="selectedSystem"
        class="detail-summary"
      >
        <div class="detail-summary__item">
          <span>异常域名</span>
          <strong>{{ selectedSystem.abnormal_count }}</strong>
        </div>
        <div class="detail-summary__item">
          <span>总域名</span>
          <strong>{{ selectedSystem.domain_count }}</strong>
        </div>
        <div class="detail-summary__item">
          <span>监控策略</span>
          <strong>{{ selectedSystem.matched_strategy_count }}</strong>
        </div>
        <div class="detail-summary__item detail-summary__item--wide">
          <span>最近检测</span>
          <strong>{{ formatDateTime(selectedSystem.last_checked_at) }}</strong>
        </div>
      </div>
    </div>

    <div
      v-if="!selectedSystem"
      class="overview-panel__empty"
    >
      <el-empty description="选择蜂窝后查看该系统的拨测明细" />
    </div>

    <div
      v-else
      class="oa-table-panel overview-table-panel"
    >
      <div class="oa-table-panel__card">
        <el-table
          :data="selectedItems"
          class="oa-table"
          stripe
          empty-text="当前系统暂无拨测明细"
        >
          <el-table-column
            label="域名"
            min-width="220"
          >
            <template #default="{ row }">
              <div class="table-title-stack">
                <strong class="oa-table-title">{{ displayTarget(row) }}</strong>
                <span class="oa-table-meta">{{ assetMatchLabel(row.asset_match_status) }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column
            label="监控策略"
            min-width="180"
          >
            <template #default="{ row }">
              <div class="table-title-stack">
                <strong class="oa-table-title">{{ row.check_name }}</strong>
                <span class="oa-table-meta">{{ row.protocol }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column
            label="最新状态"
            width="120"
          >
            <template #default="{ row }">
              <span :class="statusTextClass(row.latest_status)">
                {{ statusLabel(row.latest_status) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            label="最近检测"
            min-width="180"
          >
            <template #default="{ row }">
              {{ formatDateTime(row.last_checked_at) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type {
  MonitoringOverviewItem,
  MonitoringOverviewStatus,
  MonitoringOverviewSystem,
} from '@/features/alerts/api/alertsApi';

defineProps<{
  selectedSystem: MonitoringOverviewSystem | null;
  selectedItems: MonitoringOverviewItem[];
  formatDateTime: (value: string | null | undefined) => string;
  statusLabel: (status: MonitoringOverviewStatus) => string;
  statusTextClass: (status: MonitoringOverviewStatus) => string;
  displayTarget: (item: MonitoringOverviewItem) => string;
  assetMatchLabel: (status: string) => string;
}>();
</script>

<style scoped>
.overview-panel {
  background: var(--oa-bg-panel);
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  overflow: hidden;
}

.overview-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.overview-panel__heading {
  min-width: 0;
}

.overview-panel__title {
  margin: 0;
  color: var(--oa-text-primary);
  font-size: var(--oa-font-page-title);
  font-weight: 600;
}

.overview-panel__title--sm {
  font-size: var(--oa-font-section-title);
}

.detail-summary {
  display: flex;
  align-items: stretch;
  gap: 10px;
  flex-wrap: wrap;
}

.detail-summary__item {
  min-width: 110px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--oa-border-light);
  background: var(--oa-bg-muted);
}

.detail-summary__item span {
  color: var(--oa-text-muted);
  font-size: 12px;
}

.detail-summary__item strong {
  color: var(--oa-text-primary);
  font-size: 16px;
}

.detail-summary__item--wide {
  min-width: 180px;
  margin-left: auto;
}

.detail-summary__item--wide strong {
  font-size: 14px;
  line-height: 1.4;
}

.overview-table-panel {
  padding: 0;
  background: var(--oa-bg-panel);
}

.table-title-stack {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.status-text {
  font-weight: 600;
}

.status-text--success {
  color: var(--oa-color-success);
}

.status-text--danger {
  color: var(--oa-color-danger);
}

.status-text--idle {
  color: var(--oa-text-muted);
}

.overview-panel__empty {
  padding: 24px 0;
  background: var(--oa-bg-panel);
}

@media (max-width: 768px) {
  .overview-panel__header {
    padding: 12px;
  }

  .detail-summary {
    width: 100%;
  }

  .detail-summary__item {
    min-width: calc(50% - 5px);
  }

  .detail-summary__item--wide {
    min-width: 100%;
    margin-left: 0;
  }
}
</style>
