import apiClient from './apiClient';

export interface ProxyMappingItem {
  id: string;
  proxy: string;
  display_name: string;
  remark?: string;
  is_active: boolean;
  updated_at: string;
}

export async function fetchProxyMappings() {
  const { data } = await apiClient.get<ProxyMappingItem[]>('/assets/proxy-mappings');
  return data;
}

export async function upsertProxyMappings(items: Array<{ proxy: string; display_name?: string; remark?: string; is_active?: boolean }>) {
  const { data } = await apiClient.put<{ changed: number; items: ProxyMappingItem[] }>('/assets/proxy-mappings', { items });
  return data;
}

