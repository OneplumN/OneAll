<template>
  <RepositoryPageShell
    root-title="监控策略"
    :section-title="isCreateMode ? '新建监控策略' : (check ? check.name : '加载中...')"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <el-button
        class="toolbar-button"
        @click="goBack"
      >
        返回列表
      </el-button>
    </template>

    <el-alert
      v-if="error"
      type="error"
      :closable="false"
      class="oa-inline-alert"
      show-icon
    >
      {{ error }}
    </el-alert>

    <div
      v-if="isCreateMode || check"
      class="oa-detail-page"
    >
      <div class="oa-detail-header">
        <div class="oa-detail-header__left">
          <div class="oa-detail-title">
            {{ isCreateMode ? '新建监控策略' : form.name || check?.name || '监控策略' }}
          </div>
          <div class="oa-detail-meta">
            <span>{{ isCreateMode ? '手工配置' : sourceTypeLabel(check?.source_type || 'ad_hoc') }}</span>
            <span class="sep">·</span>
            <span>{{ form.protocol }}</span>
            <span class="sep">·</span>
            <span>{{ form.target || '未设置目标' }}</span>
            <span
              v-if="!isEditable"
              class="sep"
            >·</span>
            <span v-if="!isEditable">当前仅支持调整告警条件与通知设置</span>
          </div>
        </div>
      </div>

      <div class="oa-detail-scroll">
        <div class="check-detail-main">
          <el-card
            shadow="never"
            class="oa-detail-card check-detail-card"
          >
            <el-form
              label-width="100px"
              :model="form"
              class="detail-form"
              :disabled="!isEditable"
            >
              <section class="form-section">
                <h3 class="oa-section-title">
                  基本信息
                </h3>
                <el-form-item
                  label="策略名称"
                  required
                >
                  <el-input v-model="form.name" />
                </el-form-item>
                <el-form-item
                  label="探测目标"
                  required
                >
                  <el-input
                    v-model="form.target"
                    placeholder="例如：https://example.com"
                  />
                </el-form-item>
                <el-form-item
                  label="协议"
                  required
                >
                  <el-select
                    v-model="form.protocol"
                    class="narrow-select"
                  >
                    <el-option
                      label="HTTP"
                      value="HTTP"
                    />
                    <el-option
                      label="HTTPS"
                      value="HTTPS"
                    />
                    <el-option
                      label="TCP"
                      value="TCP"
                    />
                    <el-option
                      label="证书（仅证书检测）"
                      value="CERTIFICATE"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="频率 (分钟)">
                  <el-input-number
                    v-model="form.frequency_minutes"
                    :min="1"
                    :max="1440"
                  />
                </el-form-item>
                <el-form-item
                  v-if="isEditable"
                  label="执行探针"
                  required
                >
                  <el-select
                    v-model="form.probe_ids"
                    multiple
                    filterable
                    clearable
                    collapse-tags
                    collapse-tags-tooltip
                    class="oa-input-lg"
                    placeholder="请选择执行探针"
                  >
                    <el-option
                      v-for="probe in availableProbes"
                      :key="probe.id"
                      :label="probeOptionLabel(probe)"
                      :value="probe.id"
                    />
                  </el-select>
                </el-form-item>
              </section>

              <section
                v-if="form.protocol !== 'CERTIFICATE'"
                class="form-section"
              >
                <h3 class="oa-section-title">
                  探测配置
                </h3>
                <el-form-item label="请求超时 (秒)">
                  <el-input-number
                    v-model="form.timeout_seconds"
                    :min="1"
                    :max="600"
                  />
                </el-form-item>
                <el-form-item label="期望状态码">
                  <el-input
                    v-model="expectedStatusInput"
                    placeholder="例如：200 或 200, 302"
                    class="oa-input-lg"
                    @blur="syncExpectedStatusFromInput"
                  />
                  <div
                    v-if="form.expected_status_codes.length"
                    class="status-tag-list"
                  >
                    <el-tag
                      v-for="code in form.expected_status_codes"
                      :key="code"
                      round
                      size="small"
                    >
                      {{ code }}
                    </el-tag>
                  </div>
                </el-form-item>
              </section>

              <section class="form-section">
                <h3 class="oa-section-title">
                  告警条件
                </h3>
                <el-form-item
                  v-if="form.protocol !== 'CERTIFICATE'"
                  label="连续失败次数"
                >
                  <el-input-number
                    v-model="form.alert_threshold"
                    :min="1"
                    :max="10"
                  />
                  <span class="hint-text">连续失败达到此次数时触发告警。</span>
                </el-form-item>

                <template v-if="form.protocol === 'HTTPS' || form.protocol === 'CERTIFICATE'">
                  <el-divider v-if="form.protocol === 'HTTPS'" />
                  <h3
                    v-if="form.protocol === 'HTTPS'"
                    class="oa-section-title"
                  >
                    证书告警
                  </h3>
                  <el-form-item
                    v-if="form.protocol === 'HTTPS'"
                    label="启用证书检测"
                  >
                    <el-switch v-model="form.cert_check_enabled" />
                  </el-form-item>
                  <el-form-item label="提前告警天数">
                    <el-input-number
                      v-model="form.cert_warning_days"
                      :min="1"
                      :max="365"
                    />
                    <span class="hint-text">证书剩余天数小于该值时触发证书告警。</span>
                  </el-form-item>
                </template>
              </section>

              <section class="form-section">
                <h3 class="oa-section-title">
                  通知设置
                </h3>
                <el-form-item label="通知渠道">
                  <div class="channels-row">
                    <template v-if="activeChannels.length">
                      <el-checkbox-group v-model="form.alert_channels">
                        <el-checkbox
                          v-for="channel in activeChannels"
                          :key="channel.type"
                          :label="channel.type"
                        >
                          {{ channel.name }}
                        </el-checkbox>
                      </el-checkbox-group>
                    </template>
                    <span
                      v-else
                      class="channels-empty"
                    >
                      当前没有启用的告警通道，请在「系统设置 - 告警通道」中配置。
                    </span>
                  </div>
                  <p class="hint-text">
                    不选择时默认使用全部已启用的告警通道。
                  </p>
                </el-form-item>

                <el-form-item label="通知对象">
                  <el-input
                    v-model="alertContactsText"
                    placeholder="工号或邮箱，逗号分隔"
                  />
                </el-form-item>
              </section>
            </el-form>
          </el-card>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="check-detail-footer">
        <span
          v-if="!isEditable"
          class="oa-detail-footer__hint"
        >
          该策略来自监控申请，当前仅支持调整告警条件和通知对象。
        </span>
        <div class="oa-detail-footer">
          <el-button @click="goBack">
            取消
          </el-button>
          <el-button
            type="primary"
            :loading="saving"
            :disabled="!isEditable || !dirty"
            @click="handleSave"
          >
            保存
          </el-button>
        </div>
      </div>
    </template>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import type { AlertCheckDetail, AlertCheckFormPayload, AlertCheckSummary } from '@/features/alerts/api/alertsApi';
import {
  createAlertCheck,
  fetchAlertCheckSchedules,
  updateAlertCheckDetail,
} from '@/features/alerts/api/alertsApi';
import type { AlertChannelRecord } from '@/features/settings/api/settingsApi';
import { fetchAlertChannels } from '@/features/settings/api/settingsApi';
import { listProbeNodes, type ProbeNodeRecord } from '@/features/probes/api/probeNodeApi';

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);

const check = ref<AlertCheckSummary | null>(null);
const availableProbes = ref<ProbeNodeRecord[]>([]);

const form = reactive({
  name: '',
  target: '',
  protocol: 'HTTPS',
  frequency_minutes: 5,
  probe_ids: [] as string[],
  timeout_seconds: 5,
  expected_status_codes: [] as number[],
  alert_threshold: 1,
  alert_contacts: [] as string[],
  alert_channels: [] as string[],
  cert_check_enabled: false,
  cert_warning_days: 30,
});

const expectedStatusInput = ref('');
const alertContactsText = ref('');

const isCreateMode = computed(() => (route.params.checkId as string) === 'new');

const isEditable = computed(
  () => isCreateMode.value || check.value?.source_type === 'probe_schedule',
);

const originalSnapshot = ref<string>('');
const dirty = computed(() => JSON.stringify(form) !== originalSnapshot.value);

const goBack = () => {
  router.push({ name: 'alerts-checks' });
};

const channels = ref<AlertChannelRecord[]>([]);
const activeChannels = computed(() => channels.value.filter((item) => item.enabled));

const sourceTypeLabel = (value: string) => {
  if (value === 'monitoring_request') return '监控任务';
  if (value === 'probe_schedule') return '探针调度';
  if (value === 'ad_hoc') return '临时检测';
  return value || '未知';
};

const initSnapshotAndChannels = async () => {
  try {
    channels.value = await fetchAlertChannels();
  } catch {
    channels.value = [];
  }
  originalSnapshot.value = JSON.stringify(form);
};

const loadAvailableProbes = async () => {
  try {
    availableProbes.value = await listProbeNodes();
    if (isCreateMode.value && !form.probe_ids.length) {
      form.probe_ids = availableProbes.value
        .filter((probe) => probe.status === 'online')
        .map((probe) => probe.id);
    }
  } catch {
    availableProbes.value = [];
  }
};

const probeOptionLabel = (probe: ProbeNodeRecord) => {
  const pieces = [probe.name];
  if (probe.ip_address) pieces.push(probe.ip_address);
  if (probe.location) pieces.push(probe.location);
  pieces.push(probe.status === 'online' ? '在线' : '离线');
  return pieces.join(' · ');
};

const applyDetailToForm = (
  detail: AlertCheckDetail,
  options: { cloneMode?: boolean } = {},
) => {
  check.value = detail.check;

  const schedules = detail.schedules || [];
  const primarySchedule =
    schedules.find((s) => s.status === 'active') || schedules[0] || null;

  form.name = options.cloneMode ? `${detail.check.name}-副本` : detail.check.name;
  form.target = detail.check.target;
  form.protocol = detail.check.protocol;
  form.frequency_minutes = primarySchedule?.frequency_minutes ?? 5;
  form.probe_ids = [...(detail.check.probe_ids || [])];

  const meta = primarySchedule?.metadata || {};
  form.timeout_seconds = (meta.timeout_seconds as number) ?? 5;
  form.expected_status_codes = (meta.expected_status_codes as number[]) ?? [200];
  form.alert_threshold = (meta.alert_threshold as number) ?? 1;
  form.alert_contacts = (meta.alert_contacts as string[]) ?? [];
  form.alert_channels = ((meta.alert_channels as string[]) ?? []).map((c) => String(c));
  form.cert_check_enabled = Boolean(meta.cert_check_enabled);
  form.cert_warning_days = (meta.cert_warning_days as number) ?? 30;

  expectedStatusInput.value = form.expected_status_codes.join(', ');
  alertContactsText.value = form.alert_contacts.join(', ');
};

const loadDetail = async () => {
  loading.value = true;
  error.value = null;
  try {
    const checkId = route.params.checkId as string;
    const detail: AlertCheckDetail = await fetchAlertCheckSchedules(checkId);
    applyDetailToForm(detail);
    await Promise.all([initSnapshotAndChannels(), loadAvailableProbes()]);
  } catch (err) {
    error.value = '无法加载策略详情，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

const loadCloneSource = async (sourceCheckId: string) => {
  loading.value = true;
  error.value = null;
  try {
    const detail: AlertCheckDetail = await fetchAlertCheckSchedules(sourceCheckId);
    applyDetailToForm(detail, { cloneMode: true });
    await Promise.all([initSnapshotAndChannels(), loadAvailableProbes()]);
  } catch {
    error.value = '无法加载克隆来源策略，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

const syncExpectedStatusFromInput = () => {
  const raw = expectedStatusInput.value.trim();
  if (!raw) {
    form.expected_status_codes = [];
    return;
  }
  const parts = raw.split(',').map((s) => s.trim());
  const codes = new Set<number>();
  for (const p of parts) {
    const n = Number(p);
    if (Number.isFinite(n) && n >= 100 && n <= 599) {
      codes.add(n);
    }
  }
  form.expected_status_codes = Array.from(codes).sort((a, b) => a - b);
  expectedStatusInput.value = form.expected_status_codes.join(', ');
};

const syncContactsFromText = () => {
  const raw = alertContactsText.value.trim();
  if (!raw) {
    form.alert_contacts = [];
    return;
  }
  const parts = raw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  form.alert_contacts = parts;
};

const handleSave = async () => {
  syncExpectedStatusFromInput();
  syncContactsFromText();
  if (!form.probe_ids.length) {
    error.value = '请至少选择一个执行探针。';
    ElMessage.error(error.value);
    return;
  }
  if (isCreateMode.value) {
    await handleCreateSave();
    return;
  }
  if (!isEditable.value || !check.value) {
    return;
  }
  saving.value = true;
  error.value = null;
  try {
    const payload: Partial<AlertCheckFormPayload> = {
      name: form.name,
      target: form.target,
      protocol: form.protocol,
      frequency_minutes: form.frequency_minutes,
      probe_ids: [...form.probe_ids],
      timeout_seconds: form.timeout_seconds,
      expected_status_codes: form.expected_status_codes,
      alert_contacts: form.alert_contacts,
    };
    if (form.protocol !== 'CERTIFICATE') {
      payload.alert_threshold = form.alert_threshold;
    }
    if (form.protocol === 'HTTPS' || form.protocol === 'CERTIFICATE') {
      payload.cert_check_enabled = form.cert_check_enabled;
      payload.cert_warning_days = form.cert_warning_days;
    }
    if (form.alert_channels && form.alert_channels.length) {
      payload.alert_channels = [...form.alert_channels];
    }

    await updateAlertCheckDetail(check.value.id, payload);
    originalSnapshot.value = JSON.stringify(form);
    ElMessage.success('策略已保存');
  } catch (err) {
    error.value = '保存策略失败，请稍后重试。';
    ElMessage.error('保存策略失败，请稍后重试。');
  } finally {
    saving.value = false;
  }
};

const handleCreateSave = async () => {
  saving.value = true;
  error.value = null;
  try {
    if (!form.probe_ids.length) {
      error.value = '当前没有可用探针节点，无法创建监控策略，请先在“节点”页面注册探针。';
      ElMessage.error(error.value);
      return;
    }

    const payload: AlertCheckFormPayload = {
      name: form.name,
      target: form.target,
      protocol: form.protocol,
      frequency_minutes: form.frequency_minutes,
      probe_ids: [...form.probe_ids],
      timeout_seconds: form.timeout_seconds,
      expected_status_codes: form.expected_status_codes,
      alert_contacts: form.alert_contacts,
    };
    if (form.protocol !== 'CERTIFICATE') {
      payload.alert_threshold = form.alert_threshold;
    }
    if (form.protocol === 'HTTPS' || form.protocol === 'CERTIFICATE') {
      payload.cert_check_enabled = form.cert_check_enabled;
      payload.cert_warning_days = form.cert_warning_days;
    }
    if (form.alert_channels && form.alert_channels.length) {
      payload.alert_channels = [...form.alert_channels];
    }

    await createAlertCheck(payload);
    originalSnapshot.value = JSON.stringify(form);
    ElMessage.success('策略已创建');
    router.push({ name: 'alerts-checks' });
  } catch (err) {
    error.value = '创建策略失败，请稍后重试。';
    ElMessage.error(error.value);
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  if (isCreateMode.value) {
    const cloneFrom = route.query.cloneFrom;
    if (typeof cloneFrom === 'string' && cloneFrom.trim()) {
      await loadCloneSource(cloneFrom);
    } else {
      await Promise.all([initSnapshotAndChannels(), loadAvailableProbes()]);
    }
  } else {
    await loadDetail();
  }
});
</script>

<style scoped>
.check-detail-main {
  width: 100%;
  max-width: 840px;
  margin: 0 auto;
}

.check-detail-card {
  padding: 12px 16px;
}

.detail-form {
  max-width: 640px;
  margin: 0 auto 8px;
  font-size: var(--oa-font-base);
}

.form-section {
  margin-bottom: 16px;
}

.hint-text {
  margin-left: 12px;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.sep {
  color: var(--oa-text-muted);
}

.status-tag-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.channels-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.channels-empty {
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.check-detail-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

:deep(.page-panel__footer) {
  padding-top: 8px;
  padding-bottom: 8px;
}

.detail-form :deep(.el-form-item__label) {
  font-size: var(--oa-font-subtitle);
  color: var(--oa-text-secondary);
}

.detail-form :deep(.el-input__inner),
.detail-form :deep(.el-textarea__inner),
.detail-form :deep(.el-input-number__input),
.detail-form :deep(.el-select__selected-item),
.detail-form :deep(.el-checkbox__label) {
  font-size: var(--oa-font-base);
}

.detail-form :deep(.el-input__wrapper),
.detail-form :deep(.el-textarea__inner),
.detail-form :deep(.el-select__wrapper),
.detail-form :deep(.el-input-number) {
  font-size: var(--oa-font-base);
}
</style>
