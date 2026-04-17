// 检测页面通用工具函数和类型定义

// 通用类型定义
export interface DetectionResultViewModel {
  id: string;
  target: string;
  protocol: string;
  status: string;
  response_time_ms?: number | null;
  status_code?: number | null;
  error_message?: string | null;
  result_payload?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
  executed_at?: string | null;
  created_at?: string | null;
}

export interface DetectionLogItem {
  id: string;
  target: string;
  protocol: string;
  nodes: string[];
  status: string;
  response_time_ms: number | null;
  executed_at: string;
  status_code?: number | null;
  error_message?: string | null;
  metadata?: Record<string, unknown> | null;
  result_payload?: Record<string, unknown> | null;
}

export interface BaseDetectionLog {
  id: string;
  status: string;
  [key: string]: unknown;
}

export interface DetectionConfig {
  timeout_seconds?: number;
  expect_status?: number | string;
  [key: string]: unknown;
}

export const validateUrl = (target: string): { valid: boolean; message?: string } => {
  const trimmedTarget = target.trim();
  if (!trimmedTarget) {
    return { valid: false, message: '请输入目标地址' };
  }
  if (!/^https?:\/\//i.test(trimmedTarget)) {
    return { valid: false, message: '请在域名前包含 http:// 或 https://' };
  }
  try {
    const parsed = new URL(trimmedTarget);
    if (!parsed.hostname) {
      return { valid: false, message: '请输入有效的 URL' };
    }
  } catch {
    return { valid: false, message: '请输入有效的 URL' };
  }
  return { valid: true };
};

export const validateDomain = (target: string): { valid: boolean; message?: string } => {
  const trimmedTarget = target.trim();
  if (!trimmedTarget) {
    return { valid: false, message: '请输入目标地址' };
  }
  const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/;
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  if (!domainRegex.test(trimmedTarget) && !ipRegex.test(trimmedTarget)) {
    return { valid: false, message: '请输入有效的域名或 IP 地址' };
  }
  return { valid: true };
};

export interface CertificateInfo {
  status?: string;
  days_until_expiry?: number | null;
  issuer?: string | null;
  subject?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
}

export interface CmdbRecord {
  domain?: string;
  system?: string;
  internet_type?: string;
  owner?: string;
  contacts?: string;
  [key: string]: unknown;
}

// 协议选项配置
export const PROTOCOL_OPTIONS = {
  HTTPS: {
    label: 'HTTP(S)',
    value: 'HTTPS',
    placeholder: '请输入包含 http:// 或 https:// 的完整域名',
    validation: (target: string) => {
      if (!/^https?:\/\//i.test(target)) {
        return '请在域名前包含 http:// 或 https://';
      }
      return null;
    }
  },
  WSS: {
    label: 'WebSocket',
    value: 'WSS',
    placeholder: '请输入 wss://your-domain.com',
    validation: (target: string) => {
      if (!/^wss?:\/\//i.test(target)) {
        return '请输入正确的 WebSocket 地址';
      }
      return null;
    }
  },
  Telnet: {
    label: 'Telnet',
    value: 'Telnet',
    placeholder: '请输入域名或IP地址',
    validation: (target: string) => {
      return validateDomain(target).message ?? null;
    }
  },
  CERTIFICATE: {
    label: '证书检测',
    value: 'CERTIFICATE',
    placeholder: '请输入 https://your-domain.com',
    validation: (target: string) => {
      if (!/^https?:\/\//i.test(target)) {
        return '请包含 http:// 或 https://';
      }
      return null;
    }
  }
};

// 状态相关工具函数
export const getStatusTagType = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'succeeded':
    case 'success':
    case 'ok':
      return 'success';
    case 'timeout':
    case 'expires_soon':
    case 'unknown':
      return 'warning';
    case 'failed':
    case 'error':
    case 'expired':
      return 'danger';
    case 'not_found':
      return 'warning';
    default:
      return 'info';
  }
};

export const getStatusText = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'succeeded':
    case 'success':
      return '成功';
    case 'scheduled':
      return '已提交';
    case 'running':
      return '检测中';
    case 'failed':
    case 'error':
      return '失败';
    case 'timeout':
      return '超时';
    case 'unknown':
      return '状态未知';
    case 'pending':
      return '未查询';
    case 'ok':
      return '已收录';
    case 'not_found':
      return '未收录';
    case 'expired':
      return '已过期';
    case 'expires_soon':
      return '即将过期';
    case 'valid':
      return '有效';
    default:
      return status;
  }
};

// 日期格式化
function pad2(value: number) {
  return String(value).padStart(2, '0');
}

export const formatDate = (value?: string | null): string => {
  if (!value) return '-';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  const year = date.getFullYear();
  const month = pad2(date.getMonth() + 1);
  const day = pad2(date.getDate());
  const hour = pad2(date.getHours());
  const minute = pad2(date.getMinutes());
  const second = pad2(date.getSeconds());
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
};

export const formatAbsoluteDate = formatDate;

// 协议标签显示
export const getProtocolLabel = (protocol: string): string => {
  const option = Object.values(PROTOCOL_OPTIONS).find(opt => opt.value === protocol);
  return option?.label || protocol;
};

// 证书相关工具函数
export const extractCertificateInfo = (source: DetectionLogItem | null | undefined): CertificateInfo | null => {
  if (!source) return null;
  const payload = (source.result_payload ?? source.metadata ?? {}) as Record<string, any>;
  return payload?.certificate ?? payload?.certificate_report ?? null;
};

export const getCertificateDaysText = (info: CertificateInfo | null): string => {
  if (!info || typeof info.days_until_expiry !== 'number') {
    return '-';
  }

  const days = info.days_until_expiry;
  if (days < 0) {
    return `已过期 ${Math.abs(days)} 天`;
  } else if (days === 0) {
    return '今天过期';
  } else if (days === 1) {
    return '明天过期';
  } else {
    return `${days} 天后过期`;
  }
};

export const getCertificateStatusTag = (status?: string): string => {
  switch (status) {
    case 'valid':
      return 'success';
    case 'expires_soon':
      return 'warning';
    case 'expired':
      return 'danger';
    default:
      return 'info';
  }
};

// 输入验证
export const validateTarget = (target: string, protocol: string): string | null => {
  const trimmedTarget = target.trim();

  if (!trimmedTarget) {
    return '请输入目标地址';
  }

  const protocolConfig = PROTOCOL_OPTIONS[protocol as keyof typeof PROTOCOL_OPTIONS];
  if (protocolConfig?.validation) {
    return protocolConfig.validation(trimmedTarget);
  }

  return null;
};

// 配置项转换
export const formatConfigEntries = (config: Record<string, unknown> | null | undefined): Array<{ key: string; label: string; value: string }> => {
  if (!config) return [];

  const labelMap: Record<string, string> = {
    timeout_seconds: '超时时间 (秒)',
    follow_redirects: '允许重定向',
    port: '端口',
    warning_threshold_days: '预警天数',
    mode: '检测模式'
  };

  return Object.entries(config).map(([key, value]) => ({
    key,
    label: labelMap[key] || key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }));
};

// CMDB 字段标签映射
export const CMDB_FIELD_LABELS: Record<string, string> = {
  domain: '域名',
  system: '所属系统',
  internet_type: '互联网类型',
  owner: '负责人',
  contacts: '告警联系人',
  created_at: '创建时间',
  updated_at: '更新时间',
  status: '状态',
  description: '描述',
  tags: '标签'
};

// 响应时间格式化
export const formatResponseTime = (ms: number | null | undefined): string => {
  if (typeof ms !== 'number') return '-';

  if (ms < 1000) {
    return `${ms} ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)} s`;
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  }
};

// 错误消息处理
export const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return '操作失败，请稍后再试';
};

// 节点名称显示
export const formatNodeNames = (nodes: string[]): string => {
  if (!nodes.length) return '-';
  if (nodes.length === 1) return nodes[0];
  return `${nodes[0]} 等 ${nodes.length} 个节点`;
};

// 批量操作结果处理
export const processBatchResults = <T>(results: PromiseSettledResult<T>[]): {
  successCount: number;
  failedCount: number;
  successResults: T[];
  errors: string[];
} => {
  let successCount = 0;
  let failedCount = 0;
  const successResults: T[] = [];
  const errors: string[] = [];

  results.forEach((result) => {
    if (result.status === 'fulfilled') {
      successCount++;
      successResults.push(result.value);
    } else {
      failedCount++;
      errors.push(getErrorMessage(result.reason));
    }
  });

  return { successCount, failedCount, successResults, errors };
};

// 默认配置
export const DEFAULT_CONFIGS = {
  HTTP: {
    mode: 'http' as const,
    timeout_seconds: 10,
    follow_redirects: true
  },
  WSS: {
    mode: 'http' as const,
    timeout_seconds: 10,
    follow_redirects: false
  },
  Telnet: {
    mode: 'tcp' as const,
    timeout_seconds: 10,
    port: 80
  },
  Certificate: {
    timeout_seconds: 15,
    warning_threshold_days: 14
  }
};

// 深拷贝配置
export const cloneConfig = <T>(config: T): T => {
  return JSON.parse(JSON.stringify(config));
};
