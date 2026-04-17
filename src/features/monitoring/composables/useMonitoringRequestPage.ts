import { computed, onMounted, reactive, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';

import apiClient from '@/app/api/apiClient';
import { useSessionStore } from '@/app/stores/session';
import {
  listMonitoringRequests,
  submitMonitoringRequest,
  updateMonitoringRequest,
  type MonitoringRequestPayload,
  type MonitoringRequestRecord,
} from '@/features/monitoring/api/monitoringApi';

export interface MonitoringRequestFormState {
  title: string;
  target: string;
  system_name: string;
  network_type: 'internal' | 'internet';
  owner_name: string;
  alert_contacts: string[];
  protocol: string;
  frequency_minutes: number;
  probe_ids: string[];
  alert_threshold: number;
}

export interface MonitoringProbeNode {
  id: string;
  name: string;
  network_type: string;
}

const DEFAULT_CERT_FREQUENCY = 1440;

export const monitoringFrequencyOptions = [
  { label: '1 分钟', value: 1 },
  { label: '3 分钟', value: 3 },
  { label: '5 分钟', value: 5 },
  { label: '15 分钟', value: 15 },
  { label: '30 分钟', value: 30 },
  { label: '1 天', value: 1440 }
];

export const monitoringProtocolOptions = [
  { label: 'HTTPS', value: 'HTTPS' },
  { label: 'HTTP', value: 'HTTP' },
  { label: 'WebSocket', value: 'WSS' },
  { label: 'Telnet', value: 'Telnet' },
  { label: '证书检测', value: 'CERTIFICATE' }
];

export function useMonitoringRequestPage() {
  const sessionStore = useSessionStore();

  const form = reactive<MonitoringRequestFormState>({
    title: '周期拨测申请',
    target: '',
    system_name: '',
    network_type: 'internet',
    owner_name: '',
    alert_contacts: [],
    protocol: 'HTTPS',
    frequency_minutes: 1,
    probe_ids: [],
    alert_threshold: 3
  });

  const alertContactsText = ref('');
  const editingRequestId = ref<string | null>(null);
  const editingRequestStatus = ref<'rejected' | 'approved' | null>(null);
  const submitting = ref(false);
  const error = ref<string | null>(null);
  const success = ref<string | null>(null);
  const headerRefreshing = ref(false);
  const requests = ref<MonitoringRequestRecord[]>([]);
  const probes = ref<MonitoringProbeNode[]>([]);
  const probesLoading = ref(false);
  const systemOptions = ref<string[]>([]);
  const systemsLoading = ref(false);
  const expectedStatusInput = ref('200');
  const isCertificateProtocol = ref(false);

  const canSubmit = computed(() => {
    if (editingRequestId.value) return true;
    return sessionStore.hasPermission('detection.schedules.create');
  });

  const expectedStatusCodes = computed(() => parseStatusCodes(expectedStatusInput.value));

  const targetPlaceholder = computed(() => {
    if (form.protocol === 'CERTIFICATE') return '请输入 https://your-domain.com';
    if (form.protocol === 'Telnet') return '请输入域名或IP地址';
    if (form.protocol === 'WSS') return '请输入 wss://your-domain.com';
    return '请输入包含 http:// 或 https:// 的完整域名';
  });

  watch(
    () => form.protocol,
    (next) => {
      const isCert = next === 'CERTIFICATE';
      isCertificateProtocol.value = isCert;
      if (isCert) {
        form.frequency_minutes = DEFAULT_CERT_FREQUENCY;
      } else if (form.frequency_minutes === DEFAULT_CERT_FREQUENCY) {
        form.frequency_minutes = 1;
      }
    },
    { immediate: true }
  );

  watch(
    () => alertContactsText.value,
    () => {
      success.value = null;
      error.value = null;
    }
  );

  async function handleSubmit() {
    error.value = null;
    success.value = null;
    submitting.value = true;
    try {
      const payload = buildRequestPayload(form, alertContactsText.value, expectedStatusCodes.value);
      form.alert_contacts = payload.alert_contacts || [];
      alertContactsText.value = form.alert_contacts.join(', ');
      const response = await submitMonitoringRequest(payload);
      success.value = response?.id ? `等待管理员审批（申请ID：${response.id}）` : '等待管理员审批';
      ElMessage.success('申请已提交');
      await loadRequests();
    } catch (err) {
      console.error('提交申请失败', err);
      error.value = '提交失败，请稍后重试。';
    } finally {
      submitting.value = false;
    }
  }

  async function handleUpdate() {
    if (!editingRequestId.value) return;
    error.value = null;
    success.value = null;
    submitting.value = true;
    try {
      const payload = buildRequestPayload(form, alertContactsText.value, expectedStatusCodes.value);
      form.alert_contacts = payload.alert_contacts || [];
      alertContactsText.value = form.alert_contacts.join(', ');
      await updateMonitoringRequest(editingRequestId.value, payload);
      if (editingRequestStatus.value === 'approved') {
        ElMessage.success('已保存修改并立即生效');
      } else {
        ElMessage.success('已保存修改（请在右侧记录中点击“重新提交”进入审批）');
      }
      await loadRequests();
    } catch (err) {
      console.error('保存修改失败', err);
      error.value = '保存失败，请稍后重试。';
    } finally {
      submitting.value = false;
    }
  }

  async function loadRequests() {
    requests.value = await listMonitoringRequests();
    if (!editingRequestId.value) return;

    const current = requests.value.find((item) => item.id === editingRequestId.value);
    if (!current || (current.status !== 'rejected' && current.status !== 'approved')) {
      editingRequestId.value = null;
      editingRequestStatus.value = null;
      return;
    }
    editingRequestStatus.value = current.status as 'rejected' | 'approved';
  }

  async function loadProbes() {
    probesLoading.value = true;
    try {
      const { data } = await apiClient.get<MonitoringProbeNode[]>('/probes/nodes/');
      probes.value = data;
      const available = new Set(data.map((probe) => probe.id));
      form.probe_ids = form.probe_ids.filter((id) => available.has(id));
    } finally {
      probesLoading.value = false;
    }
  }

  async function loadSystems() {
    systemsLoading.value = true;
    try {
      const { data } = await apiClient.get<Array<{ system_name?: string | null }>>('/assets/records');
      systemOptions.value = Array.from(
        new Set((data || []).map((item) => item.system_name).filter((name): name is string => Boolean(name)))
      );
    } finally {
      systemsLoading.value = false;
    }
  }

  async function handleHeaderRefresh() {
    if (headerRefreshing.value) return;
    headerRefreshing.value = true;
    success.value = null;
    error.value = null;
    try {
      const results = await Promise.allSettled([loadRequests(), loadProbes(), loadSystems()]);
      const failedCount = results.filter((item) => item.status === 'rejected').length;
      if (failedCount) {
        ElMessage.warning(`刷新完成，但有 ${failedCount} 项失败`);
      } else {
        ElMessage.success('已刷新');
      }
    } finally {
      headerRefreshing.value = false;
    }
  }

  function startEditing(request: MonitoringRequestRecord) {
    if (!request || (request.status !== 'rejected' && request.status !== 'approved')) {
      ElMessage.warning('仅允许编辑已通过或已驳回的申请');
      return;
    }

    editingRequestId.value = request.id;
    editingRequestStatus.value = request.status as 'rejected' | 'approved';
    success.value = null;
    error.value = null;

    const meta = request.metadata || {};
    form.title = request.title || '周期拨测申请';
    form.target = request.target || '';
    form.protocol = request.protocol || 'HTTPS';
    form.frequency_minutes = Number(request.frequency_minutes || meta.frequency_minutes || 1);
    form.system_name = String(meta.system_name || '');
    form.network_type = meta.network_type === 'internal' ? 'internal' : 'internet';
    form.owner_name = String(meta.owner_name || '');
    form.probe_ids = Array.isArray(meta.probe_ids) ? meta.probe_ids.map((value) => String(value)) : [];
    form.alert_threshold = Number(meta.alert_threshold || 3);

    const contacts = Array.isArray(meta.alert_contacts) ? meta.alert_contacts.map((value) => String(value)) : [];
    form.alert_contacts = contacts;
    alertContactsText.value = contacts.join(', ');

    const codes = Array.isArray(request.expected_status_codes) ? request.expected_status_codes : [];
    expectedStatusInput.value = codes.length ? codes.join(', ') : '200';
  }

  function cancelEditing() {
    editingRequestId.value = null;
    editingRequestStatus.value = null;
    success.value = null;
    error.value = null;
  }

  function normalizeExpectedStatusInput() {
    const normalized = parseStatusCodes(expectedStatusInput.value);
    expectedStatusInput.value = normalized.length ? normalized.join(', ') : '200';
  }

  onMounted(() => {
    void loadRequests();
    void loadProbes();
    void loadSystems();
  });

  return {
    alertContactsText,
    canSubmit,
    editingRequestId,
    editingRequestStatus,
    error,
    expectedStatusCodes,
    expectedStatusInput,
    form,
    frequencyOptions: monitoringFrequencyOptions,
    handleHeaderRefresh,
    loadRequests,
    handleSubmit,
    handleUpdate,
    headerRefreshing,
    isCertificateProtocol,
    loadProbes,
    requests,
    probes,
    probesLoading,
    startEditing,
    submitting,
    success,
    systemOptions,
    systemsLoading,
    targetPlaceholder,
    normalizeExpectedStatusInput,
    cancelEditing,
    protocolOptions: monitoringProtocolOptions,
    sessionStore
  };
}

function buildRequestPayload(
  form: MonitoringRequestFormState,
  alertContactsInput: string,
  expectedStatusCodes: number[]
): MonitoringRequestPayload {
  const contacts = parseContacts(alertContactsInput);
  const codes = expectedStatusCodes.length ? expectedStatusCodes : [200];

  return {
    title: form.title,
    target: form.target,
    system_name: form.system_name,
    network_type: form.network_type,
    owner_name: form.owner_name || undefined,
    alert_contacts: contacts.length ? contacts : undefined,
    protocol: form.protocol,
    frequency_minutes: form.frequency_minutes,
    probe_ids: form.probe_ids.length ? form.probe_ids : undefined,
    alert_threshold: form.alert_threshold || undefined,
    expected_status_codes: codes
  };
}

function parseContacts(input: string): string[] {
  return input
    .split(',')
    .map((contact) => contact.trim())
    .filter(Boolean);
}

function parseStatusCodes(input: string): number[] {
  if (!input) return [];
  const segments = input
    .split(/[,，\\s]+/)
    .map((segment) => segment.trim())
    .filter(Boolean);
  const normalized = segments
    .map((segment) => Number(segment))
    .filter((code) => Number.isInteger(code) && code >= 100 && code <= 599);
  return Array.from(new Set(normalized));
}
