import apiClient from '@/app/api/apiClient';

export interface RuntimeMetricsPoint {
  timestamp: string;
  queue_depth: number;
  active_workers: number;
  tasks_executed: number;
  heartbeats_sent: number;
}

export interface RuntimeMetricsResponse {
  from: string;
  to: string;
  points: RuntimeMetricsPoint[];
}

export interface ResultStatsPoint {
  timestamp: string;
  success: number;
  failed: number;
  avg_latency_ms: number | null;
}

export interface ResultStatsResponse {
  from: string;
  to: string;
  points: ResultStatsPoint[];
  total: {
    success: number;
    failed: number;
    success_rate: number;
    avg_latency_ms: number | null;
  };
}

export async function fetchProbeRuntimeHistory(
  probeId: string,
  params: { hours?: number; interval_minutes?: number } = {}
) {
  const { data } = await apiClient.get<RuntimeMetricsResponse>(
    `/probes/nodes/${probeId}/metrics/history/`,
    { params }
  );
  return data;
}

export async function fetchProbeResultStats(
  probeId: string,
  params: { hours?: number; interval_minutes?: number } = {}
) {
  const { data } = await apiClient.get<ResultStatsResponse>(
    `/probes/nodes/${probeId}/results/stats/`,
    { params }
  );
  return data;
}
