import { ref, type ComputedRef } from 'vue';
import { ElMessage } from 'element-plus';

import {
  importAssets,
  type AssetCreatePayload,
} from '@/features/assets/api/assetsApi';
import {
  decodeTextBuffer,
  extractWorkbookRows,
  isExcelFile,
  isRowEmpty,
  parseCsvContent,
} from '@/features/assets/utils/importParsing';
import {
  formatImportServerErrors,
  getErrorMessage,
} from '@/features/assets/utils/assetHelpers';
import type {
  AssetViewDefinition,
  ImportTemplate,
} from '@/features/assets/types/assetCenter';

const MAX_IMPORT_RECORDS = 500;

export function useAssetImport(options: {
  canCreate: ComputedRef<boolean>;
  currentImportTemplate: ComputedRef<ImportTemplate | undefined>;
  viewConfig: ComputedRef<AssetViewDefinition>;
  loadAssets: () => Promise<void>;
}) {
  const { canCreate, currentImportTemplate, viewConfig, loadAssets } = options;

  const importDialogVisible = ref(false);
  const importSubmitting = ref(false);
  const importPreviewRows = ref<Record<string, any>[]>([]);
  const importPayloads = ref<AssetCreatePayload[]>([]);
  const importErrors = ref<string[]>([]);
  const importFileName = ref('');

  const resetImportState = () => {
    importPreviewRows.value = [];
    importPayloads.value = [];
    importErrors.value = [];
    importFileName.value = '';
  };

  const openImportDialog = () => {
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
    resetImportState();
    importDialogVisible.value = true;
  };

  const downloadImportTemplate = () => {
    const template = currentImportTemplate.value;
    if (!template) return;
    const header = template.columns.map((col) => col.key).join(',');
    const sampleRow = template.columns.map((col) => col.sample ?? '').join(',');
    const content = `${header}\n${sampleRow}`;
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${viewConfig.value.title}-template.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const processImportRows = (rows: Record<string, string>[]) => {
    const template = currentImportTemplate.value;
    if (!template) return;
    const preview: Record<string, any>[] = [];
    const payloads: AssetCreatePayload[] = [];
    const errors: string[] = [];
    let nonEmptyCount = 0;

    rows.forEach((row, index) => {
      try {
        if (isRowEmpty(row)) return;
        nonEmptyCount += 1;
        if (nonEmptyCount > MAX_IMPORT_RECORDS) return;
        const mapped = template.mapRow(row);
        template.columns.forEach((col) => {
          if (col.required && !String(mapped[col.key] ?? '').trim()) {
            throw new Error(`${col.label} 不能为空`);
          }
        });
        const payload = viewConfig.value.buildPayload(mapped);
        preview.push(mapped);
        payloads.push(payload);
      } catch (error) {
        errors.push(
          `第 ${index + 1} 行：${
            error instanceof Error ? error.message : String(error)
          }`
        );
      }
    });

    if (nonEmptyCount > MAX_IMPORT_RECORDS) {
      errors.unshift(
        `导入数据超过 ${MAX_IMPORT_RECORDS} 条（当前 ${nonEmptyCount} 条），请拆分文件后再导入。`
      );
    }

    importPreviewRows.value = preview;
    importPayloads.value = payloads;
    importErrors.value = errors;
  };

  const handleImportFileChange = async (event: Event) => {
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
    const template = currentImportTemplate.value;
    if (!template) {
      importErrors.value = ['当前视图暂不支持导入。'];
      return;
    }
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;
    importFileName.value = file.name;
    importErrors.value = [];

    try {
      const buffer = await file.arrayBuffer();
      const headers = template.columns.map((col) => col.key);
      const rows = isExcelFile(file)
        ? await extractWorkbookRows(buffer, headers)
        : parseCsvContent(decodeTextBuffer(buffer), headers);
      processImportRows(rows);
    } catch (error) {
      console.error('Failed to parse import file', error);
      importPreviewRows.value = [];
      importPayloads.value = [];
      importErrors.value = ['文件解析失败，请确认格式为 CSV 或 Excel，且编码为 UTF-8/GBK。'];
    } finally {
      target.value = '';
    }
  };

  const handleImportSubmit = async () => {
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
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
      }
      await loadAssets();
    } catch (error) {
      ElMessage.error(getErrorMessage(error) || '导入失败，请检查文件内容');
    } finally {
      importSubmitting.value = false;
    }
  };

  return {
    importDialogVisible,
    importErrors,
    importFileName,
    importPayloads,
    importPreviewRows,
    importSubmitting,
    handleImportFileChange,
    handleImportSubmit,
    downloadImportTemplate,
    openImportDialog,
    resetImportState,
    maxImportRecords: MAX_IMPORT_RECORDS,
  };
}
