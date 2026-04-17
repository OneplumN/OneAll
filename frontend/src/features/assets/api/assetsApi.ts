import apiClient from '@/app/api/apiClient';

// 与后端 AssetRecordSerializer 对应的基础结构
export interface AssetRecord {
  id: string;
  source: string;
  external_id: string;
  name: string;
  created_at?: string | null;
  updated_at?: string | null;
  system_name?: string | null;
  owners?: any[];
  contacts?: any[];
  metadata?: Record<string, any> | null;
  synced_at?: string | null;
  sync_status?: string;
  is_removed?: boolean;
  removed_at?: string | null;
  last_seen_at?: string | null;
}

// 创建/导入资产时使用的负载结构（兼容 AssetRecordCreateSerializer）
export interface AssetCreatePayload {
  source?: string;
  external_id?: string;
  name: string;
  system_name?: string;
  owners?: any[];
  contacts?: any[];
  metadata?: Record<string, any>;
  sync_status?: string;
}

export interface QueryAssetsParams {
  source?: string;
  asset_type?: string | string[];
  keyword?: string;
  proxy?: string;
  interface_available?: string;
  app_status?: string;
  online_status?: string;
  network_type?: string;
  limit?: number;
  offset?: number;
  include_facets?: boolean;
  order?: string;
  direction?: 'asc' | 'desc' | string;
}

export interface QueryAssetsResponse {
  items: AssetRecord[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
  };
  facets?: Record<string, string[]>;
}

export interface ImportAssetsResponse {
  created: number;
  failed: number;
  errors?: Array<{ index: number; errors: Record<string, unknown> }>;
  detail?: string;
}

export interface TriggerAssetSyncPayload {
  mode?: 'async' | 'sync' | string;
  sources?: string | string[];
}

export interface TriggerAssetSyncResponse {
  detail: string;
  run_id: string;
}

export interface AssetSyncRun {
  run_id: string;
  mode: string;
  status: string;
  source_filters: string[];
  started_at?: string | null;
  finished_at?: string | null;
  summary?: Record<string, any> | null;
  error_message?: string;
  created_at: string;
}

export interface AssetSyncRunListResponse {
  total: number;
  items: AssetSyncRun[];
}

export interface AssetTypeSummary {
  key: string;
  label: string;
  category: string;
  default_source: string;
  unique_fields: string[];
  default_unique_fields?: string[];
  // 后端资产类型定义中声明的业务字段集合，用于前端配置唯一键等场景
  fields?: string[];
  // 系统设置中为该资产类型配置的扩展字段定义
  extra_fields?: Array<{
    key: string;
    label: string;
    type?: string;
    options?: string[];
    required?: boolean;
    list_visible?: boolean;
  }>;
}

// 后端 AssetModelSerializer 对应的结构：可配置资产模型 + 绑定脚本
export interface AssetModel {
  id: string;
  key: string;
  label: string;
  category: string;
  fields: Array<{
    key: string;
    label: string;
    type?: string;
  }>;
  unique_key: string[];
  script_id?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** 分页查询资产列表（资产中心使用） */
export async function queryAssets(params: QueryAssetsParams) {
  const { data } = await apiClient.get<QueryAssetsResponse>('/assets/records/query', {
    params
  });
  return data;
}

/** 触发资产同步任务（异步或同步执行） */
export async function triggerAssetSync(payload: TriggerAssetSyncPayload) {
  const { data } = await apiClient.post<TriggerAssetSyncResponse>('/assets/sync', payload);
  return data;
}

/** 查询资产同步历史（最近同步记录） */
export async function fetchAssetSyncRuns(params: { limit?: number; offset?: number; status?: string; mode?: string }) {
  const { data } = await apiClient.get<AssetSyncRunListResponse>('/assets/sync/runs', { params });
  return data;
}

/** 查询可配置资产模型列表（用于资产模型管理） */
export async function fetchAssetModels() {
  const { data } = await apiClient.get<AssetModel[]>('/assets/models');
  return data;
}

/** 创建单条资产记录（主要用于手工录入） */
export async function createAsset(payload: AssetCreatePayload) {
  const { data } = await apiClient.post<AssetRecord>('/assets/records', payload);
  return data;
}

/** 更新资产记录，目前后端仅允许编辑工单纳管主机信息 */
export async function updateAsset(recordId: string, payload: Partial<AssetCreatePayload>) {
  const { data } = await apiClient.patch<AssetRecord>(`/assets/records/${recordId}`, payload);
  return data;
}

/** 批量导入资产 */
export async function importAssets(records: AssetCreatePayload[]) {
  const { data } = await apiClient.post<ImportAssetsResponse>('/assets/import', { records });
  return data;
}

/** 查询资产类型定义（用于前端显示和唯一键提示） */
export async function fetchAssetTypes() {
  const { data } = await apiClient.get<AssetTypeSummary[]>('/assets/types');
  return data;
}

export async function updateAssetTypeSettings(
  typeKey: string,
  payload: {
    unique_fields?: string[];
    extra_fields?: NonNullable<AssetTypeSummary['extra_fields']>;
  }
) {
  const { data } = await apiClient.patch<AssetTypeSummary>(`/assets/types/${typeKey}`, payload);
  return data;
}

/** 创建资产模型（配置化模型定义） */
export async function createAssetModel(payload: {
  key: string;
  label: string;
  category?: string;
  fields: AssetModel['fields'];
  unique_key: string[];
  is_active?: boolean;
}) {
  const body = {
    ...payload,
    category: payload.category ?? '',
    is_active: payload.is_active ?? true
  };
  const { data } = await apiClient.post<AssetModel>('/assets/models', body);
  return data;
}

/** 更新资产模型（不包含脚本上传） */
export async function updateAssetModel(
  modelId: string,
  payload: {
    key: string;
    label: string;
    category?: string;
    fields: AssetModel['fields'];
    unique_key: string[];
    is_active?: boolean;
  }
) {
  const body = {
    ...payload,
    category: payload.category ?? '',
    is_active: payload.is_active ?? true
  };
  const { data } = await apiClient.put<AssetModel>(`/assets/models/${modelId}`, body);
  return data;
}

/** 上传或替换资产模型的同步脚本 */
export async function uploadAssetModelScript(modelId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post<AssetModel>(`/assets/models/${modelId}/script`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return data;
}

/** 下载资产模型的同步脚本模板（返回 Blob，由调用方负责触发浏览器下载） */
export async function downloadAssetModelScriptTemplate(modelId: string) {
  const response = await apiClient.get(`/assets/models/${modelId}/script/template`, {
    responseType: 'blob'
  });
  return response.data as Blob;
}

/** 下载当前绑定的同步脚本（返回 Blob，由调用方负责触发浏览器下载） */
export async function downloadAssetModelScript(modelId: string) {
  const response = await apiClient.get(`/assets/models/${modelId}/script/current`, {
    responseType: 'blob'
  });
  return response.data as Blob;
}

/** 触发某个资产模型的同步脚本执行 */
export async function syncAssetModel(modelId: string) {
  const { data } = await apiClient.post<{
    detail: string;
    run_id: string;
    model_key: string;
    summary: {
      trigger_type: string;
      model_id: string;
      model_key: string;
      script_id: string;
      totals: { fetched: number; created: number; updated: number; restored?: number; removed: number };
    };
  }>(`/assets/models/${modelId}/sync`, {});
  return data;
}
