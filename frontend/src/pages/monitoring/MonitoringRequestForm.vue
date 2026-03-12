<template>
  <DetectionPageBase
    root-title="工单申请"
    title="拨测监控申请"
    :error="error"
    config-title="申请配置"
    refreshable
    :refreshing="headerRefreshing"
    refresh-text="刷新"
    @refresh="handleHeaderRefresh"
  >
    <template #intro>
      <el-alert v-if="success" type="success" :closable="false" show-icon class="mb-4">
        申请已提交：{{ success }}
      </el-alert>
      <el-alert v-if="editingRequestId" type="warning" show-icon class="mb-4" :closable="false">
        <template v-if="editingRequestStatus === 'approved'">
          正在修改已通过并已生效的申请（ID：{{ editingRequestId }}）。保存修改后立即生效，无需重新提交。
        </template>
        <template v-else>
          正在修改已驳回的申请（ID：{{ editingRequestId }}）。保存修改后需要“重新提交”才会进入审批。
        </template>
      </el-alert>
    </template>

    <template #header-left>
      <div class="protocol-combo">
        <el-select
          v-model="form.protocol"
          class="protocol-combo__select"
          size="large"
          :disabled="submitting"
        >
          <el-option label="HTTPS" value="HTTPS" />
          <el-option label="HTTP" value="HTTP" />
          <el-option label="WebSocket" value="WSS" />
          <el-option label="Telnet" value="Telnet" />
          <el-option label="证书检测" value="CERTIFICATE" />
        </el-select>
        <el-input
          v-model="form.target"
          class="protocol-combo__input"
          size="large"
          data-test="monitoring-target"
          :placeholder="targetPlaceholder"
          :disabled="submitting"
          clearable
          @keyup.enter="handleSubmit"
        />
      </div>
    </template>

    <template #config>
      <div class="detection-grid">
        <div class="request-left">
          <DetectionConfig title="基础信息" embedded>
            <template #config-items>
              <div class="config-item config-item--column">
                <div class="config-item__header">
                  <span class="config-item__label">拨测标题</span>
                </div>
                <el-input v-model="form.title" data-test="monitoring-title" />
              </div>

              <div class="config-item config-item--column">
                <div class="config-item__header">
                  <span class="config-item__label">所属系统</span>
                </div>
                <el-select
                  v-model="form.system_name"
                  data-test="monitoring-system-name"
                  filterable
                  allow-create
                  :loading="systemsLoading"
                  placeholder="请选择或输入系统名称"
                >
                  <el-option
                    v-for="option in systemOptions"
                    :key="option"
                    :label="option"
                    :value="option"
                  />
                </el-select>
              </div>

              <div class="config-item config-item--row">
                <span class="config-item__label">网络类型</span>
                <el-select v-model="form.network_type" class="narrow-select">
                  <el-option label="内网域名" value="internal" />
                  <el-option label="互联网域名" value="internet" />
                </el-select>
              </div>

              <div class="config-item config-item--column">
                <div class="config-item__header">
                  <span class="config-item__label">负责人</span>
                </div>
                <el-input v-model="form.owner_name" placeholder="请输入负责人姓名" />
              </div>

              <div class="config-item config-item--column">
                <div class="config-item__header">
                  <span class="config-item__label">告警联系人</span>
                </div>
                <el-input v-model="alertContactsText" placeholder="示例：000123,000456" />
                <span class="hint-text hint-text--block">多个工号请用英文逗号分隔</span>
              </div>
            </template>
          </DetectionConfig>

          <ProbeNodeSelector
            v-model="form.probe_ids"
            :nodes="probes"
            :loading="probesLoading"
            embedded
            hint="可多选节点，将依次在各节点执行拨测。"
            @refresh="loadProbes"
          />
        </div>

        <DetectionConfig title="拨测配置" embedded>
          <template #config-items>
            <div class="config-item config-item--column">
              <div class="config-item__header">
                <span class="config-item__label">频率（分钟）</span>
              </div>
              <el-select
                v-model="form.frequency_minutes"
                :disabled="isCertificateProtocol"
                data-test="monitoring-frequency"
              >
                <el-option
                  v-for="option in frequencyOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
              <span v-if="isCertificateProtocol" class="hint-text hint-text--block"
                >证书检测默认每天执行一次。</span
              >
            </div>

            <div class="config-item config-item--row">
              <span class="config-item__label">告警阈值</span>
              <div class="inline-field">
                <el-input-number v-model="form.alert_threshold" :min="1" :max="10" />
                <span class="hint-text inline-hint">连续失败次数</span>
              </div>
            </div>

            <div class="config-item config-item--column">
              <div class="config-item__header">
                <span class="config-item__label">期望状态码</span>
              </div>
              <el-input
                v-model="expectedStatusInput"
                placeholder="例如 200,202"
                clearable
                @blur="normalizeExpectedStatusInput"
              />
              <span class="hint-text hint-text--block">
                支持多个状态码，用逗号或空格分隔；留空默认 200。
              </span>
              <div v-if="expectedStatusCodes.length" class="status-tags">
                <el-tag v-for="code in expectedStatusCodes" :key="code" round size="small">{{
                  code
                }}</el-tag>
              </div>
            </div>
          </template>
        </DetectionConfig>
      </div>
    </template>

    <template #config-footer>
      <div class="submit-row">
        <el-button v-if="editingRequestId" size="large" @click="cancelEditing">取消编辑</el-button>
        <el-button
          type="primary"
          size="large"
          :loading="submitting"
          :disabled="!canSubmit"
          @click="editingRequestId ? handleUpdate() : handleSubmit()"
        >
          {{ editingRequestId ? '保存修改' : '提交申请' }}
        </el-button>
      </div>
    </template>

    <template #content>
      <ResultsCard title="申请记录">
        <template #actions>
          <el-button
            text
            size="small"
            :loading="headerRefreshing"
            :disabled="headerRefreshing"
            @click="handleHeaderRefresh"
          >
            刷新
          </el-button>
        </template>

        <RequestTimeline
          :requests="requests"
          :current-user-id="sessionStore.user?.id"
          :is-admin="Boolean(sessionStore.user?.is_admin)"
          embedded
          @refresh="loadRequests"
          @edit="startEditing"
        />
      </ResultsCard>
    </template>
  </DetectionPageBase>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';

import DetectionPageBase from '../detection/components/DetectionPageBase.vue';
import DetectionConfig from '../detection/components/DetectionConfig.vue';
import ProbeNodeSelector from '../detection/components/ProbeNodeSelector.vue';
import ResultsCard from '../detection/components/ResultsCard.vue';
import RequestTimeline from './components/RequestTimeline.vue';
import { useSessionStore } from '@/stores/session';
import {
  listMonitoringRequests,
  submitMonitoringRequest,
  updateMonitoringRequest,
  type MonitoringRequestRecord
} from '@/services/monitoringApi';
import apiClient from '@/services/apiClient';

interface MonitoringRequestFormState {
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

interface ProbeNode {
  id: string;
  name: string;
  network_type: string;
}

const DEFAULT_CERT_FREQUENCY = 1440;

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
const sessionStore = useSessionStore();
const editingRequestId = ref<string | null>(null);
const editingRequestStatus = ref<'rejected' | 'approved' | null>(null);
const canSubmit = computed(() => {
  if (editingRequestId.value) return true;
  return sessionStore.hasPermission('detection.schedules.create');
});

const submitting = ref(false);
const error = ref<string | null>(null);
const success = ref<string | null>(null);
const headerRefreshing = ref(false);
const requests = ref<MonitoringRequestRecord[]>([]);
const probes = ref<ProbeNode[]>([]);
const probesLoading = ref(false);
const systemOptions = ref<string[]>([]);
const systemsLoading = ref(false);

const expectedStatusInput = ref('200');
const expectedStatusCodes = computed(() => parseStatusCodes(expectedStatusInput.value));

const frequencyOptions = [
  { label: '1 分钟', value: 1 },
  { label: '3 分钟', value: 3 },
  { label: '5 分钟', value: 5 },
  { label: '15 分钟', value: 15 },
  { label: '30 分钟', value: 30 },
  { label: '1 天', value: 1440 }
];

const isCertificateProtocol = ref(false);

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
  }
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
    const contacts = parseContacts(alertContactsText.value);
    form.alert_contacts = contacts;
    alertContactsText.value = contacts.join(', ');
    const expectedCodes = expectedStatusCodes.value.length ? expectedStatusCodes.value : [200];
    const payload = {
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
      expected_status_codes: expectedCodes
    };
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
    const contacts = parseContacts(alertContactsText.value);
    form.alert_contacts = contacts;
    alertContactsText.value = contacts.join(', ');
    const expectedCodes = expectedStatusCodes.value.length ? expectedStatusCodes.value : [200];
    const payload = {
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
      expected_status_codes: expectedCodes
    };
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
  if (editingRequestId.value) {
    const current = requests.value.find((item) => item.id === editingRequestId.value);
    if (!current || (current.status !== 'rejected' && current.status !== 'approved')) {
      editingRequestId.value = null;
      editingRequestStatus.value = null;
    } else {
      editingRequestStatus.value = current.status as any;
    }
  }
}

async function loadProbes() {
  probesLoading.value = true;
  try {
    const { data } = await apiClient.get<ProbeNode[]>('/probes/nodes/');
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
    const names = Array.from(
      new Set((data || []).map((item) => item.system_name).filter((name): name is string => !!name))
    );
    systemOptions.value = names;
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

onMounted(() => {
  loadRequests();
  loadProbes();
  loadSystems();
});

function startEditing(request: MonitoringRequestRecord) {
  if (!request || (request.status !== 'rejected' && request.status !== 'approved')) {
    ElMessage.warning('仅允许编辑已通过或已驳回的申请');
    return;
  }
  editingRequestId.value = request.id;
  editingRequestStatus.value = request.status as any;
  success.value = null;
  error.value = null;

  const meta = request.metadata || {};
  form.title = request.title || '周期拨测申请';
  form.target = request.target || '';
  form.protocol = request.protocol || 'HTTPS';
  form.frequency_minutes = Number(request.frequency_minutes || meta.frequency_minutes || 1);
  form.system_name = String(meta.system_name || '');
  form.network_type = (meta.network_type === 'internal' ? 'internal' : 'internet') as any;
  form.owner_name = String(meta.owner_name || '');
  form.probe_ids = Array.isArray(meta.probe_ids) ? meta.probe_ids.map((v: any) => String(v)) : [];
  form.alert_threshold = Number(meta.alert_threshold || 3);

  const contacts = Array.isArray(meta.alert_contacts) ? meta.alert_contacts.map((v: any) => String(v)) : [];
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

function normalizeExpectedStatusInput() {
  const normalized = parseStatusCodes(expectedStatusInput.value);
  expectedStatusInput.value = normalized.length ? normalized.join(', ') : '200';
}
</script>

<style scoped>
@import '../detection/styles/detection-common.scss';

.mb-4 {
  margin-bottom: 16px;
}

.request-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.protocol-combo {
  display: flex;
  align-items: stretch;
  flex: 1;
  min-width: min(520px, 100%);
  border-radius: var(--oa-radius-md);
  background: var(--oa-bg-panel);
  box-shadow: 0 0 0 1px var(--oa-border-color) inset;
  transition: box-shadow 0.2s ease;
  overflow: hidden;
}

.protocol-combo:hover {
  box-shadow: 0 0 0 1px var(--oa-text-muted) inset;
}

.protocol-combo:focus-within {
  box-shadow: 0 0 0 2px var(--oa-color-primary-light) inset;
}

.protocol-combo__select {
  width: 140px;
  flex: 0 0 auto;
}

.protocol-combo :deep(.protocol-combo__select .el-select__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: var(--oa-radius-md) 0 0 var(--oa-radius-md);
  border-right: 1px solid var(--oa-border-color);
  min-height: 44px;
}

.protocol-combo__input {
  flex: 1;
  min-width: 0;
}

.protocol-combo :deep(.protocol-combo__input .el-input__wrapper),
.protocol-combo :deep(.protocol-combo__input .el-input__wrapper:hover),
.protocol-combo :deep(.protocol-combo__input .el-input__wrapper.is-focus) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 var(--oa-radius-md) var(--oa-radius-md) 0;
  min-height: 44px;
}

.hint-text--block {
  display: block;
  margin-left: 0;
  margin-top: 8px;
}

.inline-field {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.submit-row {
  display: flex;
  justify-content: center;
  width: 100%;
}
</style>
