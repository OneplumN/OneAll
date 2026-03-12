import apiClient from './apiClient';

import type {
  DashboardAlertSummary,
  DashboardOverviewMetrics,
  DashboardTodoSummary,
  CertificateAlertSummary,
  DetectionTaskStatus
} from '@/types/dashboard';

export async function fetchDashboardOverview(): Promise<DashboardOverviewMetrics> {
  const { data } = await apiClient.get<DashboardOverviewMetrics>('/dashboard/overview/');
  return data;
}

export async function fetchDashboardAlerts(limit = 5): Promise<DashboardAlertSummary> {
  const { data } = await apiClient.get<DashboardAlertSummary>('/dashboard/alerts-summary/', {
    params: { limit }
  });
  return data;
}

export async function fetchDashboardTodos(limit = 5): Promise<DashboardTodoSummary> {
  const { data } = await apiClient.get<DashboardTodoSummary>('/dashboard/todos/', {
    params: { limit }
  });
  return data;
}

export async function fetchDetectionGrid(): Promise<DetectionTaskStatus[]> {
  const { data } = await apiClient.get<DetectionTaskStatus[]>('/dashboard/detection-grid/');
  return data;
}

export async function fetchCertificateAlerts(limit = 12): Promise<CertificateAlertSummary> {
  const { data } = await apiClient.get<CertificateAlertSummary>('/dashboard/certificate-alerts/', {
    params: { limit }
  });
  return data;
}
