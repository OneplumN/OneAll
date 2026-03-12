import apiClient from './apiClient';

export interface ProbeNodeSummary {
  id: string;
  name: string;
  location: string;
  network_type: string;
  status: string;
}

export interface MonitoringRequestSummary {
  id: string;
  title: string;
  status: string;
  itsm_ticket_id?: string | null;
  frequency_minutes: number;
}

export interface ProbeScheduleRecord {
  id: string;
  name: string;
  description: string;
  target: string;
  protocol: string;
  frequency_minutes: number;
  start_at?: string | null;
  end_at?: string | null;
  status: string;
  status_display: string;
  status_reason?: string;
  source_type: string;
  source_display: string;
  source_id?: string | null;
  metadata: Record<string, unknown> | null;
  monitoring_request?: MonitoringRequestSummary | null;
  monitoring_job?: string | null;
  last_run_at?: string | null;
  next_run_at?: string | null;
  created_at: string;
  updated_at: string;
  probes: ProbeNodeSummary[];
  timeout_seconds?: number | null;
  expected_status_codes?: number[] | null;
  alert_threshold?: number | null;
  alert_contacts?: string[] | null;
}

export interface ProbeScheduleFilters {
  status?: string;
  source?: string;
  probe_id?: string;
}

export interface CreateProbeSchedulePayload {
  name: string;
  description?: string;
  target: string;
  protocol: string;
  frequency_minutes: number;
  probe_ids: string[];
  start_at?: string | null;
  end_at?: string | null;
  timeout_seconds?: number;
  expected_status_codes?: number[];
  alert_threshold?: number;
  alert_contacts?: string[];
}

export type UpdateProbeSchedulePayload = Partial<CreateProbeSchedulePayload>;

export async function listProbeSchedules(filters: ProbeScheduleFilters = {}) {
  const { data } = await apiClient.get<ProbeScheduleRecord[]>('/probes/schedules/', {
    params: filters
  });
  return data;
}

export async function createProbeSchedule(payload: CreateProbeSchedulePayload) {
  const { data } = await apiClient.post<ProbeScheduleRecord>('/probes/schedules/', payload);
  return data;
}

export async function updateProbeSchedule(id: string, payload: UpdateProbeSchedulePayload) {
  const { data } = await apiClient.patch<ProbeScheduleRecord>(`/probes/schedules/${id}/`, payload);
  return data;
}

export async function pauseProbeSchedule(id: string, reason?: string) {
  const { data } = await apiClient.post<ProbeScheduleRecord>(`/probes/schedules/${id}/pause/`, { reason });
  return data;
}

export async function resumeProbeSchedule(id: string) {
  const { data } = await apiClient.post<ProbeScheduleRecord>(`/probes/schedules/${id}/resume/`);
  return data;
}

export async function archiveProbeSchedule(id: string, reason?: string) {
  const { data } = await apiClient.post<ProbeScheduleRecord>(`/probes/schedules/${id}/archive/`, { reason });
  return data;
}

export async function deleteProbeSchedule(id: string) {
  await apiClient.delete(`/probes/schedules/${id}/`);
}
