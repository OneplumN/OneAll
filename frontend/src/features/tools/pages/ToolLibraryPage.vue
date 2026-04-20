<template>
  <RepositoryPageShell
    root-title="运维工具"
    :section-title="t('tools.libraryTitle')"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <div class="tool-library__actions">
        <div
          class="refresh-card"
          @click="loadTools"
        >
          <el-icon
            class="refresh-icon"
            :class="{ spinning: loading.table }"
          >
            <Refresh />
          </el-icon>
          <span>{{ t('common.refresh') }}</span>
        </div>
      </div>
    </template>

    <div class="oa-list-page">
      <div class="page-toolbar page-toolbar--panel">
        <div class="page-toolbar__left">
          <el-button
            class="toolbar-button toolbar-button--primary"
            type="primary"
            :disabled="!canCreate"
            @click="openCreateDialog"
          >
            {{ t('tools.createTool') }}
          </el-button>
        </div>
        <div class="page-toolbar__right tool-library__filters">
          <el-select
            v-model="filters.category"
            placeholder="全部类别"
            clearable
            class="pill-input narrow-select"
          >
            <el-option
              label="全部类别"
              value=""
            />
            <el-option
              v-for="category in categoryOptions"
              :key="category"
              :label="category"
              :value="category"
            />
          </el-select>

          <el-select
            v-model="filters.tag"
            placeholder="筛选标签"
            clearable
            filterable
            class="pill-input tool-library__tag-filter"
          >
            <el-option
              v-for="tag in tagOptions"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>

          <el-input
            v-model="filters.keyword"
            placeholder="搜索名称或描述"
            clearable
            class="search-input pill-input search-input--compact"
            @clear="loadTools"
            @keyup.enter="loadTools"
          >
            <template #suffix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <div class="oa-table-panel">
        <div class="oa-table-panel__card tool-library__table-card">
          <el-table
            v-loading="loading.table"
            :data="filteredTools"
            class="oa-table"
            stripe
            height="100%"
          >
            <el-table-column type="expand">
              <template #default="{ row }">
                <div class="tool-description">
                  <p class="tool-description__title">
                    描述
                  </p>
                  <p>{{ row.description || '暂无描述' }}</p>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              prop="name"
              label="名称"
              min-width="200"
            >
              <template #default="{ row }">
                <div class="tool-name">
                  <strong>{{ row.name }}</strong>
                  <span class="oa-table-meta">版本：{{ row.connector_version || '未标记' }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              prop="category"
              label="类别"
              width="140"
            />
            <el-table-column
              prop="tags"
              label="标签"
              min-width="220"
            >
              <template #default="{ row }">
                <el-space>
                  <el-tag
                    v-for="tag in row.tags"
                    :key="tag"
                    round
                    size="small"
                  >
                    {{ tag }}
                  </el-tag>
                </el-space>
              </template>
            </el-table-column>
            <el-table-column
              label="最近更新"
              width="180"
            >
              <template #default="{ row }">
                {{ formatTime(row.updated_at) }}
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="160"
              fixed="right"
            >
              <template #default="{ row }">
                <el-button
                  type="primary"
                  link
                  class="oa-table-action oa-table-action--success"
                  :disabled="!canExecute"
                  @click="handleExecute(row)"
                >
                  {{ t('tools.execute') }}
                </el-button>
                <el-button
                  type="info"
                  link
                  class="oa-table-action oa-table-action--primary"
                  @click="openDetails(row)"
                >
                  {{ t('tools.viewDetails') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="createDialogVisible"
      :title="t('tools.dialogTitle')"
      width="520px"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        label-position="top"
        :rules="createRules"
      >
        <el-form-item
          label="名称"
          prop="name"
        >
          <el-input
            v-model="createForm.name"
            placeholder="工具名称"
          />
        </el-form-item>
        <el-form-item
          label="类别"
          prop="category"
        >
          <el-input
            v-model="createForm.category"
            placeholder="所属类别，例如 脚本 / 数据采集"
          />
        </el-form-item>
        <el-form-item
          label="标签"
          prop="tags"
        >
          <el-select
            v-model="createForm.tags"
            multiple
            allow-create
            filterable
            placeholder="添加标签"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="说明工具用途、注意事项等"
          />
        </el-form-item>
        <el-form-item label="关联脚本 ID">
          <el-input
            v-model="createForm.script_id"
            placeholder="可选：关联脚本仓库 ID"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">
          {{ t('common.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="loading.creating"
          @click="submitCreate"
        >
          {{ t('common.save') }}
        </el-button>
      </template>
    </el-dialog>

    <el-drawer
      v-model="detailsDrawerVisible"
      :title="selectedTool?.name"
      size="40%"
    >
      <div
        v-if="selectedTool"
        class="drawer-section"
      >
        <p class="oa-table-meta">
          类别：{{ selectedTool.category }}
        </p>
        <p class="oa-table-meta">
          版本：{{ selectedTool.connector_version || '未标记' }}
        </p>
        <p class="oa-table-meta">
          标签：
          <el-tag
            v-for="tag in selectedTool.tags"
            :key="tag"
            round
            size="small"
          >
            {{ tag }}
          </el-tag>
        </p>
        <p>{{ selectedTool.description || '暂无描述' }}</p>
      </div>
      <el-divider />
      <div class="drawer-section">
        <h4>执行记录</h4>
        <el-empty description="后端暂未接入执行历史" />
      </div>
    </el-drawer>

    <el-drawer
      v-model="executionDrawerVisible"
      :title="`执行结果 - ${executingTool?.name || ''}`"
      size="40%"
    >
      <el-skeleton
        v-if="loading.executing"
        :rows="5"
        animated
      />
      <div
        v-else-if="executionResult"
        class="drawer-section"
      >
        <p class="oa-table-meta">
          运行 ID：{{ executionResult.run_id }}
        </p>
        <p class="oa-table-meta">
          状态：{{ executionResult.status }}
        </p>
        <p class="oa-table-meta">
          开始时间：{{ formatTime(executionResult.started_at) }}
        </p>
        <p class="oa-table-meta">
          结束时间：{{ formatTime(executionResult.finished_at) }}
        </p>
        <el-input
          v-if="executionResult.output"
          v-model="executionResult.output"
          type="textarea"
          :rows="8"
          readonly
        />
        <el-empty
          v-else
          description="执行成功，但未返回输出"
        />
      </div>
      <el-empty
        v-else
        description="尚未触发执行"
      />
    </el-drawer>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { Refresh, Search } from '@element-plus/icons-vue';

import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import { useToolLibraryPage } from '@/features/tools/composables/useToolLibraryPage';

const {
  canCreate,
  canExecute,
  canManage,
  categoryOptions,
  createDialogVisible,
  createForm,
  createFormRef,
  createRules,
  detailsDrawerVisible,
  executingTool,
  executionDrawerVisible,
  executionResult,
  filteredTools,
  filters,
  formatTime,
  handleExecute,
  loadTools,
  loading,
  openCreateDialog,
  openDetails,
  selectedTool,
  submitCreate,
  t,
  tagOptions,
} = useToolLibraryPage();
</script>

<style scoped>
.tool-library__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tool-library__filters {
  flex-wrap: wrap;
}

.tool-library__tag-filter {
  width: 200px;
}

.tool-library__table-card {
  flex: 1;
  min-height: 0;
}

.tool-name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-description {
  padding: 1rem 2rem 1rem 3rem;
  line-height: 1.6;
}

.tool-description__title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>
