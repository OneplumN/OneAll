<template>
  <div class="repository-main">
    <div class="repository-header">
      <div class="repository-header__info">
        <span class="header__title">{{ primaryNavTitle }}</span>
        <span class="header__separator">/</span>
        <span class="header__subtitle">{{ currentDirectoryName }}</span>
      </div>
      <div class="repository-header__actions">
        <el-dropdown
          trigger="click"
          class="directory-actions"
          @command="handleCommand"
        >
          <span class="dropdown-trigger">
            <el-icon><Setting /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="manageDirectories">
                管理目录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <div
          class="refresh-card"
          @click="emit('refresh')"
        >
          <el-icon
            class="refresh-icon"
            :class="{ spinning: loadingRepositories }"
          >
            <Refresh />
          </el-icon>
          <span>刷新</span>
        </div>
      </div>
    </div>

    <div class="page-toolbar page-toolbar--panel repository-filters">
      <div class="page-toolbar__left">
        <el-button
          class="toolbar-button toolbar-button--primary"
          type="primary"
          :disabled="!canCreate || !directoryOptions.length"
          @click="emit('openCreate')"
        >
          新建脚本
        </el-button>
      </div>
      <div class="page-toolbar__right">
        <el-select
          v-model="languageFilter"
          class="pill-input narrow-select"
        >
          <el-option
            label="全部语言"
            value="all"
          />
          <el-option
            v-for="option in languageOptions"
            :key="option"
            :label="option"
            :value="option.toLowerCase()"
          />
        </el-select>
        <el-input
          v-model="keyword"
          placeholder="搜索脚本名称 / 标签"
          clearable
          class="search-input pill-input search-input--compact"
        >
          <template #prefix>
            <i class="el-icon-search" />
          </template>
        </el-input>
      </div>
    </div>

    <div class="oa-table-panel repository-table">
      <div class="oa-table-panel__card repository-table__card">
        <el-table
          v-loading="loadingRepositories"
          class="oa-table"
          height="100%"
          :data="paginatedRepos"
          stripe
          :row-class-name="rowClassName"
          @sort-change="emit('sortChange', $event)"
        >
          <template #empty>
            <div class="table-empty">
              <p>该目录暂无脚本</p>
            </div>
          </template>
          <el-table-column
            prop="name"
            label="脚本名称"
            min-width="160"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span
                class="repository-name"
                @click.stop="emit('view', row)"
              >{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="language"
            label="语言"
            width="90"
          />
          <el-table-column
            label="标签"
            min-width="140"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <el-space>
                <el-tag
                  v-for="tag in row.tags"
                  :key="tag"
                  size="small"
                  round
                >
                  {{ tag }}
                </el-tag>
              </el-space>
            </template>
          </el-table-column>
          <el-table-column
            label="最新版本"
            width="110"
            min-width="110"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              {{ row.latest_version || '未发布' }}
            </template>
          </el-table-column>
          <el-table-column
            prop="updated_at"
            label="更新时间"
            width="160"
            show-overflow-tooltip
            sortable="custom"
          >
            <template #default="{ row }">
              {{ formatTime(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="160"
          >
            <template #default="{ row }">
              <el-space size="small">
                <el-button
                  text
                  size="small"
                  class="oa-table-action oa-table-action--success"
                  :disabled="!canManage"
                  @click.stop="emit('edit', row)"
                >
                  编辑
                </el-button>
                <el-button
                  text
                  type="danger"
                  size="small"
                  class="oa-table-action oa-table-action--danger"
                  :disabled="!canManage"
                  @click.stop="emit('delete', row)"
                >
                  删除
                </el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div class="oa-panel-footer repository-table__footer">
      <div class="oa-panel-footer__left">
        <div class="oa-panel-stats">
          共 {{ filteredTotal }} 条
        </div>
        <el-pagination
          class="repository-pagination__sizes"
          :total="filteredTotal"
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="pageSizeOptions"
          layout="sizes"
          background
          @size-change="emit('pageSizeChange', $event)"
          @current-change="emit('pageChange', $event)"
        />
      </div>
      <div class="oa-panel-footer__right">
        <el-pagination
          class="repository-pagination__pager"
          :total="filteredTotal"
          :current-page="currentPage"
          :page-size="pageSize"
          layout="prev, pager, next"
          background
          @current-change="emit('pageChange', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Refresh, Setting } from '@element-plus/icons-vue';

import type { ScriptRepository } from '@/features/tools/api/codeRepositoryApi';

type DirectoryOption = {
  key: string;
  title: string;
};

type SortChangePayload = {
  prop: string;
  order: 'ascending' | 'descending' | null;
};

defineProps<{
  primaryNavTitle: string;
  currentDirectoryName: string;
  canCreate: boolean;
  canManage: boolean;
  directoryOptions: DirectoryOption[];
  languageOptions: string[];
  loadingRepositories: boolean;
  paginatedRepos: ScriptRepository[];
  filteredTotal: number;
  currentPage: number;
  pageSize: number;
  pageSizeOptions: number[];
  formatTime: (value?: string) => string;
  rowClassName: (payload: { row: ScriptRepository }) => string;
}>();

const emit = defineEmits<{
  (event: 'manageDirectories'): void;
  (event: 'refresh'): void;
  (event: 'openCreate'): void;
  (event: 'view', repository: ScriptRepository): void;
  (event: 'edit', repository: ScriptRepository): void;
  (event: 'delete', repository: ScriptRepository): void;
  (event: 'pageChange', page: number): void;
  (event: 'pageSizeChange', size: number): void;
  (event: 'sortChange', payload: SortChangePayload): void;
}>();

const languageFilter = defineModel<string>('languageFilter', { required: true });
const keyword = defineModel<string>('keyword', { required: true });

const handleCommand = (command: string) => {
  if (command === 'manageDirectories') {
    emit('manageDirectories');
  }
};
</script>

<style scoped>
.repository-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--oa-bg-panel);
  padding: 0 16px 0;
  overflow: hidden;
}

.repository-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.repository-header__info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: var(--oa-text-secondary);
}

.header__title {
  font-weight: 600;
  color: var(--oa-text-primary);
}

.header__separator {
  color: var(--oa-text-muted);
  font-size: 13px;
}

.header__subtitle {
  color: var(--oa-text-secondary);
}

.repository-header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--oa-border-light);
  border-radius: 8px;
  background: var(--oa-bg-panel);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
  box-shadow: var(--oa-shadow-sm);
}

.refresh-card:hover {
  border-color: var(--oa-color-primary-light);
  box-shadow: 0 10px 18px rgba(64, 158, 255, 0.08);
  transform: translateY(-1px);
}

.refresh-icon.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.toolbar-button {
  border-radius: 6px;
  padding: 0 16px;
  height: 32px;
  font-weight: 500;
}

.toolbar-button--primary {
  box-shadow: none;
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

.search-input {
  flex: 1;
  min-width: 220px;
}

.search-input--compact {
  max-width: 320px;
}

.narrow-select {
  width: 180px;
}

.pill-input :deep(.el-input__wrapper),
.pill-input :deep(.el-select__wrapper) {
  border-radius: 999px;
  padding-left: 0.85rem;
  background: var(--oa-filter-control-bg);
  box-shadow: inset 0 0 0 1px var(--oa-border-color);
}

.repository-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--oa-bg-panel);
  overflow: hidden;
  padding: 0 16px 12px;
}

.repository-table__card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: none;
  min-height: 0;
}

.repository-table__card :deep(.el-table) {
  flex: 1;
  overflow-x: hidden;
}

.repository-table__card :deep(.el-table__inner-wrapper) {
  border-left: none !important;
  border-right: none !important;
}

.repository-name {
  color: var(--oa-color-primary);
  cursor: pointer;
}

.repository-name:hover {
  text-decoration: underline;
}

.repository-table__footer {
  padding: 0 16px 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  color: var(--oa-text-secondary);
  border-top: none;
}

.repository-pagination__sizes :deep(.el-input__wrapper) {
  padding: 0 10px;
}

.table-empty {
  padding: 2rem;
  color: var(--oa-text-muted);
  font-size: var(--oa-font-base);
}

@media (max-width: 1200px) {
  .repository-filters {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
  }

  .search-input,
  .narrow-select {
    width: 100%;
  }
}
</style>
