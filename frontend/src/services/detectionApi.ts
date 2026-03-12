import apiClient from './apiClient';

export interface DetectionRequestPayload {
  target: string;
  protocol: string;
  probe_id?: string | null;
  timeout_seconds?: number;
  metadata?: Record<string, unknown>;
}

export async function requestOneOffDetection(payload: DetectionRequestPayload) {
  const { data } = await apiClient.post('/detection/one-off', payload);
  return data;
}

export async function fetchDetectionTask(id: string) {
  const { data } = await apiClient.get(`/detection/tasks/${id}`);
  return data;
}

export async function validateDomainWithCMDB(domain: string) {
  const { data } = await apiClient.get('/detection/cmdb/validate', {
    params: { domain }
  });
  return data as {
    status: 'ok' | 'not_found' | 'error';
    message?: string;
    record?: Record<string, unknown> | null;
  };
}
