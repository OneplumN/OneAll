import apiClient from './apiClient';

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

export async function fetchProbeRuntime(probeId: string) {
  const { data } = await apiClient.get<ProbeRuntimePayload>(`/probes/nodes/${probeId}/runtime/`);
  return data;
}

export async function fetchProbeAgentConfig(probeId: string) {
  const { data } = await apiClient.get<ProbeAgentConfig>(`/probes/nodes/${probeId}/config/`);
  return data;
}

export async function updateProbeAgentConfig(probeId: string, payload: ProbeAgentConfig) {
  const { data } = await apiClient.put<ProbeAgentConfig>(`/probes/nodes/${probeId}/config/`, payload);
  return data;
}
