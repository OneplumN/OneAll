import { computed, onMounted, ref } from 'vue';

import {
  fetchMonitoringOverview,
  type MonitoringOverviewItem,
  type MonitoringOverviewPayload,
  type MonitoringOverviewStatus,
  type MonitoringOverviewSystem,
} from '@/features/alerts/api/alertsApi';
import type { HoneycombCell } from '@/features/dashboard/components/DetectionHoneycomb.vue';

export function useHomeOverviewPage() {
  const loading = ref(false);
  const overviewError = ref<string | null>(null);
  const monitoringOverview = ref<MonitoringOverviewPayload | null>(null);
  const selectedSystemName = ref<string | null>(null);

  const pageLoading = computed(() => loading.value && !monitoringOverview.value);

  const overviewSystems = computed<MonitoringOverviewSystem[]>(() =>
    sortOverviewSystems(monitoringOverview.value?.systems || [])
  );

  const overviewItems = computed(() => monitoringOverview.value?.items || []);

  const honeycombColumns = computed(() => {
    if (overviewSystems.value.length <= 6) return 3;
    if (overviewSystems.value.length <= 12) return 4;
    if (overviewSystems.value.length <= 24) return 6;
    if (overviewSystems.value.length <= 48) return 8;
    if (overviewSystems.value.length <= 80) return 10;
    if (overviewSystems.value.length <= 120) return 12;
    if (overviewSystems.value.length <= 160) return 14;
    return 16;
  });

  const honeycombSize = computed(() => {
    const count = overviewSystems.value.length;
    if (count > 160) return 14;
    if (count > 120) return 16;
    if (count > 80) return 18;
    if (count > 48) return 20;
    if (count > 24) return 24;
    if (count > 12) return 30;
    if (count > 6) return 36;
    return 42;
  });

  const isHoneycombCompact = computed(() => honeycombSize.value <= 24);

  const honeycombCells = computed<HoneycombCell[]>(() =>
    overviewSystems.value.map((system) => ({
      id: system.system_name,
      label: system.system_name,
      shortLabel:
        system.system_name === '未纳管域名' ? '未纳管' : abbreviateSystemName(system.system_name),
      value: `${system.domain_count}`,
      category: system.system_name === '未纳管域名' ? 'unmanaged' : 'default',
      status: system.status,
      description: `${statusLabel(system.status)} · ${system.domain_count} 个域名 / ${system.matched_strategy_count} 条策略`,
      meta: [
        `异常域名 ${system.abnormal_count}`,
        `总域名 ${system.domain_count}`,
        `策略数 ${system.matched_strategy_count}`,
        `最近检测 ${formatDateTime(system.last_checked_at)}`,
        ...(system.system_name === '未纳管域名'
          ? ['说明 这些目标未命中 CMDB 域名资产，暂未归属到具体系统']
          : []),
      ],
      payload: system,
    }))
  );

  const selectedSystem = computed<MonitoringOverviewSystem | null>(() => {
    if (!overviewSystems.value.length) return null;
    return (
      overviewSystems.value.find((system) => system.system_name === selectedSystemName.value) ||
      overviewSystems.value[0]
    );
  });

  const selectedItems = computed<MonitoringOverviewItem[]>(() => {
    if (!selectedSystem.value) return [];
    return overviewItems.value
      .filter((item) => item.system_name === selectedSystem.value?.system_name)
      .sort((left, right) => {
        if (left.latest_status !== right.latest_status) {
          return statusPriority(left.latest_status) - statusPriority(right.latest_status);
        }
        return displayTarget(left).localeCompare(displayTarget(right), 'zh-CN');
      });
  });

  async function refreshOverview() {
    loading.value = true;
    overviewError.value = null;
    try {
      const payload = await fetchMonitoringOverview();
      monitoringOverview.value = payload;
      const currentExists = payload.systems.some(
        (system) => system.system_name === selectedSystemName.value
      );
      selectedSystemName.value = currentExists
        ? selectedSystemName.value
        : sortOverviewSystems(payload.systems)[0]?.system_name ?? null;
    } catch {
      monitoringOverview.value = null;
      selectedSystemName.value = null;
      overviewError.value = '无法加载系统拨测总览。';
    } finally {
      loading.value = false;
    }
  }

  function handleSystemSelect(cell: HoneycombCell) {
    const payload = cell.payload as MonitoringOverviewSystem | undefined;
    selectedSystemName.value = payload?.system_name || cell.id;
  }

  function displayTarget(item: MonitoringOverviewItem): string {
    return item.resolved_domain || item.target;
  }

  onMounted(() => {
    void refreshOverview();
  });

  return {
    loading,
    overviewError,
    pageLoading,
    overviewSystems,
    honeycombCells,
    honeycombColumns,
    honeycombSize,
    isHoneycombCompact,
    selectedSystemName,
    selectedSystem,
    selectedItems,
    refreshOverview,
    handleSystemSelect,
    displayTarget,
    assetMatchLabel,
    formatDateTime,
    statusLabel,
    statusTextClass,
  };
}

function sortOverviewSystems(systems: MonitoringOverviewSystem[]): MonitoringOverviewSystem[] {
  return [...systems].sort((left, right) => {
    const priorityDiff = statusPriority(left.status) - statusPriority(right.status);
    if (priorityDiff !== 0) return priorityDiff;
    if (left.abnormal_count !== right.abnormal_count) {
      return right.abnormal_count - left.abnormal_count;
    }
    if (left.domain_count !== right.domain_count) {
      return right.domain_count - left.domain_count;
    }
    return left.system_name.localeCompare(right.system_name, 'zh-CN');
  });
}

function statusPriority(status: MonitoringOverviewStatus): number {
  if (status === 'danger') return 0;
  if (status === 'idle') return 1;
  return 2;
}

function statusLabel(status: MonitoringOverviewStatus): string {
  if (status === 'danger') return '异常';
  if (status === 'idle') return '无结果';
  return '正常';
}

function assetMatchLabel(status: string): string {
  if (status === 'missing_system') return '未配置系统';
  if (status === 'unmanaged') return '未纳管域名';
  if (status === 'invalid_target') return '目标无效';
  return '已纳管系统';
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

function abbreviateSystemName(value: string): string {
  const normalized = value.trim();
  if (!normalized) return '未命';
  if (/^[A-Za-z0-9_-]+$/.test(normalized)) {
    return normalized.slice(0, 4).toUpperCase();
  }
  return normalized.slice(0, 4);
}

function statusTextClass(status: MonitoringOverviewStatus): string {
  if (status === 'danger') return 'status-text status-text--danger';
  if (status === 'idle') return 'status-text status-text--idle';
  return 'status-text status-text--success';
}
