<template>
  <div :class="['code-repository', { 'code-repository--detail': detailMode || createMode }]">
    <section class="repository-panel">
      <div class="repository-body">
        <RepositoryDirectorySidebar
          v-model:collapsed="sidebarCollapsed"
          :directory-groups="directoryGroups"
          :selected-directory-key="selectedDirectoryKey"
          :resolve-directory-icon="resolveDirectoryIcon"
          @select="handleDirectorySelect"
        />

        <RepositoryListPanel
          v-if="!detailMode && !createMode"
          v-model:language-filter="languageFilter"
          v-model:keyword="repoKeyword"
          :primary-nav-title="primaryNavTitle"
          :current-directory-name="currentDirectoryName"
          :can-create="canCreate"
          :can-manage="canManage"
          :directory-options="directoryOptions"
          :language-options="LANGUAGE_OPTIONS"
          :loading-repositories="loading.repositories"
          :paginated-repos="paginatedRepos"
          :filtered-total="filteredCurrentRepos.length"
          :current-page="currentPage"
          :page-size="pageSize"
          :page-size-options="pageSizeOptions"
          :format-time="formatTime"
          :row-class-name="rowClassName"
          @manage-directories="handleDirectoryCommand('manageDirectories')"
          @refresh="loadRepositories"
          @open-create="openCreateDialog"
          @view="handleView"
          @edit="handleEdit"
          @delete="handleDelete"
          @page-change="handlePageChange"
          @page-size-change="handlePageSizeChange"
          @sort-change="handleSortChange"
        />

        <div
          v-else-if="createMode"
          class="repository-main"
        >
          <div class="repository-header">
            <div class="repository-header__info">
              <span class="header__title">{{ primaryNavTitle }}</span>
              <span class="header__separator">/</span>
              <span class="header__subtitle">{{ currentDirectoryName }}</span>
              <span class="header__separator">/</span>
              <span class="header__subtitle">新建脚本</span>
            </div>
            <div class="repository-header__actions">
              <el-button
                class="toolbar-button"
                @click="exitCreateMode"
              >
                返回列表
              </el-button>
              <el-button
                class="toolbar-button toolbar-button--primary"
                type="primary"
                :disabled="!canCreate"
                :loading="loading.creating"
                @click="handleCreateInline"
              >
                保存
              </el-button>
            </div>
          </div>
          <RepositoryEditorLayout
            :model-value="createForm.content"
            :language="createForm.language"
            :placeholder="codePlaceholder(createForm.language)"
            @update:model-value="createForm.content = $event"
          >
            <RepositoryCreateFormCard
              ref="createFormCardRef"
              v-model="createForm"
              :rules="createRules"
              :directory-options="directoryOptions"
              :language-options="LANGUAGE_OPTIONS"
            />
          </RepositoryEditorLayout>
        </div>

        <div
          v-else
          class="repository-main"
        >
          <div class="repository-header">
            <div class="repository-header__info">
              <span class="header__title">{{ primaryNavTitle }}</span>
              <span class="header__separator">/</span>
              <span
                class="header__subtitle clickable"
                @click="navigateToDirectory(selectedDirectoryKey || '')"
              >
                {{ currentDirectoryName }}
              </span>
              <span class="header__separator">/</span>
              <span class="header__subtitle">{{ detailRepository?.name || '脚本详情' }}</span>
            </div>
            <div class="repository-header__actions">
              <el-button
                class="toolbar-button"
                @click="exitDetailMode"
              >
                返回列表
              </el-button>
              <el-button
                class="toolbar-button toolbar-button--primary"
                type="primary"
                :disabled="!canManage || !canCreate || !detailRepository"
                :loading="loading.updating"
                @click="handleSaveAll"
              >
                保存
              </el-button>
            </div>
          </div>
          <RepositoryEditorLayout
            v-if="detailRepository"
            :model-value="detailRepository.content || ''"
            :language="detailRepository.language"
            placeholder="暂无代码"
            @update:model-value="detailRepository.content = $event"
          >
            <RepositoryDetailSidebar
              v-model:repository="detailRepository"
              :directory-options="directoryOptions"
              :language-options="LANGUAGE_OPTIONS"
              :can-manage="canManage"
              @dirty="markDetailDirty"
              @delete="handleDelete(detailRepository)"
            />
          </RepositoryEditorLayout>
          <el-empty
            v-else
            description="未选择脚本"
          />
        </div>
      </div>
    </section>

    <RepositoryDirectoryManagerDialog
      ref="directoryDialogRef"
      v-model:visible="directoryManagerVisible"
      v-model:form="directoryForm"
      :form-rules="directoryFormRules"
      :directory-managing="directoryManaging"
      :editing-directory-key="editingDirectoryKey"
      :available-directories="availableDirectories"
      :can-manage="canManage"
      @reset="resetDirectoryForm"
      @save="submitDirectorySave"
      @edit="startEditDirectory"
      @delete="handleDeleteDirectory"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue';
import type { FormInstance } from 'element-plus';

import RepositoryDirectorySidebar from '@/features/tools/components/RepositoryDirectorySidebar.vue';
import RepositoryEditorLayout from '@/features/tools/components/RepositoryEditorLayout.vue';
import RepositoryCreateFormCard from '@/features/tools/components/RepositoryCreateFormCard.vue';
import RepositoryDetailSidebar from '@/features/tools/components/RepositoryDetailSidebar.vue';
import RepositoryDirectoryManagerDialog from '@/features/tools/components/RepositoryDirectoryManagerDialog.vue';
import RepositoryListPanel from '@/features/tools/components/RepositoryListPanel.vue';
import { codePlaceholder, LANGUAGE_OPTIONS } from '@/features/tools/utils/repositoryPageHelpers';
import { useCodeRepositoryPage } from '@/features/tools/composables/useCodeRepositoryPage';

const {
  availableDirectories,
  canCreate,
  canManage,
  createForm,
  createFormRef,
  createMode,
  createRules,
  currentDirectoryName,
  currentPage,
  detailMode,
  detailRepository,
  directoryForm,
  directoryFormRef,
  directoryFormRules,
  directoryGroups,
  directoryManagerVisible,
  directoryManaging,
  directoryOptions,
  editingDirectoryKey,
  exitCreateMode,
  exitDetailMode,
  filteredCurrentRepos,
  formatTime,
  handleCreateInline,
  handleDelete,
  handleDeleteDirectory,
  handleDirectoryCommand,
  handleDirectorySelect,
  handleEdit,
  handlePageChange,
  handlePageSizeChange,
  handleSaveAll,
  handleSortChange,
  handleView,
  languageFilter,
  loadRepositories,
  loading,
  markDetailDirty,
  navigateToDirectory,
  openCreateDialog,
  paginatedRepos,
  pageSize,
  pageSizeOptions,
  primaryNavTitle,
  repoKeyword,
  resolveDirectoryIcon,
  resetDirectoryForm,
  rowClassName,
  selectedDirectoryKey,
  sidebarCollapsed,
  startEditDirectory,
  submitDirectorySave,
} = useCodeRepositoryPage();

const createFormCardRef = ref<{ formRef?: FormInstance } | null>(null);
const directoryDialogRef = ref<{ formRef?: FormInstance } | null>(null);

watchEffect(() => {
  createFormRef.value = createFormCardRef.value?.formRef;
});

watchEffect(() => {
  directoryFormRef.value = directoryDialogRef.value?.formRef;
});
</script>

<style scoped>
.code-repository {
  height: 100%;
  background: var(--oa-bg-panel);
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.code-repository--detail {
  height: auto;
  min-height: 100%;
  overflow: visible;
}

.repository-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  border-left: 1px solid var(--oa-border-color);
  background: var(--oa-bg-panel);
  flex: 1;
  overflow: hidden;
}

.code-repository--detail .repository-panel {
  height: auto;
  overflow: visible;
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

.repository-body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.code-repository--detail .repository-body {
  overflow: visible;
}

.repository-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--oa-bg-panel);
  padding: 0 16px 0;
  overflow: hidden;
}

.code-repository--detail .repository-main {
  overflow: visible;
}


:deep(.is-selected-row) {
  background: rgba(14, 165, 233, 0.08) !important;
}

</style>
