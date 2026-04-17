import { computed, onMounted, ref, type ComputedRef, type Ref } from 'vue';

import {
  fetchAssetTypes,
  type AssetRecord,
  type AssetTypeSummary,
} from '@/features/assets/api/assetsApi';
import {
  compareAppCodeAsc,
  interfaceAvailabilityLabel,
  normalizeAppCode,
  stableSortBy,
  uniqueRowValues,
} from '@/features/assets/utils/assetHelpers';
import {
  applyAssetExtraFieldsToRow,
  buildAssetEffectiveColumns,
  buildAssetExtraFormFields,
  matchesAssetViewDefinition,
} from '@/features/assets/utils/assetViewEnhancement';
import type {
  AssetRow,
  AssetViewDefinition,
  AssetViewKey,
} from '@/features/assets/types/assetCenter';

export function useAssetViewPresentation(options: {
  assets: Ref<AssetRecord[]>;
  facets: Ref<Record<string, string[]>>;
  viewKey: ComputedRef<AssetViewKey>;
  viewConfig: ComputedRef<AssetViewDefinition>;
}) {
  const { assets, facets, viewKey, viewConfig } = options;

  const assetTypes = ref<AssetTypeSummary[]>([]);

  const backendAssetType = computed<AssetTypeSummary | undefined>(() => {
    const keys = viewConfig.value.assetTypes || [];
    if (!keys.length) return undefined;
    return assetTypes.value.find((item) => keys.includes(item.key));
  });

  const extraFormFields = computed(() =>
    buildAssetExtraFormFields(viewKey.value, backendAssetType.value)
  );

  const currentFormFields = computed(() =>
    viewConfig.value.formFields.concat(extraFormFields.value)
  );

  const createDialogTitle = computed(() => `新增${viewConfig.value.title}`);
  const currentImportTemplate = computed(() => viewConfig.value.importTemplate);
  const canImport = computed(() => Boolean(currentImportTemplate.value));

  const effectiveColumns = computed(() =>
    buildAssetEffectiveColumns(viewConfig.value.columns || [], backendAssetType.value)
  );

  const matchingRecords = computed(() =>
    assets.value.filter((record) => matchesAssetViewDefinition(record, viewConfig.value))
  );

  const shapedRows = computed(() =>
    matchingRecords.value
      .map((record) => {
        const row = viewConfig.value.transform(record);
        if (!row) return null;
        applyAssetExtraFieldsToRow(row, record, backendAssetType.value);
        return row;
      })
      .filter((row): row is AssetRow => Boolean(row))
  );

  const proxyOptions = computed(() => facets.value.proxy || uniqueRowValues(shapedRows.value, 'proxy'));

  const interfaceAvailableOptions = computed(() => {
    const raw = facets.value.interface_available || uniqueRowValues(shapedRows.value, 'interface_available');
    const mapped = raw
      .map((item) => {
        const label = interfaceAvailabilityLabel(item);
        return label === '-' ? '' : label;
      })
      .filter(Boolean);
    const unique = Array.from(new Set(mapped));
    const base = ['可用', '不可用', '未知', '停用'];
    const rest = unique
      .filter((value) => !base.includes(value))
      .sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));
    return [...base, ...rest];
  });

  const appStatusOptions = computed(() =>
    facets.value.app_status || uniqueRowValues(shapedRows.value, 'app_status')
  );

  const displayRows = computed(() => {
    let rows = shapedRows.value;
    if (viewKey.value === 'ipmp-project') {
      rows = stableSortBy(rows, (row) => normalizeAppCode(row.app_code), compareAppCodeAsc);
    }
    return rows;
  });

  const pagedRows = computed(() => displayRows.value);

  async function loadAssetTypes() {
    try {
      assetTypes.value = await fetchAssetTypes();
    } catch (error) {
      // 资产类型仅用于增强展示，失败不阻断主流程。
      console.error('加载资产类型失败', error);
    }
  }

  onMounted(() => {
    void loadAssetTypes();
  });

  return {
    appStatusOptions,
    backendAssetType,
    canImport,
    createDialogTitle,
    currentFormFields,
    currentImportTemplate,
    displayRows,
    effectiveColumns,
    interfaceAvailableOptions,
    matchingRecords,
    pagedRows,
    proxyOptions,
    shapedRows,
  };
}
