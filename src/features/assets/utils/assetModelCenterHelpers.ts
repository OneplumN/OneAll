import dayjs from 'dayjs';

import type { AssetModel } from '@/features/assets/api/assetsApi';

export type AssetModelFieldColumn = {
  key: string;
  label: string;
  minWidth: number;
  isUnique: boolean;
};

export type AssetModelFormField = {
  key: string;
  label: string;
  required: boolean;
  component: 'input' | 'number' | 'select';
  options?: Array<{ label: string; value: unknown }>;
};

export function buildModelFieldColumns(model?: AssetModel | null): AssetModelFieldColumn[] {
  if (!model) return [];
  return (model.fields || []).map((field) => ({
    key: field.key,
    label: field.label || field.key,
    minWidth: 160,
    isUnique: (model.unique_key || []).includes(field.key)
  }));
}

export function buildAssetModelFormFields(model?: AssetModel | null): AssetModelFormField[] {
  if (!model) return [];
  const requiredKeys = new Set(model.unique_key || []);

  return (model.fields || []).map((field) => {
    const rawType = (field.type || 'string').toLowerCase();

    if (rawType === 'number') {
      return {
        key: field.key,
        label: field.label || field.key,
        required: requiredKeys.has(field.key),
        component: 'number'
      };
    }

    if (rawType === 'boolean') {
      return {
        key: field.key,
        label: field.label || field.key,
        required: requiredKeys.has(field.key),
        component: 'select',
        options: [
          { label: '是', value: true },
          { label: '否', value: false }
        ]
      };
    }

    return {
      key: field.key,
      label: field.label || field.key,
      required: requiredKeys.has(field.key),
      component: 'input'
    };
  });
}

export function buildAssetCreateDraft(model?: AssetModel | null): Record<string, unknown> {
  if (!model) return {};
  return (model.fields || []).reduce<Record<string, unknown>>((draft, field) => {
    draft[field.key] = '';
    return draft;
  }, {});
}

export function buildImportTemplateContent(model?: AssetModel | null): string {
  if (!model) return '';
  const headers = (model.fields || []).map((field) => field.key).join(',');
  const sample = (model.fields || []).map(() => '').join(',');
  return `${headers}\n${sample}`;
}

export function buildExportCsvContent(
  model: AssetModel | null | undefined,
  rows: Array<Record<string, unknown>>
): string {
  if (!model || !rows.length) return '';
  const headers = (model.fields || []).map((field) => field.key);
  const headerLine = headers.join(',');
  const dataLines = rows.map((row) =>
    headers
      .map((key) => escapeCsvCell(row[key]))
      .join(',')
  );
  return [headerLine, ...dataLines].join('\n');
}

export function downloadTextFile(filename: string, content: string, contentType = 'text/csv;charset=utf-8;') {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function formatSyncStatus(value: string | undefined | null): string {
  const raw = (value || '').trim();
  if (!raw || raw === 'unknown') return '-';
  if (raw === 'synced' || raw === 'success') return '已同步';
  if (raw === 'manual') return '手工维护';
  if (raw === 'conflict') return '冲突';
  if (raw === 'needs_review') return '需人工检查';
  if (raw === 'removed') return '已移除';
  return raw;
}

export function formatAssetDate(value: string | null | undefined): string {
  if (!value) return '-';
  return dayjs(value).format('YYYY-MM-DD HH:mm');
}

export function formatRowValue(row: Record<string, unknown> | null, key: string): string {
  if (!row) return '-';
  const value = row[key];
  if (value === null || value === undefined) return '-';
  const text = String(value).trim();
  return text || '-';
}

export function formatImportServerErrors(items: Array<{ index: number; errors: Record<string, unknown> }>): string[] {
  if (!items || !items.length) return [];
  const lines: string[] = [];
  const maxLines = 50;
  const sorted = [...items].sort((a, b) => (a?.index ?? 0) - (b?.index ?? 0));

  sorted.slice(0, maxLines).forEach((item) => {
    const rowNo = (item?.index ?? 0) + 1;
    const messages = formatFieldErrors(item?.errors);
    lines.push(`第 ${rowNo} 条：${messages || '导入失败'}`);
  });

  if (sorted.length > maxLines) {
    lines.push(`还有 ${sorted.length - maxLines} 条错误未展示`);
  }

  return lines;
}

export function formatFieldErrors(value: unknown): string {
  if (!value || typeof value !== 'object') return '';
  const entries = Object.entries(value as Record<string, unknown>);
  const parts: string[] = [];
  entries.forEach(([field, detail]) => {
    const message = normalizeErrorMessage(detail);
    if (!message) return;
    if (!field || field === 'non_field_errors' || field === 'detail') {
      parts.push(message);
      return;
    }
    parts.push(`${field}：${message}`);
  });
  return parts.join('；');
}

export function resolveSyncErrorMessage(err: unknown): string {
  const detail = String((err as any)?.response?.data?.detail || '').trim();
  if (!detail) return '资产同步失败，请稍后重试';
  if (detail.includes('尚未配置真实数据源')) {
    return '当前模型尚未配置真实数据源，暂不可同步';
  }
  if (detail.includes('模板示例')) {
    return '当前脚本仍是模板示例，请先完善真实同步逻辑后再执行同步';
  }
  return detail;
}

function normalizeErrorMessage(detail: unknown): string {
  if (!detail) return '';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const texts = detail.map((item) => normalizeErrorMessage(item)).filter(Boolean);
    return texts.join('，');
  }
  if (typeof detail === 'object') {
    const maybeMessage = (detail as Record<string, unknown>)?.message ?? (detail as Record<string, unknown>)?.detail;
    if (typeof maybeMessage === 'string') return maybeMessage;
  }
  return String(detail);
}

function escapeCsvCell(value: unknown): string {
  if (value == null) return '';
  const text = String(value);
  if (text.includes(',') || text.includes('"') || text.includes('\n')) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}
