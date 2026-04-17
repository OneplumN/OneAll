<template>
  <div class="alert-templates-view">
    <SettingsPageShell
      section-title="通知管理"
      breadcrumb="通知模板"
      body-padding="0"
      :panel-bordered="false"
    >
      <template #actions>
        <div class="settings-actions">
          <el-button
            class="toolbar-button"
            @click="goChannels"
          >
            通知渠道
          </el-button>
          <div
            class="refresh-card"
            @click="loadTemplates"
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

      <el-alert
        v-if="error"
        type="error"
        :closable="false"
        class="oa-inline-alert"
        show-icon
      >
        {{ error }}
      </el-alert>

      <div class="oa-list-page">
        <div class="page-toolbar page-toolbar--panel">
          <div class="page-toolbar__left">
            <el-button
              class="toolbar-button toolbar-button--primary"
              type="primary"
              @click="openTemplateDialog()"
            >
              新增模板
            </el-button>
          </div>
          <div class="page-toolbar__right">
            <el-select
              v-model="channelTypeFilter"
              class="pill-input narrow-select"
              placeholder="通道"
              clearable
            >
              <el-option
                v-for="option in channelTypeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-input
              v-model="keyword"
              placeholder="搜索模板名称"
              clearable
              class="search-input pill-input search-input--compact"
            />
          </div>
        </div>

        <div class="oa-table-panel">
          <div class="oa-table-panel__card">
            <el-table
              v-loading="loading"
              :data="pagedTemplates"
              class="oa-table"
              height="100%"
              stripe
              empty-text="暂无模板"
            >
              <el-table-column
                prop="name"
                label="模板名称"
                min-width="240"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <div class="template-name">
                    <strong class="oa-table-title">{{ row.name }}</strong>
                    <el-tag
                      v-if="row.is_default"
                      size="small"
                      type="success"
                      effect="plain"
                    >
                      默认
                    </el-tag>
                  </div>
                  <p class="oa-table-meta">
                    {{ row.description || '—' }}
                  </p>
                </template>
              </el-table-column>
              <el-table-column
                prop="channel_type"
                label="通道"
                width="180"
              >
                <template #default="{ row }">
                  {{ channelTypeMap[row.channel_type] || row.channel_type }}
                </template>
              </el-table-column>
              <el-table-column
                prop="updated_at"
                label="更新时间"
                width="200"
              >
                <template #default="{ row }">
                  {{ formatDate(row.updated_at) }}
                </template>
              </el-table-column>
              <el-table-column
                label="操作"
                width="260"
                fixed="right"
              >
                <template #default="{ row }">
                  <div class="row-actions">
                    <el-button
                      text
                      size="small"
                      class="oa-table-action oa-table-action--success"
                      @click="openTemplateDialog(row)"
                    >
                      编辑
                    </el-button>
                    <el-button
                      text
                      size="small"
                      class="oa-table-action oa-table-action--primary"
                      :disabled="row.is_default"
                      @click="setTemplateDefault(row)"
                    >
                      设为默认
                    </el-button>
                    <el-button
                      text
                      size="small"
                      class="oa-table-action oa-table-action--danger"
                      @click="handleTemplateDelete(row)"
                    >
                      删除
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <div class="oa-panel-footer">
          <div class="oa-panel-footer__left">
            <div class="oa-panel-stats">
              共 {{ filteredTemplates.length }} 条
            </div>
            <el-pagination
              :total="filteredTemplates.length"
              :current-page="currentPage"
              :page-size="pageSize"
              :page-sizes="pageSizeOptions"
              layout="sizes"
              background
              class="repository-pagination__sizes"
              :disabled="loading"
              @size-change="handlePageSizeChange"
              @current-change="handlePageChange"
            />
          </div>
          <div class="oa-panel-footer__right">
            <el-pagination
              class="repository-pagination__pager"
              :total="filteredTemplates.length"
              :current-page="currentPage"
              :page-size="pageSize"
              layout="prev, pager, next"
              background
              :disabled="loading"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </div>
    </SettingsPageShell>

    <AlertTemplateEditorDialog
      v-model:visible="templateDialog.visible"
      v-model:form="templateDialog.form"
      :title="templateDialog.record ? '编辑模板' : '新增模板'"
      :loading="templateDialog.loading"
      :variables="templateDialog.variables"
      :channel-type-options="channelTypeOptions"
      @submit="submitTemplate"
    />
  </div>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue';
import AlertTemplateEditorDialog from '@/features/settings/components/AlertTemplateEditorDialog.vue';
import SettingsPageShell from '@/features/settings/components/SettingsPageShell.vue';
import { useAlertTemplatesPage } from '@/features/settings/composables/useAlertTemplatesPage';

const {
  channelTypeOptions,
  channelTypeMap,
  loading,
  error,
  keyword,
  channelTypeFilter,
  pageSizeOptions,
  currentPage,
  pageSize,
  templateDialog,
  filteredTemplates,
  pagedTemplates,
  loadTemplates,
  handlePageSizeChange,
  handlePageChange,
  formatDate,
  openTemplateDialog,
  submitTemplate,
  handleTemplateDelete,
  setTemplateDefault,
  goChannels,
} = useAlertTemplatesPage();
</script>

<style scoped>
.alert-templates-view {
  height: 100%;
  min-height: 0;
}

.settings-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.row-actions {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
}

.row-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

</style>
