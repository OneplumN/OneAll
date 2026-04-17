import { computed, onBeforeUnmount, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { usePageTitle } from '@/composables/usePageTitle';
import { useSessionStore } from '@/app/stores/session';
import { useCodeDirectoryStore } from '@/features/tools/stores/codeDirectories';
import { useAppStore } from '@/app/stores/app';
import { useRepositoryBrowser } from '@/features/tools/composables/useRepositoryBrowser';
import { useCodeRepositoryPersistence } from '@/features/tools/composables/useCodeRepositoryPersistence';
import { useDirectoryManager } from '@/features/tools/composables/useDirectoryManager';

export function useCodeRepositoryPage() {
  usePageTitle('脚本仓库');

  const route = useRoute();
  const router = useRouter();
  const sessionStore = useSessionStore();
  const codeDirectoryStore = useCodeDirectoryStore();
  const appStore = useAppStore();

  const canCreate = computed(() => sessionStore.hasPermission('tools.repository.create'));
  const canManage = computed(() => sessionStore.hasPermission('tools.repository.manage'));
  const primaryNavTitle = computed(() => {
    const matched = route.matched?.[0];
    return (matched?.meta?.title as string) || (route.meta?.title as string) || '脚本仓库';
  });
  const directories = computed(() => codeDirectoryStore.directories);

  const {
    bindBrowser,
    createForm,
    createFormRef,
    createMode,
    createRules,
    detailMode,
    detailRepository,
    exitCreateMode,
    exitDetailMode,
    handleCreateInline,
    handleDelete,
    handleEdit,
    handleSaveAll,
    handleView,
    loadRepositories,
    loading,
    markDetailDirty,
    openCreateDialog,
    openRepoFromQuery,
    repositories,
    selectedRepository,
  } = useCodeRepositoryPersistence({
    route,
    router,
    canCreate,
    canManage,
  });

  const {
    availableDirectories,
    currentPage,
    currentDirectoryName,
    directoryGroups,
    directoryOptions,
    filteredCurrentRepos,
    formatTime,
    handleDirectorySelect,
    handlePageChange,
    handlePageSizeChange,
    handleSortChange,
    languageFilter,
    pageSize,
    pageSizeOptions,
    paginatedRepos,
    repoKeyword,
    resolveActiveDirectoryForForm,
    resolveDirectoryIcon,
    rowClassName,
    selectedDirectoryKey,
    sidebarCollapsed,
    sidebarWidth,
    syncDirectorySelection,
    ensureRepositorySelection,
    navigateToDirectory,
  } = useRepositoryBrowser({
    route,
    router,
    directories,
    repositories,
    selectedRepository,
    detailRepository,
  });

  bindBrowser({
    availableDirectories,
    ensureRepositorySelection,
    navigateToDirectory,
    resolveActiveDirectoryForForm,
    selectedDirectoryKey,
  });

  const {
    directoryManagerVisible,
    directoryForm,
    directoryFormRef,
    directoryFormRules,
    directoryManaging,
    editingDirectoryKey,
    handleDeleteDirectory,
    openDirectoryManager,
    resetDirectoryForm,
    startEditDirectory,
    submitDirectorySave,
  } = useDirectoryManager({
    canManage,
    codeDirectoryStore,
    syncDirectorySelection,
  });

  const handleDirectoryCommand = (command: string) => {
    if (command === 'manageDirectories') {
      openDirectoryManager();
    }
  };

  watch(
    () => [detailMode.value, createMode.value],
    ([detail, create]) => {
      appStore.setMainScrollLocked(!detail && !create);
    },
    { immediate: true }
  );

  onBeforeUnmount(() => {
    appStore.setMainScrollLocked(false);
  });

  watch(
    () => [
      repositories.value.map((repo) => repo.id).join(','),
      availableDirectories.value.map((dir) => dir.key).join(','),
      typeof route.params.directoryKey === 'string' ? route.params.directoryKey : '',
      typeof route.query.repoId === 'string' ? route.query.repoId : '',
      createMode.value,
    ],
    () => {
      ensureRepositorySelection();
      openRepoFromQuery();
    },
    { immediate: true }
  );

  watch(
    () => repositories.value,
    (list) => {
      if (selectedRepository.value) {
        const updated = list.find((repo) => repo.id === selectedRepository.value?.id);
        if (updated) {
          selectedRepository.value = updated;
        }
      }
      if (detailRepository.value) {
        const updatedDetail = list.find((repo) => repo.id === detailRepository.value?.id);
        if (updatedDetail) {
          detailRepository.value = updatedDetail;
        }
      }
    },
    { deep: false }
  );

  onMounted(async () => {
    if (!directories.value.length) {
      await codeDirectoryStore.fetchDirectories();
    }
    await loadRepositories();
  });

  return {
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
    sidebarWidth,
    startEditDirectory,
    submitDirectorySave,
  };
}
