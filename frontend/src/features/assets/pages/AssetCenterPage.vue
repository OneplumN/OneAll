<template>
  <RepositoryPageShell
    :root-title="rootTitle"
    :section-title="viewConfig.title"
    :breadcrumb="breadcrumbTitle"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <el-button
        v-if="showSyncButton"
        class="toolbar-button"
        type="primary"
        :loading="syncing"
        :disabled="!canManage"
        @click="handleSync"
      >
        同步资产
      </el-button>
      <el-button
        v-if="showSyncButton"
        class="toolbar-button"
        plain
        :disabled="!canManage"
        @click="openSyncHistory"
      >
        同步历史
      </el-button>
    </template>

    <AssetCenterToolbar
      v-model:keyword="keyword"
      v-model:network-filter="networkFilter"
      v-model:online-status-filter="onlineStatusFilter"
      v-model:proxy-filter="proxyFilter"
      v-model:interface-available-filter="interfaceAvailableFilter"
      v-model:app-status-filter="appStatusFilter"
      :can-create="canCreate"
      :can-import="canImport"
      :can-manage="canManage"
      :view-key="viewKey"
      :selected-row-count="selectedRowIds.length"
      :show-network-type-filter="Boolean(viewConfig.filters?.networkType)"
      :show-online-status-filter="showOnlineStatusFilter"
      :show-proxy-filter="showProxyFilter"
      :show-interface-available-filter="showInterfaceAvailableFilter"
      :show-app-status-filter="showAppStatusFilter"
      :keyword-placeholder="keywordPlaceholder"
      :proxy-options="proxyOptions"
      :interface-available-options="interfaceAvailableOptions"
      :app-status-options="appStatusOptions"
      @open-create="openCreateDialog"
      @open-import="openImportDialog"
      @export="handleExport"
      @batch-status-command="handleBatchStatusCommand"
    />

    <AssetCenterTable
      :view-key="viewKey"
      :can-manage="canManage"
      :show-edit-column="showEditColumn"
      :allow-horizontal-scroll="allowHorizontalScroll"
      :loading="tableLoading"
      :rows="pagedRows"
      :columns="effectiveColumns"
      :status-toggling="statusToggling"
      :total="totalCount"
      :page="page"
      :page-size="pageSize"
      :page-size-options="pageSizeOptions"
      :status-tag-type="statusTagType"
      @selection-change="handleSelectionChange"
      @row-status-command="handleRowStatusCommand"
      @edit="openEditDialog"
      @conflict="openConflictDialog"
      @detail="openDetailDialog"
      @page-change="handlePageChange"
      @page-size-change="handlePageSizeChange"
    />

    <AssetFormDialog
      v-model:visible="createDialogVisible"
      v-model:form="createForm"
      :title="createDialogTitle"
      :fields="currentFormFields"
      :loading="createSubmitting"
      @close="resetCreateForm"
      @submit="handleCreateSubmit"
    />

    <AssetFormDialog
      v-model:visible="editDialogVisible"
      v-model:form="editForm"
      :title="editDialogTitle"
      :fields="currentFormFields"
      :loading="editSubmitting"
      :disabled="!canManage"
      @close="resetEditForm"
      @submit="handleEditSubmit"
    />

    <AssetConflictDialog
      v-model:visible="conflictDialogVisible"
      :record="conflictRecord"
      :format-sync-status="formatSyncStatus"
    />

    <AssetSyncHistoryDialog
      v-model:visible="syncHistoryDialogVisible"
      :loading="syncHistoryLoading"
      :runs="syncHistoryRuns"
      :format-date="formatDate"
      :format-scope="formatSyncRunScope"
      :format-summary="formatSyncRunSummary"
      :status-tag-type="statusTagType"
    />

    <AssetRecordDetailDialog
      v-model:visible="detailDialogVisible"
      :record="detailRecord"
      :detail-row="detailRow"
      :columns="effectiveColumns"
      :display-name="detailDisplayName"
      :format-sync-status="formatSyncStatus"
      :format-date="formatDate"
      :format-row-value="formatRowValue"
    />

    <AssetImportDialog
      v-model:visible="importDialogVisible"
      :columns="currentImportTemplate?.columns || []"
      :preview-rows="importPreviewRows"
      :errors="importErrors"
      :file-name="importFileName"
      :loading="importSubmitting"
      :disabled="!canCreate || !importPreviewRows.length"
      accept=".csv,.txt"
      empty-label="选择 CSV 文件"
      @close="resetImportState"
      @download-template="downloadImportTemplate"
      @file-change="handleImportFileChange"
      @submit="handleImportSubmit"
    />
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import { INTEGRATION_PLUGIN_MAP } from '@/data/integrationPlugins';
import { useSessionStore } from '@/app/stores/session';
import AssetCenterTable from '@/features/assets/components/AssetCenterTable.vue';
import AssetCenterToolbar from '@/features/assets/components/AssetCenterToolbar.vue';
import AssetConflictDialog from '@/features/assets/components/AssetConflictDialog.vue';
import AssetFormDialog from '@/features/assets/components/AssetFormDialog.vue';
import AssetImportDialog from '@/features/assets/components/AssetImportDialog.vue';
import AssetRecordDetailDialog from '@/features/assets/components/AssetRecordDetailDialog.vue';
import AssetSyncHistoryDialog from '@/features/assets/components/AssetSyncHistoryDialog.vue';
import { useAssetDataFlow } from '@/features/assets/composables/useAssetDataFlow';
import { useAssetImport } from '@/features/assets/composables/useAssetImport';
import { useAssetPageControls } from '@/features/assets/composables/useAssetPageControls';
import { useAssetRecordMutations } from '@/features/assets/composables/useAssetRecordMutations';
import { useAssetViewPresentation } from '@/features/assets/composables/useAssetViewPresentation';
import {
  ASSET_VIEW_DEFINITIONS,
  ROUTE_VIEW_KEY,
} from '@/features/assets/mappers/assetViewDefinitions';
import {
  formatDate,
  formatRowValue,
  formatSyncRunScope,
  formatSyncRunSummary,
  formatSyncStatus,
  statusTagType,
} from '@/features/assets/utils/assetHelpers';
import { matchesAssetViewDefinition } from '@/features/assets/utils/assetViewEnhancement';
import type {
  AssetViewKey,
} from '@/features/assets/types/assetCenter';

const sessionStore = useSessionStore();
const canCreate = computed(() => sessionStore.hasPermission('assets.records.create'));
const canManage = computed(() => sessionStore.hasPermission('assets.records.manage'));

const route = useRoute();
const viewKey = computed<AssetViewKey>(() => ROUTE_VIEW_KEY[String(route.name)] || 'cmdb-domain');
const viewConfig = computed(() => ASSET_VIEW_DEFINITIONS[viewKey.value]);
const {
  appStatusFilter,
  bindLifecycle,
  handlePageChange,
  handlePageSizeChange,
  interfaceAvailableFilter,
  keyword,
  keywordDebounced,
  networkFilter,
  onlineStatusFilter,
  page,
  pageSize,
  pageSizeOptions,
  proxyFilter,
} = useAssetPageControls({ viewKey });
const rootTitle = '资产信息';
const breadcrumbTitle = '';
const showEditColumn = computed(() => viewKey.value === 'workorder-host');
const allowHorizontalScroll = true;
const showSyncButton = computed(() => viewKey.value !== 'workorder-host');
const editDialogTitle = computed(() =>
  viewKey.value === 'workorder-host' ? '编辑工单纳管主机' : '编辑资产'
);
const keywordPlaceholder = computed(() => {
  if (viewKey.value === 'cmdb-domain') return '搜索域名 / 系统 / 负责人';
  if (viewKey.value === 'zabbix-host') return '搜索 IP / 主机名 / 群组';
  if (viewKey.value === 'ipmp-project') return '搜索应用编号 / 名称 / 负责人';
  return '搜索 IP / Hostname / 系统';
});

const showOnlineStatusFilter = computed(() => viewKey.value === 'workorder-host');
const showProxyFilter = computed(() => viewKey.value === 'zabbix-host' || viewKey.value === 'workorder-host');
const showInterfaceAvailableFilter = computed(() => viewKey.value === 'zabbix-host');
const showAppStatusFilter = computed(() => viewKey.value === 'ipmp-project');
const pluginDefinition = computed(() => {
  const type = viewConfig.value.pluginType;
  if (!type) return undefined;
  return INTEGRATION_PLUGIN_MAP[type];
});
const shouldLoadPluginConfig = computed(
  () => pluginDefinition.value?.runtime.mode === 'script' && Boolean(viewConfig.value.pluginType)
);
const currentImportTemplate = computed(() => viewConfig.value.importTemplate);
const {
  assets,
  facets,
  facetsByView,
  handleExport,
  handleSync,
  loadAssets,
  loadPluginConfig,
  openSyncHistory,
  pluginConfig,
  syncHistoryDialogVisible,
  syncHistoryLoading,
  syncHistoryRuns,
  syncing,
  tableLoading,
  totalCount,
} = useAssetDataFlow({
  canManage,
  viewKey,
  viewConfig,
  pluginDefinition,
  keywordDebounced,
  networkFilter,
  onlineStatusFilter,
  proxyFilter,
  interfaceAvailableFilter,
  appStatusFilter,
  showProxyFilter,
  showInterfaceAvailableFilter,
  showAppStatusFilter,
  showOnlineStatusFilter,
  page,
  pageSize,
  matchesDefinition: matchesAssetViewDefinition,
});
const {
  importDialogVisible,
  importSubmitting,
  importPreviewRows,
  importErrors,
  importFileName,
  resetImportState,
  openImportDialog,
  downloadImportTemplate,
  handleImportFileChange,
  handleImportSubmit,
} = useAssetImport({
  canCreate,
  currentImportTemplate,
  viewConfig,
  loadAssets,
});
const {
  appStatusOptions,
  backendAssetType,
  canImport,
  createDialogTitle,
  currentFormFields,
  effectiveColumns,
  interfaceAvailableOptions,
  matchingRecords,
  pagedRows,
  proxyOptions,
} = useAssetViewPresentation({
  assets,
  facets,
  viewKey,
  viewConfig,
});
const {
  conflictDialogVisible,
  conflictRecord,
  createDialogVisible,
  createForm,
  createSubmitting,
  detailDialogVisible,
  detailRecord,
  detailRow,
  editDialogVisible,
  editForm,
  editSubmitting,
  editingRecordId,
  handleBatchStatusCommand,
  handleCreateSubmit,
  handleEditSubmit,
  handleRowStatusCommand,
  handleSelectionChange,
  openConflictDialog,
  openCreateDialog,
  openDetailDialog,
  openEditDialog,
  resetCreateForm,
  resetEditForm,
  selectedRowIds,
  statusToggling,
} = useAssetRecordMutations({
  assets,
  canCreate,
  canManage,
  viewKey,
  viewConfig,
  currentFormFields,
  backendAssetType,
  matchingRecords,
  showEditColumn,
  loadAssets,
});
const detailDisplayName = computed(() =>
  detailRow.value?.domain ||
  detailRow.value?.app_name_cn ||
  detailRow.value?.hostname ||
  detailRecord.value?.name ||
  '-'
);
bindLifecycle({
  shouldLoadPluginConfig,
  loadPluginConfig,
  clearPluginConfig: () => {
    pluginConfig.value = null;
  },
  loadAssets,
  facets,
  facetsByView,
  resetCreateForm,
  resetEditForm,
  resetImportState,
  createDialogVisible,
  editDialogVisible,
  editingRecordId,
  importDialogVisible,
  selectedRowIds,
});
</script>

<style scoped>
:deep(.page-panel__body) {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0;
}

@media (max-width: 1440px) {
  :deep(.asset-filters) {
    flex-wrap: wrap;
  }
}
</style>
