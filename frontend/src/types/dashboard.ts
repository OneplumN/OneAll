export interface DashboardOverviewMetrics {
  generated_at: string;
  probes: {
    active: number;
    offline: number;
  };
  detection: {
    pending_jobs: number;
    last_24h_runs: number;
  };
  incidents: {
    open: number;
    acknowledged: number;
  };
}

export interface DashboardAlertBreakdown {
  level: 'critical' | 'warning' | 'info';
  count: number;
}

export interface DashboardAlertItem {
  id: string;
  target: string;
  status: string;
  severity: 'critical' | 'warning' | 'info';
  occurred_at: string;
  probe?: string | null;
  message?: string | null;
}

export interface DashboardAlertSummary {
  generated_at: string;
  total_alerts: number;
  breakdown: DashboardAlertBreakdown[];
  items: DashboardAlertItem[];
}

export interface DashboardTodoItem {
  id: string;
  label: string;
  created_at: string;
  link?: string | null;
  metadata?: Record<string, string> | null;
}

export type DashboardTodoBucketType = 'monitoring_request' | 'probe_health' | 'plugin';

export interface DashboardTodoBucket {
  id: string;
  title: string;
  description: string;
  type: DashboardTodoBucketType;
  total: number;
  items: DashboardTodoItem[];
}

export interface DashboardTodoSummary {
  generated_at: string;
  items: DashboardTodoBucket[];
}

export interface DetectionTaskStatus {
  id: string;
  domain: string;
  system_name?: string;
  task_name?: string;
  expected_status?: number | number[] | null;
  actual_status?: number | null;
  response_ms?: number | null;
  probe?: string | null;
  checked_at?: string | null;
  status_message?: string | null;
}

export type CertificateAlertSeverity = 'critical' | 'warning' | 'info';

export interface CertificateAlertItem {
  id: string;
  domain: string;
  issuer?: string | null;
  days_remaining?: number | null;
  severity: CertificateAlertSeverity;
  probe?: string | null;
  checked_at?: string | null;
  message?: string | null;
}

export interface CertificateAlertSummary {
  generated_at: string;
  items: CertificateAlertItem[];
}
