import { reactive, ref, type ComputedRef, type Ref } from 'vue';
import { ElMessage } from 'element-plus';

import {
  createAsset,
  updateAsset,
  type AssetCreatePayload,
  type AssetRecord,
  type AssetTypeSummary,
} from '@/features/assets/api/assetsApi';
import {
  formatPeople,
  getErrorMessage,
  normalizeOnlineStatusCode,
  onlineStatusFromRecord,
  onlineStatusLabel,
} from '@/features/assets/utils/assetHelpers';
import type {
  AssetFormField,
  AssetRow,
  AssetViewDefinition,
  AssetViewKey,
  OnlineStatusCode,
} from '@/features/assets/types/assetCenter';

export function useAssetRecordMutations(options: {
  assets: Ref<AssetRecord[]>;
  canCreate: ComputedRef<boolean>;
  canManage: ComputedRef<boolean>;
  viewKey: ComputedRef<AssetViewKey>;
  viewConfig: ComputedRef<AssetViewDefinition>;
  currentFormFields: ComputedRef<AssetFormField[]>;
  backendAssetType: ComputedRef<AssetTypeSummary | undefined>;
  matchingRecords: ComputedRef<AssetRecord[]>;
  showEditColumn: ComputedRef<boolean>;
  loadAssets: () => Promise<void>;
}) {
  const {
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
  } = options;

  const createDialogVisible = ref(false);
  const createSubmitting = ref(false);
  const createForm = reactive<Record<string, any>>({});
  const editDialogVisible = ref(false);
  const editSubmitting = ref(false);
  const editForm = reactive<Record<string, any>>({});
  const editingRecordId = ref<string | null>(null);
  const conflictDialogVisible = ref(false);
  const conflictRecord = ref<AssetRecord | null>(null);
  const detailDialogVisible = ref(false);
  const detailRecord = ref<AssetRecord | null>(null);
  const detailRow = ref<AssetRow | null>(null);
  const statusToggling = reactive<Record<string, boolean>>({});
  const selectedRowIds = ref<string[]>([]);

  const applyExtraFieldsToPayload = (payload: AssetCreatePayload, snapshot: Record<string, any>) => {
    const def = backendAssetType.value;
    const extras = def?.extra_fields || [];
    if (!extras.length) return;
    const metadata = { ...(payload.metadata || {}) };
    extras.forEach((field) => {
      const key = field.key;
      if (!key) return;
      const raw = snapshot[key];
      if (raw === undefined || raw === null) return;
      const text = String(raw).trim();
      if (!text) return;
      (metadata as any)[key] = raw;
    });
    payload.metadata = metadata;
  };

  const resetCreateForm = () => {
    currentFormFields.value.forEach((field) => {
      createForm[field.key] = field.default ?? '';
    });
  };

  const resetEditForm = () => {
    currentFormFields.value.forEach((field) => {
      editForm[field.key] = field.default ?? '';
    });
  };

  const openCreateDialog = () => {
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
    resetCreateForm();
    createDialogVisible.value = true;
  };

  const contactsToInput = (value: unknown): string => {
    if (Array.isArray(value)) {
      return value
        .map((item) => (typeof item === 'string' ? item : item?.id || item?.name))
        .filter(Boolean)
        .join(',');
    }
    if (typeof value === 'string') return value;
    return '';
  };

  const fillEditFormFromRecord = (record: AssetRecord) => {
    if (viewKey.value !== 'workorder-host') return;
    const metadata = record.metadata || {};
    editForm.ip = metadata.ip || metadata.host_ip || '';
    editForm.online_status = onlineStatusFromRecord(record) || 'online';
    editForm.idc = metadata.idc || metadata.idc_name || '';
    editForm.proxy = metadata.proxy || metadata.proxy_name || '';
    const port = metadata.port;
    editForm.port = typeof port === 'number' ? port : port ? Number(port) : undefined;
    editForm.alert_contacts = contactsToInput(metadata.alert_contacts || record.contacts);
    editForm.hostname = metadata.hostname || record.name || '';
    editForm.app_system = metadata.app_system || metadata.application || record.system_name || '';
    const owner = metadata.owner || metadata.system_owner || formatPeople(record.owners);
    editForm.owner = owner === '-' ? '' : owner;

    const def = backendAssetType.value;
    const extras = def?.extra_fields || [];
    extras.forEach((field) => {
      const key = field.key;
      if (!key) return;
      const raw = (metadata as any)[key];
      editForm[key] = raw === undefined || raw === null ? '' : raw;
    });
  };

  const openEditDialog = (row: AssetRow) => {
    if (!showEditColumn.value) return;
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    const record = matchingRecords.value.find((item) => item.id === row.id);
    if (!record) {
      ElMessage.error('找不到对应资产记录');
      return;
    }
    resetEditForm();
    editingRecordId.value = record.id;
    fillEditFormFromRecord(record);
    editDialogVisible.value = true;
  };

  const validateForm = (form: Record<string, any>) => {
    const missingField = currentFormFields.value.find((field) => {
      if (!field.required) return false;
      const value = form[field.key];
      if (field.component === 'number') {
        return value === undefined || value === null || value === '';
      }
      return !value || !String(value).trim();
    });
    if (missingField) {
      ElMessage.error(`请输入${missingField.label}`);
      return false;
    }
    return true;
  };

  const handleSelectionChange = (rows: Array<{ id: string }>) => {
    if (viewKey.value !== 'workorder-host') return;
    selectedRowIds.value = rows.map((row) => row.id).filter(Boolean);
  };

  const updateWorkorderOnlineStatus = async (recordId: string, next: OnlineStatusCode) => {
    if (viewKey.value !== 'workorder-host') return;
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    const record = matchingRecords.value.find((item) => item.id === recordId);
    if (!record) return;
    if (statusToggling[recordId]) return;
    statusToggling[recordId] = true;
    try {
      const metadata = { ...(record.metadata || {}), online_status: next, asset_type: 'workorder-host' };
      await updateAsset(recordId, { metadata });
      assets.value = assets.value.map((item) =>
        item.id === recordId ? { ...item, metadata } : item
      );
    } catch {
      ElMessage.error('状态更新失败，请稍后重试');
    } finally {
      statusToggling[recordId] = false;
    }
  };

  const handleRowStatusCommand = (row: AssetRow, command: unknown) => {
    const next = normalizeOnlineStatusCode(command);
    if (!next) return;
    void updateWorkorderOnlineStatus(row.id, next);
  };

  const batchUpdateWorkorderOnlineStatus = async (next: OnlineStatusCode) => {
    if (viewKey.value !== 'workorder-host') return;
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    const ids = selectedRowIds.value;
    if (!ids.length) return;
    const tasks = ids.filter((id) => !statusToggling[id]).map((id) => updateWorkorderOnlineStatus(id, next));
    await Promise.all(tasks);
    ElMessage.success(`已批量设置为「${onlineStatusLabel(next)}」`);
  };

  const handleBatchStatusCommand = (command: unknown) => {
    const next = normalizeOnlineStatusCode(command);
    if (!next) return;
    void batchUpdateWorkorderOnlineStatus(next);
  };

  const handleEditSubmit = async () => {
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    if (!editingRecordId.value) return;
    if (!validateForm(editForm)) return;
    editSubmitting.value = true;
    try {
      const snapshot: Record<string, any> = {};
      currentFormFields.value.forEach((field) => {
        snapshot[field.key] = editForm[field.key];
      });
      const payload = viewConfig.value.buildPayload(snapshot);
      applyExtraFieldsToPayload(payload, snapshot);
      await updateAsset(editingRecordId.value, {
        external_id: payload.external_id,
        name: payload.name,
        system_name: payload.system_name,
        owners: payload.owners,
        contacts: payload.contacts,
        metadata: payload.metadata,
      });
      ElMessage.success('已保存');
      editDialogVisible.value = false;
      editingRecordId.value = null;
      await loadAssets();
    } catch (error) {
      ElMessage.error(getErrorMessage(error) || '保存失败，请稍后重试');
    } finally {
      editSubmitting.value = false;
    }
  };

  const handleCreateSubmit = async () => {
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
    if (!validateForm(createForm)) return;
    createSubmitting.value = true;
    try {
      const snapshot: Record<string, any> = {};
      currentFormFields.value.forEach((field) => {
        snapshot[field.key] = createForm[field.key];
      });
      const payload = viewConfig.value.buildPayload(snapshot);
      applyExtraFieldsToPayload(payload, snapshot);
      await createAsset(payload);
      ElMessage.success('资产已创建');
      createDialogVisible.value = false;
      await loadAssets();
    } catch (error) {
      ElMessage.error(getErrorMessage(error) || '创建失败，请稍后重试');
    } finally {
      createSubmitting.value = false;
    }
  };

  const openConflictDialog = (row: AssetRow) => {
    const record = matchingRecords.value.find((item) => item.id === row.id);
    if (!record) {
      ElMessage.error('找不到对应资产记录');
      return;
    }
    conflictRecord.value = record;
    conflictDialogVisible.value = true;
  };

  const openDetailDialog = (row: AssetRow) => {
    const record = matchingRecords.value.find((item) => item.id === row.id) || null;
    detailRecord.value = record;
    detailRow.value = row;
    detailDialogVisible.value = true;
  };

  resetCreateForm();
  resetEditForm();

  return {
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
  };
}
