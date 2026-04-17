import { computed, reactive, ref, type ComputedRef, type Ref } from 'vue';
import { ElMessage } from 'element-plus';

import {
  fetchAssetSyncRuns,
  queryAssets,
  triggerAssetSync,
  type AssetRecord,
  type AssetSyncRun,
  type QueryAssetsParams,
} from '@/features/assets/api/assetsApi';
import { listPluginConfigs, type PluginConfigRecord } from '@/features/monitoring/api/monitoringApi';
import { executeScriptById, executeScriptByLabel } from '@/features/tools/api/scriptExecutor';
import { listToolExecutions, type ToolExecutionRecord } from '@/features/tools/api/toolsApi';
import {
  getErrorMessage,
  isScriptMissingError,
  sanitizeCsvCell,
} from '@/features/assets/utils/assetHelpers';
import type { IntegrationPluginDefinition } from '@/data/integrationPlugins';
import type {
  AssetRow,
  AssetViewDefinition,
  AssetViewKey,
} from '@/features/assets/types/assetCenter';

export function useAssetDataFlow(options: {
  canManage: ComputedRef<boolean>;
  viewKey: ComputedRef<AssetViewKey>;
  viewConfig: ComputedRef<AssetViewDefinition>;
  pluginDefinition: ComputedRef<IntegrationPluginDefinition | undefined>;
  keywordDebounced: Ref<string>;
  networkFilter: Ref<string>;
  onlineStatusFilter: Ref<string>;
  proxyFilter: Ref<string>;
  interfaceAvailableFilter: Ref<string>;
  appStatusFilter: Ref<string>;
  showProxyFilter: ComputedRef<boolean>;
  showInterfaceAvailableFilter: ComputedRef<boolean>;
  showAppStatusFilter: ComputedRef<boolean>;
  showOnlineStatusFilter: ComputedRef<boolean>;
  page: Ref<number>;
  pageSize: Ref<number>;
  matchesDefinition: (record: AssetRecord, definition: AssetViewDefinition) => boolean;
}) {
  const {
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
    matchesDefinition,
  } = options;

  const assets = ref<AssetRecord[]>([]);
  const totalCount = ref(0);
  const facets = ref<Record<string, string[]>>({});
  const facetsByView = reactive<Record<string, Record<string, string[]>>>({});
  const syncing = ref(false);
  const tableLoading = ref(false);
  const pluginConfig = ref<PluginConfigRecord | null>(null);
  const pluginConfigLoading = ref(false);
  const syncHistoryDialogVisible = ref(false);
  const syncHistoryLoading = ref(false);
  const syncHistoryRuns = ref<AssetSyncRun[]>([]);
  const runtimeMode = computed(() => pluginDefinition.value?.runtime.mode || 'embedded');
  const runtimeScriptDefault = computed(() => pluginDefinition.value?.runtime.scriptLabel || '');
  const pluginScriptLabel = computed(() => {
    const label = pluginConfig.value?.config?.script_label;
    return typeof label === 'string' ? label : '';
  });
  const pluginScriptRepositoryId = computed(() => {
    const repoId = pluginConfig.value?.config?.script_repository_id;
    return typeof repoId === 'string' ? repoId : undefined;
  });
  const runtimeScriptLabel = computed(() => pluginScriptLabel.value || runtimeScriptDefault.value);
  const shouldLoadPluginConfig = computed(
    () => runtimeMode.value === 'script' && Boolean(viewConfig.value.pluginType)
  );

  const buildQueryParams = (includeFacets: boolean, override?: { limit?: number; offset?: number }) => {
    const source = viewConfig.value.source;
    const assetTypes = viewConfig.value.assetTypes || [];
    const networkType = viewConfig.value.filters?.networkType ? networkFilter.value : '';

    const params: QueryAssetsParams = {
      source: source || undefined,
      asset_type: assetTypes.length === 1 ? assetTypes[0] : assetTypes,
      keyword: keywordDebounced.value,
      proxy: showProxyFilter.value ? proxyFilter.value : '',
      interface_available: showInterfaceAvailableFilter.value ? interfaceAvailableFilter.value : '',
      app_status: showAppStatusFilter.value ? appStatusFilter.value : '',
      online_status: showOnlineStatusFilter.value ? onlineStatusFilter.value : '',
      network_type: networkType,
      limit: override?.limit ?? pageSize.value,
      offset: override?.offset ?? (page.value - 1) * pageSize.value,
      include_facets: includeFacets,
      order: viewKey.value === 'ipmp-project' ? 'external_id' : 'synced_at',
      direction: viewKey.value === 'ipmp-project' ? 'asc' : 'desc',
    };

    return params;
  };

  const loadPluginConfig = async () => {
    if (!shouldLoadPluginConfig.value || !viewConfig.value.pluginType) {
      pluginConfig.value = null;
      return;
    }
    pluginConfigLoading.value = true;
    try {
      const configs = await listPluginConfigs();
      pluginConfig.value =
        configs.find((item: PluginConfigRecord) => item.type === viewConfig.value.pluginType) || null;
    } catch {
      pluginConfig.value = null;
    } finally {
      pluginConfigLoading.value = false;
    }
  };

  const loadAssets = async () => {
    tableLoading.value = true;
    try {
      const includeFacets = !facetsByView[viewKey.value];
      const result = await queryAssets(buildQueryParams(includeFacets));
      assets.value = (result.items || []) as AssetRecord[];
      totalCount.value = result.pagination?.total || 0;

      if (includeFacets && result.facets) {
        facetsByView[viewKey.value] = result.facets;
        facets.value = result.facets;
      } else {
        facets.value = facetsByView[viewKey.value] || {};
      }
    } finally {
      tableLoading.value = false;
    }
  };

  const waitForToolExecution = async (runId: string, timeoutMs: number): Promise<ToolExecutionRecord> => {
    const startedAt = Date.now();
    while (Date.now() - startedAt < timeoutMs) {
      const items = await listToolExecutions();
      const found = items.find((item) => item.run_id === runId);
      if (found && (found.status === 'succeeded' || found.status === 'failed')) {
        return found;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 1200));
    }
    throw new Error('同步脚本执行超时，请前往相关运维工具页面查看执行结果。');
  };

  const handleSync = async () => {
    if (viewKey.value === 'workorder-host') {
      ElMessage.info('工单纳管主机信息不支持同步资产');
      return;
    }
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    syncing.value = true;
    try {
      if (runtimeMode.value === 'script') {
        if (!runtimeScriptLabel.value && !pluginScriptRepositoryId.value) {
          throw new Error('当前视图尚未绑定同步脚本，请在脚本仓库或脚本插件中完成配置后重试。');
        }
        const parameters = {
          asset_view: viewKey.value,
          plugin: viewConfig.value.pluginType,
          full_snapshot: true,
          triggered_at: new Date().toISOString(),
        };
        const execution = pluginScriptRepositoryId.value
          ? await executeScriptById(pluginScriptRepositoryId.value, parameters)
          : await executeScriptByLabel(runtimeScriptLabel.value!, parameters);
        ElMessage.success(`已触发同步脚本（执行 ID: ${execution.run_id}），正在写入资产数据…`);
        const finalExecution = await waitForToolExecution(execution.run_id, 120_000);
        if (finalExecution.status !== 'succeeded') {
          throw new Error(finalExecution.error_message || '同步脚本执行失败');
        }
        const ingest = (finalExecution.metadata || {})?.asset_ingest;
        if (!ingest) {
          throw new Error('脚本执行完成，但未触发平台入库；请确认脚本 main() 返回 records（List[dict]）。');
        }
        ElMessage.success(
          `资产同步完成：新增 ${ingest.created ?? 0}，更新 ${ingest.updated ?? 0}，移除 ${ingest.removed ?? 0}（本次 ${ingest.fetched ?? 0}）`
        );
      } else {
        await triggerAssetSync({ mode: 'async', sources: viewConfig.value.pluginType });
        ElMessage.success('同步任务已触发');
      }
      await loadAssets();
    } catch (error) {
      if (runtimeScriptLabel.value && isScriptMissingError(error)) {
        ElMessage.error(`找不到脚本「${runtimeScriptLabel.value}」，请在脚本仓库中创建同名脚本后重试。`);
      } else {
        ElMessage.error(getErrorMessage(error));
      }
    } finally {
      syncing.value = false;
    }
  };

  const openSyncHistory = async () => {
    syncHistoryDialogVisible.value = true;
    syncHistoryLoading.value = true;
    try {
      const { items } = await fetchAssetSyncRuns({ limit: 20 });
      syncHistoryRuns.value = items || [];
    } catch {
      syncHistoryRuns.value = [];
      ElMessage.error('获取同步历史失败，请稍后重试');
    } finally {
      syncHistoryLoading.value = false;
    }
  };

  const handleExport = async () => {
    if (!totalCount.value) {
      ElMessage.warning('暂无可导出的数据');
      return;
    }
    if (totalCount.value > 5000) {
      ElMessage.warning(`当前数据量过大（${totalCount.value} 条），请先通过筛选缩小范围再导出`);
      return;
    }
    try {
      const result = await queryAssets(
        buildQueryParams(false, {
          limit: 5000,
          offset: 0,
        })
      );
      const records = (result.items || []) as AssetRecord[];
      const rows = records
        .filter((record) => matchesDefinition(record, viewConfig.value))
        .map((record) => viewConfig.value.transform(record))
        .filter((row): row is AssetRow => Boolean(row));

      const headers = viewConfig.value.columns.map((column) => column.label).join(',');
      const body = rows
        .map((row) => viewConfig.value.columns.map((column) => sanitizeCsvCell(row[column.key])).join(','))
        .join('\n');
      const blob = new Blob([`${headers}\n${body}`], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${viewConfig.value.title}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      ElMessage.error('导出失败，请稍后重试');
    }
  };

  return {
    assets,
    facets,
    facetsByView,
    loadAssets,
    loadPluginConfig,
    handleExport,
    handleSync,
    openSyncHistory,
    pluginConfig,
    pluginConfigLoading,
    syncHistoryDialogVisible,
    syncHistoryLoading,
    syncHistoryRuns,
    syncing,
    tableLoading,
    totalCount,
  };
}
