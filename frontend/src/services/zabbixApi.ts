import apiClient from './apiClient';

export interface ZabbixAlert {
  id: string;
  severity: string;
  host: string;
  message: string;
  duration: string;
  started_at: string;
}

export interface ZabbixHostItem {
  label: string;
  description: string;
  value: number;
  status: 'ok' | 'warn' | 'danger';
}

export interface ZabbixHostOverview {
  total: number;
  items: ZabbixHostItem[];
}

export interface ZabbixSyncEntry {
  time: string;
  scope: string;
  duration: string;
  result: string;
  message: string;
}

export interface ZabbixDashboardMetrics {
  total_hosts: number;
  problem_hosts: number;
  open_problems: number;
  avg_problem_age_seconds: number;
  available_hosts?: number;
  unavailable_hosts?: number;
  maintenance_hosts?: number;
}

export interface ZabbixProxyStats {
  total: number;
  online: number;
  offline: number;
}

export interface ZabbixSeverityBreakdown {
  disaster: number;
  high: number;
  average: number;
  warning: number;
  information: number;
}

export interface ZabbixSystemInfo {
  is_running: boolean;
  server_address: string;
  server_version: string;
  frontend_version: string;
  update_checked_at: string;
  latest_release: string;
  latest_release_notes: string;
  hosts_enabled: number;
  hosts_disabled: number;
  triggers_total: number;
  triggers_problem: number;
  users_total: number;
  users_online: number;
  ha_status: string;
}

export interface ZabbixDashboardResponse {
  metrics: ZabbixDashboardMetrics;
  alerts: ZabbixAlert[];
  host_overview: ZabbixHostOverview;
  sync_history: ZabbixSyncEntry[];
  proxy_stats?: ZabbixProxyStats;
  severity_breakdown?: ZabbixSeverityBreakdown;
  system_info?: ZabbixSystemInfo;
  refreshed_at?: string;
}

export async function fetchZabbixDashboard(forceRefresh = false) {
  const { data } = await apiClient.get<ZabbixDashboardResponse>('/integrations/zabbix/dashboard', {
    params: forceRefresh ? { force: 1 } : undefined
  });
  return data;
}

export async function testZabbixConnection() {
  const { data } = await apiClient.post<{ detail: string; version?: string }>('/integrations/zabbix/test');
  return data;
}

export async function triggerZabbixSync() {
  const { data } = await apiClient.post('/integrations/zabbix/sync');
  return data as { status: string; history: ZabbixSyncEntry[]; refreshed_at?: string; metrics?: ZabbixDashboardMetrics };
}
