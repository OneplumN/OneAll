import type {
  AssetRecord,
  AssetTypeSummary,
} from '@/features/assets/api/assetsApi';
import type {
  AssetColumn,
  AssetFormField,
  AssetRow,
  AssetViewDefinition,
  AssetViewKey,
} from '@/features/assets/types/assetCenter';

export function matchesAssetViewDefinition(record: AssetRecord, definition: AssetViewDefinition) {
  if (definition.source && record.source !== definition.source) {
    return false;
  }

  if (definition.assetTypes && definition.assetTypes.length) {
    const recordType = String(
      record.metadata?.asset_type || record.metadata?.category || record.metadata?.type || ''
    ).toLowerCase();
    if (recordType && !definition.assetTypes.map((item) => item.toLowerCase()).includes(recordType)) {
      return false;
    }
  }

  return true;
}

export function buildAssetExtraFormFields(
  viewKey: AssetViewKey,
  assetType?: AssetTypeSummary
): AssetFormField[] {
  if (viewKey !== 'workorder-host' || !assetType) return [];

  return (assetType.extra_fields || [])
    .filter((field) => field.key)
    .map((field) => {
      const key = field.key as string;
      const type = field.type || 'string';
      const base: AssetFormField = {
        key,
        label: field.label || key,
        component: 'input',
        required: Boolean(field.required),
        placeholder: ''
      };

      if (type === 'enum' && Array.isArray(field.options) && field.options.length) {
        return {
          ...base,
          component: 'select',
          options: field.options.map((option) => ({ label: option, value: option }))
        };
      }

      return base;
    });
}

export function buildAssetEffectiveColumns(
  baseColumns: AssetColumn[],
  assetType?: AssetTypeSummary
): AssetColumn[] {
  const uniqueSet = new Set(assetType?.unique_fields || []);

  const base = baseColumns.map((column) => ({
    ...column,
    isUnique: uniqueSet.has(column.key)
  }));

  const extras = (assetType?.extra_fields || []).filter((field) => field.list_visible !== false);
  if (!extras.length) return base;

  const existingKeys = new Set(base.map((column) => column.key));
  const extraColumns: AssetColumn[] = extras
    .filter((field) => field.key && !existingKeys.has(field.key))
    .map((field) => ({
      key: field.key,
      label: field.label || field.key,
      minWidth: 140,
      isUnique: uniqueSet.has(field.key)
    }));

  return [...base, ...extraColumns];
}

export function applyAssetExtraFieldsToRow(
  row: AssetRow,
  record: AssetRecord,
  assetType?: AssetTypeSummary
) {
  const extras = assetType?.extra_fields || [];
  if (!extras.length) return;

  const metadata = record.metadata || {};
  extras.forEach((field) => {
    const key = field.key;
    if (!key || row[key] !== undefined) return;
    const raw = (metadata as Record<string, unknown>)[key];
    if (raw === null || raw === undefined) {
      row[key] = '-';
      return;
    }
    const text = String(raw).trim();
    row[key] = text || '-';
  });
}
