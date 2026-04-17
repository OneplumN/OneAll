import apiClient from '@/app/api/apiClient';

export interface AlertEventRecord {
  id: string;
  source: string;
  event_type: string;
  severity: string;
  title: string;
  message: string;
  status: string;
  created_at: string;
  sent_at: string | null;
  context?: Record<string, unknown>;
}

export interface AlertEventQuery {
  source?: string;
  severity?: string;
  limit?: number;
}

export async function fetchAlertEvents(params?: AlertEventQuery) {
  const { data } = await apiClient.get<AlertEventRecord[]>('/alerts/events', {
    params,
  });
  return data;
}

export interface AlertCheckSummary {
  id: string;
  name: string;
  target: string;
  protocol: string;
  source_type: string;
  source_id: string | null;
  executor_type: string;
  executor_ref?: string | null;
  schedule_count: number;
  is_active?: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AlertCheckProbeOption {
  id: string;
  name: string;
  location: string;
  network_type: string;
  status: string;
}

export interface AlertCheckQuery {
  source_type?: string;
  executor_type?: string;
}

export interface AlertScheduleLastExecution {
  id: string;
  status: string;
  scheduled_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  response_time_ms: number | null;
  status_code: string;
  error_message: string;
}

export interface AlertScheduleRecord {
  id: string;
  frequency_minutes: number;
  status: string;
  start_at: string | null;
  end_at: string | null;
  last_run_at: string | null;
  next_run_at: string | null;
  metadata: Record<string, unknown>;
  last_execution: AlertScheduleLastExecution | null;
}

export interface AlertCheckDetail {
  check: AlertCheckSummary & {
    probe_ids?: string[];
    probes?: AlertCheckProbeOption[];
  };
  schedules: AlertScheduleRecord[];
}

export interface AlertCheckFormPayload {
  name: string;
  description?: string;
  target: string;
  protocol: string;
  frequency_minutes: number;
  probe_ids: string[];
  timeout_seconds?: number;
  expected_status_codes?: number[];
  alert_threshold?: number;
  alert_contacts?: string[];
  alert_channels?: string[];
  cert_check_enabled?: boolean;
  cert_warning_days?: number;
}

export type MonitoringOverviewStatus = 'success' | 'danger' | 'idle';

export interface MonitoringOverviewSystem {
  system_name: string;
  status: MonitoringOverviewStatus;
  domain_count: number;
  abnormal_count: number;
  last_checked_at: string | null;
  matched_strategy_count: number;
}

export interface MonitoringOverviewItem {
  system_name: string;
  resolved_domain: string;
  target: string;
  check_id: string;
  check_name: string;
  protocol: string;
  latest_status: MonitoringOverviewStatus;
  status_code: string;
  response_time_ms: number | null;
  last_checked_at: string | null;
  latest_error: string;
  asset_match_status: string;
}

export interface MonitoringOverviewPayload {
  generated_at: string;
  data_updated_at: string | null;
  systems: MonitoringOverviewSystem[];
  items: MonitoringOverviewItem[];
}

export async function fetchAlertChecks(params?: AlertCheckQuery) {
  const { data } = await apiClient.get<AlertCheckSummary[]>('/alerts/checks', {
    params,
  });
  return data;
}

export async function updateAlertCheck(
  id: string,
  payload: Partial<Pick<AlertCheckSummary, 'is_active'>>,
) {
  const { data } = await apiClient.patch<AlertCheckSummary>(
    `/alerts/checks/${id}`,
    payload,
  );
  return data;
}

export async function createAlertCheck(payload: AlertCheckFormPayload) {
  const { data } = await apiClient.post<AlertCheckSummary>('/alerts/checks', payload);
  return data;
}

export async function updateAlertCheckDetail(
  id: string,
  payload: Partial<AlertCheckFormPayload>,
) {
  const { data } = await apiClient.patch<AlertCheckSummary>(`/alerts/checks/${id}`, payload);
  return data;
}

export async function deleteAlertCheck(id: string) {
  await apiClient.delete(`/alerts/checks/${id}`);
}

export async function fetchAlertCheckSchedules(checkId: string) {
  const { data } = await apiClient.get<AlertCheckDetail>(
    `/alerts/checks/${checkId}/schedules`,
  );
  return data;
}

export async function fetchMonitoringOverview(): Promise<MonitoringOverviewPayload> {
  const { data } = await apiClient.get<MonitoringOverviewPayload>(
    '/alerts/checks/system-overview',
  );
  return data;
}
