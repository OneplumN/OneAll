import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';

import {
  fetchAssetModels,
  queryAssets,
  syncAssetModel,
  createAsset,
  importAssets,
  type AssetModel,
  type AssetRecord,
  type QueryAssetsParams,
  type AssetCreatePayload,
} from '@/features/assets/api/assetsApi';
import {
  buildAssetCreateDraft,
  buildAssetModelFormFields,
  buildExportCsvContent,
  buildImportTemplateContent,
  buildModelFieldColumns,
  downloadTextFile,
  formatAssetDate as formatDate,
  formatFieldErrors,
  formatImportServerErrors,
  formatRowValue,
  formatSyncStatus,
  resolveSyncErrorMessage,
} from '@/features/assets/utils/assetModelCenterHelpers';
import { useSessionStore } from '@/app/stores/session';

const MAX_IMPORT_RECORDS = 500;

export function useAssetModelCenterPage() {
  const route = useRoute();
  const sessionStore = useSessionStore();

  const rootTitle = '资产信息';
  const canManage = computed(() => sessionStore.hasPermission('assets.records.manage'));
  const canCreate = computed(() => sessionStore.hasPermission('assets.records.create'));

  const models = ref<AssetModel[]>([]);
  const modelsLoading = ref(false);
  const activeModelId = ref<string>('');

  const assets = ref<AssetRecord[]>([]);
  const assetsLoading = ref(false);

  const keyword = ref('');
  const page = ref(1);
  const pageSize = ref(20);
  const total = ref(0);
  const pageSizeOptions = [20, 50, 100];

  const syncing = ref(false);

  const createDialogVisible = ref(false);
  const createSubmitting = ref(false);
  const createForm = ref<Record<string, any>>({});

  const importDialogVisible = ref(false);
  const importSubmitting = ref(false);
  const importPreviewRows = ref<Record<string, any>[]>([]);
  const importPayloads = ref<AssetCreatePayload[]>([]);
  const importErrors = ref<string[]>([]);
  const importFileName = ref('');

  const detailDialogVisible = ref(false);
  const detailRecord = ref<AssetRecord | null>(null);
  const detailRow = ref<Record<string, any> | null>(null);

  const activeModel = computed(() => models.value.find((m) => m.id === activeModelId.value));

  const sectionTitle = computed(() => {
    if (!activeModel.value) return '扩展模型';
    return `扩展模型 · ${activeModel.value.label || activeModel.value.key}`;
  });

  const modelFieldColumns = computed(() => buildModelFieldColumns(activeModel.value));
  const formFields = computed(() => buildAssetModelFormFields(activeModel.value));

  const createDialogTitle = computed(() => {
    const model = activeModel.value;
    if (!model) return '新增资产';
    return `新增${model.label || model.key}`;
  });

  const detailDisplayName = computed(() => detailRecord.value?.name || '-');

  const rows = computed(() => {
    const model = activeModel.value;
    if (!model) return [];
    return assets.value.map((record) => {
      const metadata = record.metadata || {};
      const base: Record<string, any> = {
        id: record.id,
        _name: record.name,
        _source: record.source,
        _external_id: record.external_id,
        _sync_status: formatSyncStatus(record.sync_status),
        _synced_at: record.synced_at || '',
      };
      for (const field of model.fields || []) {
        base[field.key] = metadata[field.key] ?? '-';
      }
      return base;
    });
  });

  const primaryFieldKey = computed(() => {
    const model = activeModel.value;
    if (!model) return '';
    if (model.unique_key && model.unique_key.length) return model.unique_key[0];
    const firstField = (model.fields || [])[0];
    return firstField?.key || '';
  });

  function openDetailDialog(row: Record<string, any>) {
    const record = assets.value.find((item) => item.id === row.id) || null;
    detailRecord.value = record;
    detailRow.value = row;
    detailDialogVisible.value = true;
  }

  function handleEditClick() {
    ElMessage.info('扩展模型当前暂不支持直接在列表中编辑记录，请通过同步脚本或导入更新。');
  }

  function openCreateDialog() {
    if (!activeModel.value) return;
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
    createForm.value = buildAssetCreateDraft(activeModel.value);
    createDialogVisible.value = true;
  }

  function resetCreateForm() {
    createForm.value = {};
  }

  async function handleCreateSubmit() {
    const model = activeModel.value;
    if (!model) return;
    const key = primaryFieldKey.value;
    if (!key) {
      ElMessage.warning('当前模型未配置唯一键，暂不支持手动新增');
      return;
    }
    const value = String(createForm.value[key] ?? '').trim();
    if (!value) {
      const label = (model.fields || []).find((f) => f.key === key)?.label || key;
      ElMessage.warning(`请填写${label}`);
      return;
    }

    const metadata: Record<string, any> = { asset_type: model.key };
    for (const field of model.fields || []) {
      const raw = createForm.value[field.key];
      if (raw === undefined || raw === null || raw === '') continue;
      metadata[field.key] = raw;
    }

    const payload: AssetCreatePayload = {
      source: 'Manual',
      name: value,
      metadata,
    };

    createSubmitting.value = true;
    try {
      await createAsset(payload);
      ElMessage.success('资产创建成功');
      createDialogVisible.value = false;
      resetCreateForm();
      await reloadAssets();
    } catch (err: any) {
      const data = err?.response?.data;
      const message =
        data?.detail ||
        (Array.isArray(data?.non_field_errors) && data.non_field_errors[0]) ||
        formatFieldErrors(data) ||
        '创建失败，请稍后重试';
      ElMessage.error(message);
    } finally {
      createSubmitting.value = false;
    }
  }

  function openImportDialog() {
    if (!activeModel.value) return;
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
    importDialogVisible.value = true;
  }

  function resetImportState() {
    importPreviewRows.value = [];
    importPayloads.value = [];
    importErrors.value = [];
    importFileName.value = '';
  }

  function downloadImportTemplate() {
    const model = activeModel.value;
    if (!model) return;
    const content = buildImportTemplateContent(model);
    downloadTextFile(`${model.key}-template.csv`, content);
  }

  function processImportRows(rows: Record<string, string>[]) {
    const model = activeModel.value;
    if (!model) return;
    const primaryKey = primaryFieldKey.value;
    if (!primaryKey) {
      importErrors.value = ['当前模型未配置唯一键，暂不支持导入'];
      return;
    }

    const fields = model.fields || [];
    const preview: Record<string, any>[] = [];
    const payloads: AssetCreatePayload[] = [];
    const errors: string[] = [];
    let nonEmptyCount = 0;

    rows.forEach((row, index) => {
      const empty = Object.values(row).every((value) => !String(value || '').trim());
      if (empty) return;
      nonEmptyCount += 1;
      if (nonEmptyCount > MAX_IMPORT_RECORDS) return;

      try {
        const mapped: Record<string, any> = {};
        fields.forEach((field) => {
          mapped[field.key] = row[field.key] ?? '';
        });
        const keyValue = String(mapped[primaryKey] ?? '').trim();
        if (!keyValue) {
          const label = fields.find((f) => f.key === primaryKey)?.label || primaryKey;
          throw new Error(`${label} 不能为空`);
        }

        const metadata: Record<string, any> = { asset_type: model.key };
        fields.forEach((field) => {
          const raw = mapped[field.key];
          if (raw === undefined || raw === null || raw === '') return;
          metadata[field.key] = raw;
        });

        preview.push(mapped);
        payloads.push({
          name: keyValue,
          metadata,
        });
      } catch (error) {
        errors.push(`第 ${index + 2} 行：${error instanceof Error ? error.message : String(error)}`);
      }
    });

    if (nonEmptyCount > MAX_IMPORT_RECORDS) {
      errors.unshift(`导入数据超过 ${MAX_IMPORT_RECORDS} 条（当前 ${nonEmptyCount} 条），请拆分文件后再导入。`);
    }

    importPreviewRows.value = preview;
    importPayloads.value = payloads;
    importErrors.value = errors;
  }

  async function handleImportFileChange(event: Event) {
    const model = activeModel.value;
    if (!model) return;
    const target = event.target as HTMLInputElement | null;
    const file = target?.files?.[0];
    if (!file) return;
    importFileName.value = file.name;
    importErrors.value = [];

    try {
      const text = await file.text();
      const lines = text
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line.length > 0);
      if (lines.length < 2) {
        importErrors.value = ['文件内容为空或缺少数据行'];
        importPreviewRows.value = [];
        importPayloads.value = [];
        return;
      }
      const header = lines[0].split(',').map((h) => h.trim());
      const rows = lines.slice(1).map((line) => {
        const parts = line.split(',');
        const row: Record<string, string> = {};
        header.forEach((key, index) => {
          row[key] = parts[index] ?? '';
        });
        return row;
      });

      processImportRows(rows);
    } catch (error) {
      console.error('Failed to parse import file', error);
      importPreviewRows.value = [];
      importPayloads.value = [];
      importErrors.value = ['文件解析失败，请确认格式为 CSV，且编码为 UTF-8。'];
    } finally {
      if (target) {
        target.value = '';
      }
    }
  }

  async function handleImportSubmit() {
    if (!importPreviewRows.value.length) return;
    if (importPayloads.value.length > MAX_IMPORT_RECORDS) {
      ElMessage.warning(`最多导入 ${MAX_IMPORT_RECORDS} 条，请拆分文件后重试`);
      return;
    }
    importSubmitting.value = true;
    try {
      const result = await importAssets(importPayloads.value);
      if (result.failed) {
        importErrors.value = formatImportServerErrors(result.errors || []);
        ElMessage.warning(`导入完成：成功 ${result.created} 条，失败 ${result.failed} 条`);
      } else {
        ElMessage.success(`导入成功：${result.created} 条`);
        importDialogVisible.value = false;
        resetImportState();
      }
      await reloadAssets();
    } catch (error) {
      console.error('import failed', error);
      ElMessage.error('导入失败，请检查文件内容或稍后重试');
    } finally {
      importSubmitting.value = false;
    }
  }

  function handleExportCsv() {
    const model = activeModel.value;
    if (!model || !rows.value.length) return;
    const content = buildExportCsvContent(model, rows.value);
    downloadTextFile(`${model.key}-export.csv`, content);
  }

  async function loadModels() {
    modelsLoading.value = true;
    try {
      const data = await fetchAssetModels();
      models.value = data || [];
      const routeModelKey = (route.params.modelKey as string | undefined) || '';
      if (routeModelKey) {
        const found = models.value.find((m) => m.key === routeModelKey);
        if (found) {
          activeModelId.value = found.id;
        } else if (!activeModelId.value && models.value.length) {
          activeModelId.value = models.value[0].id;
        }
      } else if (!activeModelId.value && models.value.length) {
        activeModelId.value = models.value[0].id;
      }
    } catch (err) {
      console.error('加载资产模型失败', err);
    } finally {
      modelsLoading.value = false;
    }
  }

  async function reloadAssets() {
    const model = activeModel.value;
    if (!model) {
      assets.value = [];
      total.value = 0;
      return;
    }
    assetsLoading.value = true;
    try {
      const params: QueryAssetsParams = {
        asset_type: model.key,
        limit: pageSize.value,
        offset: (page.value - 1) * pageSize.value,
      };
      if (keyword.value.trim()) {
        params.keyword = keyword.value.trim();
      }
      const { items, pagination } = await queryAssets(params);
      const rawItems = items || [];
      const pk = primaryFieldKey.value;
      const filtered = rawItems.filter((record) => {
        const metadata = record.metadata || {};
        const type = String(metadata.asset_type || '').trim();
        if (type !== model.key) return false;
        if (!pk) return true;
        const v = String(metadata[pk] ?? '').trim();
        return !!v;
      });

      assets.value = filtered;
      total.value = pagination?.total ?? filtered.length ?? 0;
    } catch (err) {
      console.error('加载资产数据失败', err);
      ElMessage.error('加载资产数据失败，请稍后重试');
    } finally {
      assetsLoading.value = false;
    }
  }

  function handlePageChange(value: number) {
    page.value = value;
    void reloadAssets();
  }

  function handlePageSizeChange(value: number) {
    pageSize.value = value;
    page.value = 1;
    void reloadAssets();
  }

  function handleKeywordClear() {
    page.value = 1;
    void reloadAssets();
  }

  async function handleSync() {
    const model = activeModel.value;
    if (!model) return;
    if (!canManage.value) {
      ElMessage.warning('您没有执行同步的权限');
      return;
    }
    syncing.value = true;
    try {
      const result = await syncAssetModel(model.id);
      const totals = result.summary?.totals || {};
      const created = totals.created ?? 0;
      const updated = totals.updated ?? 0;
      const removed = totals.removed ?? 0;
      ElMessage.success(`资产同步完成：新增 ${created} 条，更新 ${updated} 条${removed ? `，移除 ${removed} 条` : ''}`);
      await reloadAssets();
    } catch (err: any) {
      ElMessage.error(resolveSyncErrorMessage(err));
    } finally {
      syncing.value = false;
    }
  }

  onMounted(async () => {
    await loadModels();
    await reloadAssets();
  });

  watch(
    () => route.params.modelKey as string | undefined,
    async (modelKey) => {
      const key = modelKey || '';
      if (!key) return;

      if (!models.value.length) {
        await loadModels();
      }

      const found = models.value.find((m) => m.key === key);
      if (!found) return;

      if (activeModelId.value === found.id) return;
      activeModelId.value = found.id;
      page.value = 1;
      await reloadAssets();
    }
  );

  return {
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
    handlePageChange,
    handlePageSizeChange,
    handleKeywordClear,
    reloadAssets,
    handleCreateSubmit,
    resetCreateForm,
    downloadImportTemplate,
    handleImportFileChange,
    handleImportSubmit,
    resetImportState,
    openDetailDialog,
    handleEditClick,
  };
}
