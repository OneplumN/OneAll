<template>
  <RepositoryPageShell
    :root-title="rootTitle"
    :section-title="sectionTitle"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <el-button
        class="toolbar-button"
        plain
        :disabled="!activeModel || !canManage"
        :loading="syncing"
        @click="handleSync"
      >
        同步资产
      </el-button>
    </template>

    <div class="asset-filters">
      <div class="filters-left">
        <el-button
          class="toolbar-button toolbar-button--primary"
          type="primary"
          plain
          :disabled="!activeModel || !canCreate"
          @click="openCreateDialog"
        >
          新增
        </el-button>
        <el-button
          class="toolbar-button"
          plain
          :disabled="!activeModel || !canCreate"
          @click="openImportDialog"
        >
          批量导入
        </el-button>
        <el-button
          class="toolbar-button"
          plain
          :disabled="!activeModel || !rows.length"
          @click="handleExportCsv"
        >
          导出 CSV
        </el-button>
      </div>
      <div class="filters-right">
        <el-input
          v-model="keyword"
          placeholder="支持按模型字段模糊搜索"
          clearable
          class="pill-input search-input search-input--compact"
          @keyup.enter="reloadAssets"
          @clear="handleKeywordClear"
        />
      </div>
    </div>

    <div class="asset-table">
      <div class="asset-table__card asset-table__card--x-scroll">
        <el-table
          v-loading="assetsLoading"
          :data="rows"
          class="oa-table"
          height="100%"
          stripe
        >
          <template #empty>
            <div class="table-empty">
              <p>暂无资产数据</p>
            </div>
          </template>

          <el-table-column
            v-for="col in modelFieldColumns"
            :key="col.key"
            :prop="col.key"
            :label="col.label"
            :min-width="col.minWidth"
            show-overflow-tooltip
          >
            <template #header>
              <span class="column-header">
                <span
                  v-if="col.isUnique"
                  class="unique-mark"
                >
                  *
                </span>
                {{ col.label }}
              </span>
            </template>
            <template #default="{ row }">
              <span>{{ row[col.key] ?? '-' }}</span>
            </template>
          </el-table-column>

          <el-table-column
            label="操作"
            width="180"
            fixed="right"
          >
            <template #default="{ row }">
              <el-space size="small">
                <el-button
                  class="oa-table-action oa-table-action--success"
                  text
                  size="small"
                  :disabled="!canManage"
                  @click.stop="handleEditClick"
                >
                  编辑
                </el-button>
                <el-button
                  class="oa-table-action oa-table-action--primary"
                  text
                  size="small"
                  @click.stop="openDetailDialog(row)"
                >
                  详情
                </el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <template #footer>
      <div class="oa-panel-footer">
        <div class="oa-panel-footer__left">
          <div class="oa-panel-stats">
            共 {{ total }} 条
          </div>
          <el-pagination
            class="asset-pagination__sizes"
            :total="total"
            :current-page="page"
            :page-size="pageSize"
            :page-sizes="pageSizeOptions"
            layout="sizes"
            background
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
        <div class="oa-panel-footer__right">
          <el-pagination
            class="asset-pagination__pager"
            :total="total"
            :current-page="page"
            :page-size="pageSize"
            layout="prev, pager, next"
            background
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </template>

    <AssetFormDialog
      v-model:visible="createDialogVisible"
      v-model:form="createForm"
      :title="createDialogTitle"
      :fields="formFields"
      :loading="createSubmitting"
      @close="resetCreateForm"
      @submit="handleCreateSubmit"
    />

    <AssetImportDialog
      v-model:visible="importDialogVisible"
      :columns="modelFieldColumns"
      :preview-rows="importPreviewRows"
      :errors="importErrors"
      :file-name="importFileName"
      :loading="importSubmitting"
      :disabled="!importPreviewRows.length || !canManage"
      accept=".csv,.txt"
      empty-label="选择 CSV 文件"
      @close="resetImportState"
      @download-template="downloadImportTemplate"
      @file-change="handleImportFileChange"
      @submit="handleImportSubmit"
    />

    <AssetRecordDetailDialog
      v-model:visible="detailDialogVisible"
      :record="detailRecord"
      :detail-row="detailRow"
      :columns="modelFieldColumns"
      :display-name="detailDisplayName"
      :format-sync-status="formatSyncStatus"
      :format-date="formatDate"
      :format-row-value="formatRowValue"
    />
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import AssetFormDialog from '@/features/assets/components/AssetFormDialog.vue';
import AssetImportDialog from '@/features/assets/components/AssetImportDialog.vue';
import AssetRecordDetailDialog from '@/features/assets/components/AssetRecordDetailDialog.vue';
import { useAssetModelCenterPage } from '@/features/assets/composables/useAssetModelCenterPage';

const {
  rootTitle,
  sectionTitle,
  canManage,
  canCreate,
  activeModel,
  syncing,
  assetsLoading,
  keyword,
  rows,
  modelFieldColumns,
  page,
  pageSize,
  total,
  pageSizeOptions,
  createDialogVisible,
  createForm,
  createSubmitting,
  createDialogTitle,
  formFields,
  importDialogVisible,
  importSubmitting,
  importPreviewRows,
  importErrors,
  importFileName,
  detailDialogVisible,
  detailRecord,
  detailRow,
  detailDisplayName,
  formatDate,
  formatRowValue,
  formatSyncStatus,
  handleSync,
  openCreateDialog,
  openImportDialog,
  handleExportCsv,
  reloadAssets,
  handlePageChange,
  handlePageSizeChange,
  handleKeywordClear,
  handleCreateSubmit,
  resetCreateForm,
  downloadImportTemplate,
  handleImportFileChange,
  handleImportSubmit,
  resetImportState,
  openDetailDialog,
  handleEditClick,
} = useAssetModelCenterPage();
</script>

<style scoped>
:deep(.page-panel__body) {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0;
}

:deep(.page-panel__footer) {
  border-top: none;
  background: var(--oa-bg-panel);
  padding: 0 16px 0px;
}

.asset-filters,
.asset-table {
  padding-left: 16px;
  padding-right: 16px;
  background: var(--oa-bg-panel);
}

.asset-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 16px;
  padding-bottom: 16px;
  margin: 0;
  border-bottom: 1px solid var(--oa-border-light);
}

.filters-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filters-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-left: auto;
}

.column-header {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.unique-mark {
  color: var(--oa-color-danger);
}

.asset-table {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
  padding-top: 0;
  padding-bottom: 12px;
}

.asset-table__card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: none;
  border-radius: 0;
  overflow: hidden;
}

.asset-table__card :deep(.el-table) {
  flex: 1;
  overflow-x: hidden;
}

.asset-table__card :deep(.el-table__header-wrapper) {
  overflow-x: hidden;
}

.asset-table__card :deep(.el-table__body-wrapper),
.asset-table__card :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

.asset-table__card--x-scroll :deep(.el-table__body-wrapper),
.asset-table__card--x-scroll :deep(.el-scrollbar__wrap) {
  overflow-x: auto;
}

.asset-table__card :deep(.el-table__inner-wrapper) {
  border-left: none !important;
  border-right: none !important;
}

.table-empty {
  padding: 2rem;
  text-align: center;
  color: var(--oa-text-secondary);
}

.asset-pagination__sizes,
.asset-pagination__pager {
  margin-top: 4px;
}

.asset-type-hint {
  font-size: var(--oa-font-meta);
  color: var(--oa-text-muted);
}

.asset-type-hint__label {
  margin-right: 4px;
}

.asset-type-hint__value {
  font-weight: 500;
  color: var(--oa-text-primary);
}

.asset-type-hint__unique {
  margin-left: 6px;
}

</style>
