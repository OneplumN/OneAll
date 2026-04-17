import {
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
  type ComputedRef,
  type Ref,
} from 'vue';

import type { AssetViewKey } from '@/features/assets/types/assetCenter';

type StringArrayMap = Record<string, string[]>;

export function useAssetPageControls(options: {
  viewKey: ComputedRef<AssetViewKey>;
}) {
  const { viewKey } = options;

  const suppressReload = ref(false);
  const keyword = ref('');
  const keywordDebounced = ref('');
  const networkFilter = ref('');
  const onlineStatusFilter = ref('');
  const proxyFilter = ref('');
  const interfaceAvailableFilter = ref('');
  const appStatusFilter = ref('');
  const page = ref(1);
  const pageSize = ref(20);
  const pageSizeOptions = [10, 20, 50];

  let keywordDebounceTimer: number | null = null;

  const clearKeywordDebounceTimer = () => {
    if (!keywordDebounceTimer) return;
    window.clearTimeout(keywordDebounceTimer);
    keywordDebounceTimer = null;
  };

  const resetFilters = () => {
    keyword.value = '';
    keywordDebounced.value = '';
    networkFilter.value = '';
    onlineStatusFilter.value = '';
    proxyFilter.value = '';
    interfaceAvailableFilter.value = '';
    appStatusFilter.value = '';
    page.value = 1;
  };

  const resetPageAndReload = (loadAssets: () => Promise<void>) => {
    if (suppressReload.value) return;
    const current = page.value;
    page.value = 1;
    if (current === 1) {
      void loadAssets();
    }
  };

  const handlePageChange = (newPage: number) => {
    page.value = newPage;
  };

  const handlePageSizeChange = (newSize: number) => {
    pageSize.value = newSize;
    page.value = 1;
  };

  const bindLifecycle = (options: {
    shouldLoadPluginConfig: ComputedRef<boolean>;
    loadPluginConfig: () => Promise<void>;
    clearPluginConfig: () => void;
    loadAssets: () => Promise<void>;
    facets: Ref<StringArrayMap>;
    facetsByView: Record<string, StringArrayMap>;
    resetCreateForm: () => void;
    resetEditForm: () => void;
    resetImportState: () => void;
    createDialogVisible: Ref<boolean>;
    editDialogVisible: Ref<boolean>;
    editingRecordId: Ref<string | null>;
    importDialogVisible: Ref<boolean>;
    selectedRowIds: Ref<string[]>;
  }) => {
    const {
      shouldLoadPluginConfig,
      loadPluginConfig,
      clearPluginConfig,
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
    } = options;

    watch(viewKey, () => {
      suppressReload.value = true;
      clearKeywordDebounceTimer();
      resetFilters();
      selectedRowIds.value = [];
      resetCreateForm();
      resetEditForm();
      resetImportState();
      createDialogVisible.value = false;
      editDialogVisible.value = false;
      editingRecordId.value = null;
      importDialogVisible.value = false;
      if (shouldLoadPluginConfig.value) {
        void loadPluginConfig();
      } else {
        clearPluginConfig();
      }
      facets.value = facetsByView[viewKey.value] || {};
      suppressReload.value = false;
      void loadAssets();
    });

    resetCreateForm();
    resetEditForm();
    resetImportState();
    if (shouldLoadPluginConfig.value) {
      void loadPluginConfig();
    } else {
      clearPluginConfig();
    }

    watch(keyword, () => {
      page.value = 1;
      clearKeywordDebounceTimer();
      keywordDebounceTimer = window.setTimeout(() => {
        keywordDebounced.value = keyword.value.trim();
      }, 300);
    });

    watch(networkFilter, () => resetPageAndReload(loadAssets));
    watch(onlineStatusFilter, () => resetPageAndReload(loadAssets));
    watch(proxyFilter, () => resetPageAndReload(loadAssets));
    watch(interfaceAvailableFilter, () => resetPageAndReload(loadAssets));
    watch(appStatusFilter, () => resetPageAndReload(loadAssets));

    watch([page, pageSize], () => {
      if (suppressReload.value) return;
      void loadAssets();
    });

    watch(keywordDebounced, () => {
      resetPageAndReload(loadAssets);
    });

    onMounted(() => {
      void loadAssets();
    });

    onBeforeUnmount(() => {
      clearKeywordDebounceTimer();
    });
  };

  return {
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
    suppressReload,
  };
}
