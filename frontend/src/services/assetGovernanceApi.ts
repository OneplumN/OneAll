import apiClient from './apiClient';

export interface AssetGovernanceOverview {
  generated_at: string;
  summary: {
    ipmp_total: number;
    zabbix_host_total: number;
    workorder_host_total: number;
  };
  ledger_coverage: {
    total: number;
    covered: number;
    uncovered: number;
    covered_rate: number;
    uncovered_items: Array<{
      display_name: string;
      match_key: string;
      app_code: string;
      app_status?: string;
      owner?: string;
      security_level?: string;
      system_origin?: string;
    }>;
  };
  workorder_coverage?: AssetGovernanceOverview['ledger_coverage'];
  ipmp_coverage: {
    total: number;
    monitored: number;
    uncovered: number;
    monitored_rate: number;
    uncovered_items: Array<{
      display_name: string;
      match_key: string;
      app_code: string;
      app_status?: string;
      owner?: string;
      security_level?: string;
      system_origin?: string;
    }>;
  };
  zabbix_coverage: AssetGovernanceOverview['ipmp_coverage'];
  coverage_matrix: {
    counts: {
      both: number;
      ledger_only: number;
      zabbix_only: number;
      neither: number;
    };
    items: {
      ledger_only: Array<{ display_name: string; app_code: string; app_status?: string; owner?: string }>;
      zabbix_only: Array<{ display_name: string; app_code: string; app_status?: string; owner?: string }>;
      neither: Array<{ display_name: string; app_code: string; app_status?: string; owner?: string }>;
    };
  };
  ip_reconcile: {
    workorder_total: number;
    zabbix_total: number;
    matched_by_ip: number;
    missing_in_zabbix: number;
    extra_in_zabbix: number;
    workorder_ip_conflicts: number;
    zabbix_ip_conflicts: number;
    missing_in_zabbix_items: Array<{
      ip: string;
      hostname?: string;
      system_name?: string;
      owner?: string;
    }>;
    extra_in_zabbix_items: Array<{
      ip: string;
      hosts: Array<{
        host_name?: string;
        visible_name?: string;
        proxy?: string;
        availability?: string;
      }>;
    }>;
    zabbix_ip_conflict_items: Array<{
      ip: string;
      hosts: Array<{
        host_name?: string;
        visible_name?: string;
        proxy?: string;
      }>;
    }>;
  };
  proxy_stats: Array<{
    proxy: string;
    total: number;
    available: number;
    unavailable: number;
    unknown: number;
  }>;
}

export async function fetchAssetGovernanceOverview(params?: { limit?: number }) {
  const { data } = await apiClient.get<AssetGovernanceOverview>('/analytics/assets/overview', { params });
  return data;
}

export interface AssetProxyHostsResponse {
  generated_at: string;
  proxy: string;
  summary: {
    host_total: number;
    abnormal_host_total: number;
    ip_total: number;
    conflict_ip_total: number;
    no_ip_total: number;
  };
  pagination: { limit: number; offset: number; total: number };
  items: Array<{
    ip: string;
    host_count: number;
    abnormal_count: number;
    hosts: Array<{
      external_id?: string;
      host_name?: string;
      visible_name?: string;
      availability?: string;
      proxy?: string;
      groups?: string[];
      is_abnormal?: boolean;
    }>;
  }>;
}

export async function fetchAssetProxyHosts(params: {
  proxy: string;
  limit?: number;
  offset?: number;
  keyword?: string;
  only_abnormal?: boolean;
}) {
  const query = {
    proxy: params.proxy,
    limit: params.limit,
    offset: params.offset,
    keyword: params.keyword,
    only_abnormal: params.only_abnormal ? 1 : 0
  };
  const { data } = await apiClient.get<AssetProxyHostsResponse>('/analytics/assets/proxy-hosts', { params: query });
  return data;
}
