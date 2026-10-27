export type DetectionKind = 'http' | 'certificate' | 'cmdb';

export type ProbeRegistrationInput = {
  name: string;
  region: string;
  networkType: string;
  ipAddress?: string;
  capabilities: string[];
};

export type DetectionInput = {
  kind: DetectionKind;
  target: string;
  protocol?: string;
  probes?: string[];
  port?: number;
  timeoutSeconds?: number;
  followRedirects?: boolean;
};

const hostnamePattern = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/;
const ipv4Pattern = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/;

export function extractTargetHost(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return '';
  try {
    const parsed = trimmed.includes('://') ? new URL(trimmed) : new URL(`https://${trimmed}`);
    return parsed.hostname;
  } catch {
    return trimmed.replace(/^[a-z]+:\/\//i, '').replace(/[/:?#].*$/, '');
  }
}

export function isValidDetectionTarget(value: string) {
  const host = extractTargetHost(value);
  return hostnamePattern.test(host) || ipv4Pattern.test(host);
}

export function normalizeProbeCapabilities(values: string[]) {
  return Array.from(new Set(values.map((value) => value.trim().toUpperCase()).filter(Boolean))).sort();
}

export function validateProbeRegistration(input: ProbeRegistrationInput) {
  const errors: string[] = [];
  if (!input.name.trim()) errors.push('探针名称必填');
  if (!input.region.trim()) errors.push('区域必填');
  if (!input.networkType.trim()) errors.push('网络类型必填');
  if (!normalizeProbeCapabilities(input.capabilities).length) errors.push('至少选择一种探针能力');
  if (input.ipAddress?.trim() && !ipv4Pattern.test(input.ipAddress.trim())) errors.push('IP 地址格式不合法');
  return errors;
}

export function validateDetectionInput(input: DetectionInput) {
  const errors: string[] = [];
  if (!input.target.trim()) errors.push('检测目标必填');
  if (input.target.trim() && !isValidDetectionTarget(input.target)) errors.push('请输入合法域名或 IPv4 地址');
  if (input.kind !== 'cmdb' && !input.probes?.length) errors.push('请至少选择一个探针节点');
  if (input.kind !== 'cmdb' && (!input.timeoutSeconds || input.timeoutSeconds < 1 || input.timeoutSeconds > 60)) errors.push('超时时间需在 1-60 秒之间');
  if (input.kind === 'certificate' && (!input.port || input.port < 1 || input.port > 65535)) errors.push('证书端口需在 1-65535 之间');
  if (input.kind === 'http' && input.protocol === 'Telnet' && (!input.port || input.port < 1 || input.port > 65535)) errors.push('Telnet 端口需在 1-65535 之间');
  return errors;
}

export function buildDetectionRequest(input: DetectionInput & { probe?: string }) {
  const host = extractTargetHost(input.target);
  return {
    type: input.kind,
    protocol: input.protocol ?? (input.kind === 'certificate' ? 'CERTIFICATE' : input.kind === 'cmdb' ? 'CMDB' : 'HTTPS'),
    target: input.target.trim(),
    related_asset: host || input.target.trim(),
    probe: input.probe,
    port: input.port,
    timeout_seconds: input.timeoutSeconds,
    metadata: {
      follow_redirects: Boolean(input.followRedirects),
      selected_probe: input.probe
    }
  };
}

export function presentDetectionStatus(status: string) {
  if (status === 'success') return '成功';
  if (status === 'failed') return '失败';
  if (status === 'running') return '检测中';
  if (status === 'pending' || status === 'scheduled') return '待执行';
  return status || '-';
}
