import apiClient from './apiClient';
import type { ProbeScheduleRecord, ProbeNodeSummary } from './probeScheduleApi';

export interface ProbeScheduleSummary
  extends Pick<
    ProbeScheduleRecord,
    'id' | 'name' | 'target' | 'protocol' | 'frequency_minutes' | 'status' | 'status_display' | 'source_type' | 'source_display'
  > {}

export interface ProbeScheduleExecutionRecord {
  id: string;
  schedule_id: string;
  schedule?: ProbeScheduleSummary;
  probe?: ProbeNodeSummary | null;
  scheduled_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  status: string;
  response_time_ms?: number | null;
  status_code?: string | null;
  message?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ProbeScheduleExecutionAggregates {
  total_count: number;
  status_counts: Record<string, number>;
  average_response_time_ms: number | null;
  success_rate: number | null;
}

export interface ProbeScheduleExecutionPagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface ProbeScheduleExecutionFilters {
  schedule_id?: string;
  probe_id?: string;
  status?: string;
  target?: string;
  protocol?: string;
  started_after?: string;
  started_before?: string;
  page?: number;
  page_size?: number;
}

export interface ProbeScheduleExecutionListResponse {
  items: ProbeScheduleExecutionRecord[];
  aggregates: ProbeScheduleExecutionAggregates;
  pagination: ProbeScheduleExecutionPagination;
}

export async function fetchProbeScheduleExecutions(filters: ProbeScheduleExecutionFilters) {
  const { data } = await apiClient.get<ProbeScheduleExecutionListResponse>('/probes/schedule-executions/', {
    params: filters
  });
  return data;
}

export async function fetchScheduleExecutionsBySchedule(
  scheduleId: string,
  params: { status?: string; page?: number; page_size?: number } = {}
) {
  const { data } = await apiClient.get<ProbeScheduleExecutionListResponse>(`/probes/schedules/${scheduleId}/executions/`, {
    params
  });
  return data;
}
