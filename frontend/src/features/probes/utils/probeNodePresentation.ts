import dayjs from 'dayjs';

import type { ProbeHealthItem } from '@/features/probes/api/probeNodeApi';

type ProbeHealthLookup = Record<string, ProbeHealthItem | null | undefined>;
type ProbeStatusCarrier = { id: string; status: string };

export function formatAuthTime(value: string) {
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss');
}

export function statusTagType(status: string) {
  switch (status) {
    case 'online':
      return 'success';
    case 'maintenance':
      return 'warning';
    default:
      return 'info';
  }
}

export function statusLabel(status: string) {
  switch (status) {
    case 'online':
      return '在线';
    case 'maintenance':
      return '维护中';
    case 'offline':
      return '离线';
    default:
      return status || '未知';
  }
}

export function networkTypeLabel(networkType: string) {
  if (networkType === 'internal') return '内网';
  if (networkType === 'external') return '外网';
  return networkType || '未知网络';
}

export function heartbeatAgo(value: string) {
  const seconds = dayjs().diff(dayjs(value), 'second');
  if (seconds < 60) return `${seconds}s 前`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
}

export function effectiveStatus(probe: ProbeStatusCarrier, healthById: ProbeHealthLookup) {
  const health = getHealth(probe.id, healthById);
  return (health && health.status) || probe.status;
}

export function formatCpuUsage(probeId: string, healthById: ProbeHealthLookup) {
  const health = getHealth(probeId, healthById);
  const raw = health?.cpu_usage;
  if (raw == null || Number.isNaN(Number(raw))) return '—';
  const value = Number(raw);
  if (!Number.isFinite(value)) return '—';
  return `${value.toFixed(0)}%`;
}

export function formatMemoryUsage(probeId: string, healthById: ProbeHealthLookup) {
  const health = getHealth(probeId, healthById);
  const pctRaw = health?.memory_usage_pct;
  if (pctRaw != null && !Number.isNaN(Number(pctRaw))) {
    const pct = Number(pctRaw);
    if (Number.isFinite(pct)) {
      return `${pct.toFixed(0)}%`;
    }
  }
  const rawMb = health?.memory_usage_mb;
  if (rawMb == null || Number.isNaN(Number(rawMb))) return '—';
  const value = Number(rawMb);
  if (!Number.isFinite(value)) return '—';
  if (value >= 1024) {
    return `${(value / 1024).toFixed(1)} GB`;
  }
  return `${value.toFixed(0)} MB`;
}

export function formatQueueDepth(probeId: string, healthById: ProbeHealthLookup) {
  const health = getHealth(probeId, healthById);
  const raw = health?.queue_depth;
  if (raw == null || Number.isNaN(Number(raw))) return '--';
  const value = Number(raw);
  if (!Number.isFinite(value)) return '--';
  return `${value}`;
}

export function uptimeDisplay(probeId: string, healthById: ProbeHealthLookup) {
  const health = getHealth(probeId, healthById);
  if (!health) return '未上报';
  const seconds = Number(health.uptime_seconds);
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return '未上报';
  }
  return formatDuration(seconds);
}

export function formatExecutions(probeId: string, healthById: ProbeHealthLookup) {
  const health = getHealth(probeId, healthById);
  if (!health) return '未上报';
  return health.executions ?? 0;
}

export function formatFailureRate(probeId: string, healthById: ProbeHealthLookup) {
  const health = getHealth(probeId, healthById);
  if (!health || !health.executions) return '未上报';
  const failed = health.failed ?? 0;
  const rate = typeof health.success_rate === 'number' ? health.success_rate : 0;
  return `${failed} / ${rate.toFixed(1)}%`;
}

export function formatAvgLatency(probeId: string, healthById: ProbeHealthLookup) {
  const health = getHealth(probeId, healthById);
  if (!health || health.avg_latency_ms == null) return '未上报';
  const value = Number(health.avg_latency_ms);
  if (!Number.isFinite(value)) return '未上报';
  return `${value.toFixed(1)} ms`;
}

export function hasHealthSummary(healthById: ProbeHealthLookup) {
  return Object.keys(healthById).length > 0;
}

function getHealth(probeId: string, healthById: ProbeHealthLookup) {
  return healthById[probeId] || null;
}

function formatDuration(totalSeconds: number) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} 分钟`;
  const hours = Math.floor(minutes / 60);
  const remMinutes = minutes % 60;
  if (hours < 24) {
    return remMinutes ? `${hours} 小时 ${remMinutes} 分钟` : `${hours} 小时`;
  }
  const days = Math.floor(hours / 24);
  const remHours = hours % 24;
  if (remHours) {
    return `${days} 天 ${remHours} 小时`;
  }
  return `${days} 天`;
}
