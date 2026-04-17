import dayjs from 'dayjs';

import type { AssetRecord, AssetSyncRun } from '@/features/assets/api/assetsApi';
import type {
  AssetRow,
  InterfaceAvailabilityCode,
  OnlineStatusCode,
} from '@/features/assets/types/assetCenter';

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

export function statusTagType(status: string) {
  if (!status) return 'info';
  if (status === '冲突') return 'danger';
  if (status === '需人工检查') return 'warning';
  if (status === '已同步') return 'success';
  if (status === '手工维护') return 'info';
  if (status === '已移除') return 'info';
  if (status === '可用') return 'success';
  if (status === '不可用') return 'danger';
  if (status === '未知') return 'info';
  if (status === '停用') return 'info';
  if (status === '生产') return 'success';
  if (status === '在建' || status === '挂起') return 'warning';
  if (
    status === '下线' ||
    status === '中止或取消' ||
    status.includes('中止') ||
    status.includes('取消')
  ) {
    return 'info';
  }
  if (status === '在线' || status === 'online') return 'success';
  if (status === '维护' || status === 'maintenance') return 'warning';
  if (status === '下线' || status === 'offline') return 'danger';
  if (status === 'success' || status === 'synced') return 'success';
  const text = String(status);
  if (
    text.includes('运行') ||
    text.includes('正常') ||
    text.includes('启用') ||
    text.includes('上线')
  ) {
    return 'success';
  }
  if (text.includes('维护') || text.includes('检修')) return 'warning';
  if (
    text.includes('停用') ||
    text.includes('下线') ||
    text.includes('终止') ||
    text.includes('失败')
  ) {
    return 'danger';
  }
  if (
    text.includes('测试') ||
    text.includes('灰度') ||
    text.includes('建设') ||
    text.includes('开发') ||
    text.includes('在研')
  ) {
    return 'warning';
  }
  if (status === 'warning') return 'warning';
  if (status === 'error' || status === 'failed') return 'danger';
  return 'info';
}

export function formatPeople(value: unknown): string {
  if (Array.isArray(value)) {
    const names = value
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          return item.name || item.username || item.id || '';
        }
        return '';
      })
      .filter(Boolean);
    if (names.length) return names.join('、');
  }
  if (typeof value === 'string') return value;
  return '-';
}

export function formatContacts(value: unknown): string {
  if (Array.isArray(value)) {
    const contacts = value
      .map((item) => (typeof item === 'string' ? item : item?.id || item?.name))
      .filter(Boolean);
    if (contacts.length) return contacts.join('、');
  }
  if (typeof value === 'string') return value;
  return '-';
}

export function formatArray(value: unknown): string {
  if (Array.isArray(value)) {
    const items = value
      .map((item) => (typeof item === 'string' ? item : item?.name || ''))
      .filter(Boolean);
    if (items.length) return items.join('、');
  }
  if (typeof value === 'string') return value;
  return '-';
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '-';
  return dayjs(value).format('YYYY-MM-DD HH:mm');
}

export function sanitizeCsvCell(value: unknown): string {
  const text = value == null ? '' : String(value);
  if (text.includes(',') || text.includes('"')) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function networkTypeLabel(code: string) {
  if (code === 'internal') return '内网域名';
  if (code === 'internet') return '互联网域名';
  return code || '-';
}

export function normalizeOnlineStatusCode(value: unknown): OnlineStatusCode {
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value ? 'online' : 'offline';
  if (typeof value === 'number') {
    if (value === 1) return 'online';
    if (value === 0) return 'offline';
    return '';
  }
  const text = String(value).trim();
  if (!text) return '';
  const lowered = text.toLowerCase();
  if (
    lowered === 'online' ||
    lowered === 'up' ||
    lowered === 'available' ||
    lowered === 'true' ||
    lowered === '1'
  ) {
    return 'online';
  }
  if (lowered === 'maintenance' || lowered === 'maint' || lowered === 'maintain') {
    return 'maintenance';
  }
  if (
    lowered === 'offline' ||
    lowered === 'down' ||
    lowered === 'unavailable' ||
    lowered === 'false' ||
    lowered === '0'
  ) {
    return 'offline';
  }
  if (
    text.includes('在线') ||
    text.includes('可用') ||
    text.includes('运行') ||
    text.includes('上线')
  ) {
    return 'online';
  }
  if (text.includes('维护') || text.includes('检修')) return 'maintenance';
  if (
    text.includes('下线') ||
    text.includes('不可用') ||
    text.includes('停用') ||
    text.includes('停机')
  ) {
    return 'offline';
  }
  return '';
}

export function onlineStatusFromRecord(record: AssetRecord): OnlineStatusCode {
  const metadata = record.metadata || {};
  const direct =
    metadata.online_status ??
    metadata.onlineStatus ??
    metadata.online ??
    metadata.availability;
  const directCode = normalizeOnlineStatusCode(direct);
  if (directCode) return directCode;

  const interfaceAvailable =
    metadata.interface_available_label ?? metadata.interface_available;
  const interfaceCode = normalizeOnlineStatusCode(interfaceAvailable);
  if (interfaceCode) return interfaceCode;

  const appStatus = metadata.app_status ?? metadata.status;
  const appCode = normalizeOnlineStatusCode(appStatus);
  if (appCode) return appCode;

  return '';
}

export function onlineStatusLabel(code: OnlineStatusCode): string {
  if (code === 'online') return '在线';
  if (code === 'maintenance') return '维护';
  if (code === 'offline') return '下线';
  return '-';
}

export function normalizeInterfaceAvailabilityCode(
  value: unknown
): InterfaceAvailabilityCode {
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value ? 'available' : 'unavailable';
  if (typeof value === 'number') {
    if (value === 1) return 'available';
    if (value === 2) return 'unavailable';
    if (value === 0) return 'unknown';
    return '';
  }
  const text = String(value).trim();
  if (!text || text === '-') return '';
  const lowered = text.toLowerCase();
  if (lowered === '1' || lowered === 'available' || lowered === 'up') {
    return 'available';
  }
  if (lowered === '2' || lowered === 'unavailable' || lowered === 'down') {
    return 'unavailable';
  }
  if (lowered === '0' || lowered === 'unknown') return 'unknown';
  if (lowered === 'disabled' || text.includes('停用')) return 'disabled';
  if (text.includes('不可用') || text.includes('不可达') || text.includes('异常')) {
    return 'unavailable';
  }
  if (text.includes('可用') || text.includes('正常')) return 'available';
  if (text.includes('未知')) return 'unknown';
  return '';
}

export function interfaceAvailabilityLabel(value: unknown): string {
  const code = normalizeInterfaceAvailabilityCode(value);
  if (code === 'available') return '可用';
  if (code === 'unavailable') return '不可用';
  if (code === 'unknown') return '未知';
  if (code === 'disabled') return '停用';
  const text = value == null ? '' : String(value).trim();
  return text || '-';
}

export function isZabbixHostDisabled(
  record: AssetRecord,
  metadata: Record<string, any>
): boolean {
  const raw =
    metadata.status ??
    metadata.host_status ??
    metadata.hostStatus ??
    metadata.enabled ??
    metadata.monitoring_status ??
    record.sync_status;
  if (raw === null || raw === undefined) return false;
  if (typeof raw === 'boolean') return !raw;
  if (typeof raw === 'number') return raw === 1;
  const text = String(raw).trim().toLowerCase();
  if (!text) return false;
  return text === '1' || text === 'disabled' || text.includes('停用');
}

export function formatImportServerErrors(
  items: Array<{ index: number; errors: Record<string, unknown> }>
): string[] {
  const lines: string[] = [];
  const maxLines = 50;
  const sorted = [...items].sort(
    (a, b) => (a?.index ?? 0) - (b?.index ?? 0)
  );

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

export function normalizeErrorMessage(detail: unknown): string {
  if (!detail) return '';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const texts = detail.map((item) => normalizeErrorMessage(item)).filter(Boolean);
    return texts.join('，');
  }
  if (typeof detail === 'object') {
    const maybeMessage = (detail as any)?.message ?? (detail as any)?.detail;
    if (typeof maybeMessage === 'string') return maybeMessage;
  }
  return String(detail);
}

export function getErrorMessage(error: unknown) {
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object') {
    const data = (error as any)?.response?.data;
    const detail = data?.detail || (error as any)?.message;
    if (detail) return String(detail);
    const nonField = data?.non_field_errors;
    if (Array.isArray(nonField) && nonField.length) {
      return String(nonField[0]);
    }
  }
  return '操作失败，请稍后重试';
}

export function isScriptMissingError(error: unknown) {
  const message = getErrorMessage(error);
  return message.includes('未找到名称或标签');
}

export function stableSortBy<T>(
  values: T[],
  selector: (value: T) => string,
  compare: (a: string, b: string) => number
): T[] {
  return values
    .map((value, index) => ({ value, index, key: selector(value) }))
    .sort((left, right) => {
      const result = compare(left.key, right.key);
      if (result !== 0) return result;
      return left.index - right.index;
    })
    .map((entry) => entry.value);
}

export function normalizeAppCode(value: unknown): string {
  const text = value == null ? '' : String(value).trim();
  if (!text || text === '-') return '';
  return text;
}

export function compareAppCodeAsc(a: string, b: string): number {
  if (!a && !b) return 0;
  if (!a) return 1;
  if (!b) return -1;
  const aMatch = /^([A-Za-z]+)?(\d+)?$/.exec(a);
  const bMatch = /^([A-Za-z]+)?(\d+)?$/.exec(b);
  const aPrefix = (aMatch?.[1] || '').toUpperCase();
  const bPrefix = (bMatch?.[1] || '').toUpperCase();
  if (aPrefix !== bPrefix) return aPrefix.localeCompare(bPrefix);
  const aNumRaw = aMatch?.[2];
  const bNumRaw = bMatch?.[2];
  if (aNumRaw && bNumRaw) {
    const aNum = Number(aNumRaw);
    const bNum = Number(bNumRaw);
    if (Number.isFinite(aNum) && Number.isFinite(bNum) && aNum !== bNum) {
      return aNum - bNum;
    }
  }
  return a.localeCompare(b);
}

export function normalizeFilterOption(value: unknown): string {
  const text = value == null ? '' : String(value).trim();
  if (!text || text === '-') return '';
  return text;
}

export function uniqueRowValues(rows: AssetRow[], key: string): string[] {
  const values = rows
    .map((row) => normalizeFilterOption(row[key]))
    .filter(Boolean);
  return Array.from(new Set(values)).sort((a, b) =>
    a.localeCompare(b, 'zh-Hans-CN')
  );
}

export function formatRowValue(row: AssetRow | null, key: string): string {
  if (!row) return '-';
  const value = row[key];
  if (value === null || value === undefined) return '-';
  const text = String(value).trim();
  return text || '-';
}

export function formatSyncRunSummary(run: AssetSyncRun): string {
  const summary = (run.summary || {}) as any;
  const totals = summary?.totals || {};
  const fetched = totals.fetched ?? 0;
  const created = totals.created ?? 0;
  const updated = totals.updated ?? 0;
  const removed = totals.removed ?? 0;
  const restored = totals.restored ?? 0;
  const conflicts = summary.conflicts ?? summary.canonical_conflicts ?? 0;
  const needsReview = summary.needs_review ?? 0;

  const parts: string[] = [];
  if (fetched) parts.push(`本次 ${fetched}`);
  if (created) parts.push(`新增 ${created}`);
  if (updated) parts.push(`更新 ${updated}`);
  if (restored) parts.push(`恢复 ${restored}`);
  if (removed) parts.push(`移除 ${removed}`);
  if (conflicts) parts.push(`冲突 ${conflicts}`);
  if (needsReview) parts.push(`需人工检查 ${needsReview}`);
  return parts.length ? parts.join('，') : '-';
}

export function formatSyncRunScope(run: AssetSyncRun): string {
  const summary = (run.summary || {}) as any;
  if (summary?.trigger_type === 'asset_model') {
    return summary?.model_key || '模型同步';
  }
  const filters = (run.source_filters || []).filter(Boolean);
  return filters.join(', ') || '全量同步';
}
