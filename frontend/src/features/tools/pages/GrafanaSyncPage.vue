<template>
  <RepositoryPageShell
    root-title="运维工具"
    section-title="Grafana 同步"
    scroll-mode="page"
  >
    <template #actions>
      <div
        class="refresh-card"
        @click="fetchPlugin"
      >
        <el-icon
          class="refresh-icon"
          :class="{ spinning: loading }"
        >
          <Refresh />
        </el-icon>
        <span>刷新</span>
      </div>
      <el-button
        class="toolbar-button toolbar-button--primary"
        type="primary"
        :loading="saving"
        :disabled="!canSave"
        @click="handleSave"
      >
        保存配置
      </el-button>
      <el-button
        class="toolbar-button"
        type="success"
        :loading="running"
        :disabled="!canRun"
        @click="handleRun"
      >
        立即同步
      </el-button>
    </template>

    <div class="layout-grid">
      <GrafanaSyncConfigCard
        v-model:panels="activePanels"
        v-model:form-values="formValues"
        :expanded="configExpanded"
        :is-zabbix-ready="isZabbixReady"
        :is-grafana-ready="isGrafanaReady"
        :zabbix-token-placeholder="zabbixTokenPlaceholder"
        :grafana-token-placeholder="grafanaTokenPlaceholder"
        @toggle-expand="configExpanded = !configExpanded"
      />

      <ToolExecutionPanel
        v-model:scrollbar-ref="logScrollbarRef"
        :current-execution="currentExecution"
        :current-run-id="currentRunId"
        :executions-loading="executionsLoading"
        :status-tag-type="statusTagType"
        :status-text="statusText"
        :format-time="formatTime"
        :is-running-status="isRunningStatus"
        :log-auto-follow="logAutoFollow"
        :log-wrap="logWrap"
        :visible-log-output="visibleLogOutput"
        @refresh="fetchExecutions"
        @copy-run-id="copyText"
        @toggle-follow="toggleFollow"
        @toggle-wrap="toggleWrap"
        @copy-log="copyText"
        @download-log="downloadLog"
        @clear-log="clearLogView"
        @scroll="handleLogScroll"
      />
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue';
import GrafanaSyncConfigCard from '@/features/tools/components/GrafanaSyncConfigCard.vue';
import ToolExecutionPanel from '@/features/tools/components/ToolExecutionPanel.vue';
import { useGrafanaSyncPage } from '@/features/tools/composables/useGrafanaSyncPage';
import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';

const {
  activePanels,
  canRun,
  canSave,
  clearLogView,
  configExpanded,
  copyText,
  currentExecution,
  currentRunId,
  downloadLog,
  executionsLoading,
  fetchExecutions,
  fetchPlugin,
  formValues,
  formatTime,
  grafanaTokenPlaceholder,
  handleLogScroll,
  handleRun,
  handleSave,
  isGrafanaReady,
  isRunningStatus,
  isZabbixReady,
  loading,
  logAutoFollow,
  logScrollbarRef,
  logWrap,
  running,
  saving,
  statusTagType,
  statusText,
  toggleFollow,
  toggleWrap,
  visibleLogOutput,
  zabbixTokenPlaceholder,
} = useGrafanaSyncPage();
</script>

<style scoped>
.layout-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

@media (max-width: 1024px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }
}
</style>
