import apiClient from '@/app/api/apiClient';

export interface ProbeNodeRecord {
  id: string;
  name: string;
  location: string;
  network_type: string;
  supported_protocols: string[];
  status: string;
  last_heartbeat_at: string | null;
  last_authenticated_at: string | null;
  ip_address?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ProbeRuntimePayload {
  probe: {
    id: string;
    name: string;
    status: string;
    location: string;
    network_type: string;
    supported_protocols: string[];
    last_heartbeat_at: string | null;
    last_authenticated_at: string | null;
  };
  heartbeat_delay_seconds: number | null;
  tasks: Record<string, number>;
  resource_metrics: Record<string, unknown>;
}

export type ProbeAgentConfig = Record<string, unknown> & {
  version?: string;
  heartbeat_interval?: number;
  task_poll_interval?: number;
  max_concurrent_tasks?: number;
  enabled_protocols?: string[];
  log_level?: string;
};

// 聚合后的探针健康摘要（用于列表视图）
export interface ProbeHealthItem {
  id: string;
  name: string;
  location: string;
  network_type: string;
  status: string;
  last_heartbeat_at: string | null;
  heartbeat_delay_seconds: number | null;
  uptime_seconds?: number | null;
  executions: number;
  success: number;
  failed: number;
  success_rate: number; // 0-100 之间，百分比
  avg_latency_ms: number | null;
  cpu_usage?: number | null;
  memory_usage_mb?: number | null;
   memory_usage_pct?: number | null;
  load_avg?: number | null;
  queue_depth?: number | null;
  active_tasks?: number | null;
}

export interface ProbeHealthResponse {
  items: ProbeHealthItem[];
  window: {
    hours: number;
    interval_minutes: number;
  };
}

export async function fetchProbeRuntime(probeId: string) {
  const { data } = await apiClient.get<ProbeRuntimePayload>(`/probes/nodes/${probeId}/runtime/`);
  return data;
}

export async function listProbeNodes() {
  const { data } = await apiClient.get<ProbeNodeRecord[]>('/probes/nodes/');
  return data;
}

export interface ProbeMetricsHistoryPoint {
  timestamp: string;
  cpu_usage: number;
  memory_usage_mb: number;
  queue_depth: number;
  active_workers: number;
  tasks_executed: number;
  heartbeats_sent: number;
}

export interface ProbeMetricsHistoryResponse {
  from: string;
  to: string;
  points: ProbeMetricsHistoryPoint[];
}

export async function fetchProbeAgentConfig(probeId: string) {
  const { data } = await apiClient.get<ProbeAgentConfig>(`/probes/nodes/${probeId}/config/`);
  return data;
}

export async function updateProbeAgentConfig(probeId: string, payload: ProbeAgentConfig) {
  const { data } = await apiClient.put<ProbeAgentConfig>(`/probes/nodes/${probeId}/config/`, payload);
  return data;
}

export async function fetchProbeHealth(params?: { hours?: number; interval_minutes?: number }) {
  const { data } = await apiClient.get<ProbeHealthResponse>('/probes/nodes/health/', {
    params
  });
  return data;
}

export async function fetchProbeMetricsHistory(
  probeId: string,
  params?: { hours?: number; interval_minutes?: number }
) {
  const { data } = await apiClient.get<ProbeMetricsHistoryResponse>(
    `/probes/nodes/${probeId}/metrics/history/`,
    { params }
  );
  return data;
}
