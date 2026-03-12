import apiClient from './apiClient';

export async function fetchAssets() {
  const { data } = await apiClient.get('/assets/records');
  return data as any[];
}

export interface AssetRecordQueryResponse<T = any> {
  items: T[];
  pagination: { limit: number; offset: number; total: number };
  facets?: Record<string, string[]>;
}

export interface QueryAssetsParams {
  source?: string | string[];
  asset_type?: string | string[];
  keyword?: string;
  proxy?: string;
  interface_available?: string;
  app_status?: string;
  online_status?: string;
  network_type?: string;
  order?: 'synced_at' | 'name' | 'external_id' | 'system_name';
  direction?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
  include_facets?: boolean;
}

export async function queryAssets(params: QueryAssetsParams) {
  const { data } = await apiClient.get<AssetRecordQueryResponse>('/assets/records/query', { params });
  return data;
}

export interface AssetCreatePayload {
  source?: string;
  external_id?: string;
  name: string;
  system_name?: string;
  owners?: string[];
  contacts?: string[];
  metadata?: Record<string, unknown>;
}

export async function createAsset(payload: AssetCreatePayload) {
  const { data } = await apiClient.post('/assets/records', payload);
  return data;
}

export async function updateAsset(recordId: string, payload: Partial<AssetCreatePayload> & { metadata?: Record<string, unknown> }) {
  const { data } = await apiClient.patch(`/assets/records/${recordId}`, payload);
  return data;
}

export async function importAssets(records: AssetCreatePayload[]) {
  const { data } = await apiClient.post('/assets/import', { records }, { timeout: 120000 });
  return data as {
    created: number;
    failed: number;
    errors: Array<{ index: number; errors: Record<string, unknown> }>;
  };
}

export interface AssetSyncPayload {
  source?: string;
  sources?: string[];
  mode?: 'sync' | 'async';
}

export async function triggerAssetSync(payload?: AssetSyncPayload) {
  const { data } = await apiClient.post('/assets/sync', payload || {});
  return data;
}
