import apiClient from '@/app/api/apiClient';

export interface MonitoringRequestPayload {
  title: string;
  target: string;
  system_name: string;
  network_type?: 'internal' | 'internet';
  owner_name?: string;
  alert_contacts?: string[];
  protocol: string;
  frequency_minutes?: number;
  probe_ids?: string[];
  alert_threshold?: number;
  description?: string;
  expected_status_codes?: number[];
}

export async function submitMonitoringRequest(payload: MonitoringRequestPayload) {
  const { data } = await apiClient.post('/monitoring/requests', payload);
  return data;
}

export async function listMonitoringRequests() {
  const { data } = await apiClient.get('/monitoring/requests');
  return data;
}

export interface MonitoringJobRecord {
  id: string;
  status: string;
  schedule_cron?: string;
  frequency_minutes?: number;
  last_run_at?: string | null;
  next_run_at?: string | null;
}

export interface MonitoringRequestRecord {
  id: string;
  title: string;
  target: string;
  protocol: string;
  description?: string;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled' | string;
  frequency_minutes?: number;
  schedule_cron?: string;
  metadata?: Record<string, any>;
  expected_status_codes?: number[];
  created_at?: string;
  updated_at?: string;
  jobs?: MonitoringJobRecord[];
  created_by_id?: string | null;
  created_by_username?: string;
}

export async function getMonitoringRequest(id: string) {
  const { data } = await apiClient.get<MonitoringRequestRecord>(`/monitoring/requests/${id}`);
  return data;
}

export async function updateMonitoringRequest(id: string, payload: Partial<MonitoringRequestPayload>) {
  const { data } = await apiClient.patch<MonitoringRequestRecord>(`/monitoring/requests/${id}`, payload);
  return data;
}

export async function approveMonitoringRequest(id: string) {
  const { data } = await apiClient.post<MonitoringRequestRecord>(`/monitoring/requests/${id}/approve`, {});
  return data;
}

export async function rejectMonitoringRequest(id: string, reason?: string) {
  const { data } = await apiClient.post<MonitoringRequestRecord>(`/monitoring/requests/${id}/reject`, {
    reason: reason || undefined
  });
  return data;
}

export async function resubmitMonitoringRequest(id: string) {
  const { data } = await apiClient.post<MonitoringRequestRecord>(`/monitoring/requests/${id}/resubmit`, {});
  return data;
}

export interface PluginConfigRecord {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  config: Record<string, unknown>;
  status: string;
  last_checked_at?: string | null;
  last_message?: string | null;
}

export async function listPluginConfigs() {
  const { data } = await apiClient.get<PluginConfigRecord[]>('/settings/plugins/');
  return data;
}

export async function updatePluginConfig(id: string, payload: Partial<PluginConfigRecord>) {
  const { data } = await apiClient.patch(`/settings/plugins/${id}/`, payload);
  return data;
}

export async function deletePluginConfig(id: string) {
  await apiClient.delete(`/settings/plugins/${id}/`);
}
