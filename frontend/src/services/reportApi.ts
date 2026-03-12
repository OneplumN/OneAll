import apiClient from './apiClient';

export async function fetchDetectionReport(days = 30) {
  const { data } = await apiClient.get('/analytics/reports/detection', { params: { days } });
  return data as any;
}
