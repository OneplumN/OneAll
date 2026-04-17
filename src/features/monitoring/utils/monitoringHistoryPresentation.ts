import dayjs from 'dayjs';

export const monitoringHistoryStatusOptions = [
  { value: 'scheduled', label: '待执行' },
  { value: 'running', label: '执行中' },
  { value: 'succeeded', label: '成功' },
  { value: 'failed', label: '失败' },
  { value: 'missed', label: '错过执行' }
];

export const monitoringHistoryProtocolOptions = [
  { value: 'HTTP', label: 'HTTP' },
  { value: 'HTTPS', label: 'HTTPS' },
  { value: 'Telnet', label: 'Telnet' },
  { value: 'WSS', label: 'WebSocket Secure' },
  { value: 'TCP', label: 'TCP' },
  { value: 'CERTIFICATE', label: '证书检测' }
];

export function translateExecutionStatus(status: string) {
  switch (status) {
    case 'succeeded':
    case 'SUCCEEDED':
      return '成功';
    case 'failed':
    case 'FAILED':
      return '失败';
    case 'timeout':
    case 'TIMEOUT':
      return '超时';
    case 'missed':
    case 'MISSED':
      return '错过执行';
    case 'running':
    case 'RUNNING':
      return '执行中';
    case 'scheduled':
    case 'SCHEDULED':
      return '待执行';
    default:
      return status;
  }
}

export function executionStatusTagType(status: string) {
  if (status.toLowerCase() === 'succeeded') return 'success';
  if (status.toLowerCase() === 'failed') return 'danger';
  if (status.toLowerCase() === 'missed') return 'danger';
  if (status.toLowerCase() === 'timeout') return 'warning';
  if (status.toLowerCase() === 'running') return 'info';
  return 'info';
}

export function formatExecutionDate(value?: string | null) {
  if (!value) return '--';
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss');
}

export function summarizeExecutionMessage(value?: string | null) {
  if (!value) return '--';
  return value.replace(/\s+/g, ' ').trim();
}

export function createHistoryDateShortcuts() {
  return [
    {
      text: '最近 24 小时',
      value: () => {
        const end = dayjs();
        const start = end.subtract(1, 'day');
        return [
          start.format('YYYY-MM-DDTHH:mm:ss[Z]'),
          end.format('YYYY-MM-DDTHH:mm:ss[Z]')
        ];
      }
    },
    {
      text: '最近 7 天',
      value: () => {
        const end = dayjs();
        const start = end.subtract(7, 'day');
        return [
          start.format('YYYY-MM-DDTHH:mm:ss[Z]'),
          end.format('YYYY-MM-DDTHH:mm:ss[Z]')
        ];
      }
    }
  ];
}
