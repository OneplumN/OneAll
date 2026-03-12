import apiClient from './apiClient';

export interface ProbeAlertRecord {
  id: string;
  execution_id: string | null;
  schedule_id: string | null;
  schedule_name: string;
  probe_id: string | null;
  probe_name: string;
  status: string;
  severity: string;
  threshold: number;
  alert_contacts: string[];
  occurred_at: string;
  message: string;
}

export interface ProbeAlertResponse {
  items: ProbeAlertRecord[];
}

export const fetchRecentProbeAlerts = async (limit = 10) => {
  const { data } = await apiClient.get<ProbeAlertResponse>('/probes/alerts/recent/', {
    params: { limit },
  });
  return data.items;
};
