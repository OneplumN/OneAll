<template>
  <PageWrapper :loading="pageLoading">
    <RepositoryPageShell
      root-title="监控与告警"
      section-title="拨测可视化"
      shell-padding="0"
      body-padding="0"
      :panel-bordered="false"
      scroll-mode="page"
    >
      <template #actions>
        <div class="overview-actions">
          <div
            class="refresh-card"
            @click="refreshOverview"
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

      <div class="oa-list-page overview-page">
        <el-alert
          v-if="overviewError"
          type="error"
          :closable="false"
          show-icon
          class="oa-inline-alert"
        >
          {{ overviewError }}
        </el-alert>

        <div class="overview-panels">
          <section class="overview-panel">
            <div class="overview-panel__header">
              <div class="overview-panel__heading">
                <h1 class="overview-panel__title">
                  拨测蜂窝总览
                </h1>
              </div>
            </div>

            <div class="overview-panel__body overview-panel__body--honeycomb">
              <DetectionHoneycomb
                v-if="overviewSystems.length"
                :cells="honeycombCells"
                :columns="honeycombColumns"
                :selected-id="selectedSystemName"
                :size="honeycombSize"
                :compact="isHoneycombCompact"
                @select="handleSystemSelect"
              />

              <el-empty
                v-else-if="!loading && !overviewError"
                description="暂无系统拨测数据"
                class="system-empty"
              />
            </div>
          </section>

          <OverviewSystemDetailPanel
            :selected-system="selectedSystem"
            :selected-items="selectedItems"
            :format-date-time="formatDateTime"
            :status-label="statusLabel"
            :status-text-class="statusTextClass"
            :display-target="displayTarget"
            :asset-match-label="assetMatchLabel"
          />
        </div>
      </div>
    </RepositoryPageShell>
  </PageWrapper>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue';

import OverviewSystemDetailPanel from '@/features/dashboard/components/OverviewSystemDetailPanel.vue';
import PageWrapper from '@/shared/components/layout/PageWrapper';
import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import DetectionHoneycomb from '@/features/dashboard/components/DetectionHoneycomb.vue';
import { useHomeOverviewPage } from '@/features/dashboard/composables/useHomeOverviewPage';

const {
  loading,
  overviewError,
  pageLoading,
  overviewSystems,
  honeycombCells,
  honeycombColumns,
  honeycombSize,
  isHoneycombCompact,
  selectedSystemName,
  selectedSystem,
  selectedItems,
  refreshOverview,
  handleSystemSelect,
  displayTarget,
  assetMatchLabel,
  formatDateTime,
  statusLabel,
  statusTextClass,
} = useHomeOverviewPage();
</script>

<style scoped>
.overview-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.overview-page {
  background: var(--oa-bg-panel);
}

.overview-panels {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 12px 0 0;
  background: var(--oa-bg-body);
}

.overview-panel__title {
  margin: 0;
  color: var(--oa-text-primary);
  font-size: var(--oa-font-page-title);
  font-weight: 600;
}

.overview-panel__body {
  padding: 16px;
  background: var(--oa-bg-panel);
}

.overview-panel__body--honeycomb {
  padding: 12px;
}

.system-empty {
  min-height: 280px;
  border-radius: 8px;
  border: 1px dashed var(--oa-border-color);
  background: var(--oa-bg-muted);
}

@media (max-width: 768px) {
  .overview-panels {
    padding: 8px 0 0;
  }

  .overview-panel__body {
    padding: 12px;
  }
}
</style>
