<template>
  <SettingsPageShell section-title="全局设置" body-padding="0" :panel-bordered="false">
    <template #actions>
      <div class="refresh-card" @click="loadSettings">
        <el-icon class="refresh-icon" :class="{ spinning: loading }"><Refresh /></el-icon>
        <span>刷新</span>
      </div>
      <el-button
        class="toolbar-button toolbar-button--primary"
        type="primary"
        :loading="saving"
        :disabled="loading || Boolean(certificateThresholdError)"
        @click="saveSettings"
      >
        保存更改
      </el-button>
    </template>

    <el-alert v-if="error" type="error" show-icon :closable="false" class="mb-3">
      {{ error }}
    </el-alert>

    <div class="system-settings-page">
      <div class="system-settings-scroll">
        <SettingsTabs
          class="settings-stack"
          :form="form"
          :loading="saving"
          :role-options="roleOptions"
          :roles-loading="roleOptionsLoading"
          :syncing-ldap="syncingLdap"
          :certificate-threshold-error="certificateThresholdError"
          @change="handleFieldChange"
          @submit="saveSettings"
          @sync-ldap="triggerLdapSync"
        />
      </div>
    </div>
  </SettingsPageShell>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { computed, onMounted, reactive, ref } from 'vue';

import apiClient from '@/services/apiClient';
import { fetchRoles, syncLdapUsers } from '@/services/settingsApi';
import { useBrandingStore } from '@/stores/branding';

import SettingsTabs from './components/SettingsTabs.vue';
import SettingsPageShell from './components/SettingsPageShell.vue';

interface LDAPIntegration {
  enabled: boolean;
  host: string;
  port: number;
  use_ssl: boolean;
  base_dn: string;
  bind_dn: string;
  bind_password: string;
  has_bind_password: boolean;
  user_filter: string;
  username_attr: string;
  display_name_attr: string;
  email_attr: string;
  sync_filter: string;
  sync_size_limit: number | null;
  default_role_ids: string[];
}

interface IntegrationsForm {
  ldap: LDAPIntegration;
  [key: string]: unknown;
}

interface SystemSettingsForm {
  platform_name: string;
  platform_logo: string;
  default_timezone: string;
  alert_escalation_threshold: number;
  zabbix_dashboard_refresh_seconds: number;
  certificate_expiry_threshold_critical_days: number;
  certificate_expiry_threshold_warning_days: number;
  certificate_expiry_threshold_notice_days: number;
  theme: string;
  notification_channels: {
    email: string;
    webhook: string;
  };
  integrations: IntegrationsForm;
}

type RoleOption = { label: string; value: string };

type LDAPIntegrationPayload = Omit<LDAPIntegration, 'bind_password' | 'has_bind_password' | 'sync_size_limit'> & {
  bind_password?: string;
  sync_size_limit?: number;
};

type IntegrationsPayload = Omit<IntegrationsForm, 'ldap'> & {
  ldap: LDAPIntegrationPayload;
};

type SystemSettingsPayload = Omit<SystemSettingsForm, 'integrations'> & {
  integrations: IntegrationsPayload;
};

const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const roleOptions = ref<RoleOption[]>([]);
const roleOptionsLoading = ref(false);
const syncingLdap = ref(false);
const branding = useBrandingStore();

const form = reactive<SystemSettingsForm>({
  platform_name: '多维运维平台',
  platform_logo: '',
  default_timezone: 'Asia/Shanghai',
  alert_escalation_threshold: 60,
  zabbix_dashboard_refresh_seconds: 60,
  certificate_expiry_threshold_critical_days: 15,
  certificate_expiry_threshold_warning_days: 30,
  certificate_expiry_threshold_notice_days: 45,
  theme: 'light',
  notification_channels: {
    email: 'ops@example.com',
    webhook: ''
  },
  integrations: {
    ldap: {
      enabled: false,
      host: '',
      port: 389,
      use_ssl: false,
      base_dn: '',
      bind_dn: '',
      bind_password: '',
      has_bind_password: false,
      user_filter: '(uid={username})',
      username_attr: 'uid',
      display_name_attr: 'cn',
      email_attr: 'mail',
      sync_filter: '(uid=*)',
      sync_size_limit: null,
      default_role_ids: []
    }
  }
});

function assignForm(data: Partial<SystemSettingsForm>) {
  if (data.platform_name !== undefined) form.platform_name = data.platform_name;
  if (data.platform_logo !== undefined) form.platform_logo = data.platform_logo || '';
  if (data.default_timezone !== undefined) form.default_timezone = data.default_timezone;
  if (data.alert_escalation_threshold !== undefined) {
    form.alert_escalation_threshold = data.alert_escalation_threshold;
  }
  if (data.zabbix_dashboard_refresh_seconds !== undefined) {
    form.zabbix_dashboard_refresh_seconds = data.zabbix_dashboard_refresh_seconds;
  }
  if (data.certificate_expiry_threshold_critical_days !== undefined) {
    form.certificate_expiry_threshold_critical_days = data.certificate_expiry_threshold_critical_days;
  }
  if (data.certificate_expiry_threshold_warning_days !== undefined) {
    form.certificate_expiry_threshold_warning_days = data.certificate_expiry_threshold_warning_days;
  }
  if (data.certificate_expiry_threshold_notice_days !== undefined) {
    form.certificate_expiry_threshold_notice_days = data.certificate_expiry_threshold_notice_days;
  }
  if (data.theme !== undefined) form.theme = data.theme;
  if (data.notification_channels) {
    form.notification_channels.email = data.notification_channels.email ?? '';
    form.notification_channels.webhook = data.notification_channels.webhook ?? '';
  }
  if (data.integrations) {
    assignIntegrations(data.integrations);
  }
}

function assignIntegrations(payload: Partial<IntegrationsForm>) {
  const ldapPayload = payload.ldap;
  if (!ldapPayload) return;
  const ldap = form.integrations.ldap;
  ldap.enabled = Boolean(ldapPayload.enabled);
  ldap.host = ldapPayload.host ?? '';
  ldap.port = Number(ldapPayload.port ?? ldap.port ?? 389);
  ldap.use_ssl = Boolean(ldapPayload.use_ssl);
  ldap.base_dn = ldapPayload.base_dn ?? '';
  ldap.bind_dn = ldapPayload.bind_dn ?? '';
  ldap.has_bind_password = Boolean(ldapPayload.has_bind_password);
  ldap.bind_password = '';
  ldap.user_filter = ldapPayload.user_filter ?? '(uid={username})';
  ldap.username_attr = ldapPayload.username_attr ?? 'uid';
  ldap.display_name_attr = ldapPayload.display_name_attr ?? 'cn';
  ldap.email_attr = ldapPayload.email_attr ?? 'mail';
  ldap.sync_filter = ldapPayload.sync_filter ?? '(uid=*)';
  const limit = ldapPayload.sync_size_limit;
  ldap.sync_size_limit = typeof limit === 'number' ? limit : limit ? Number(limit) : null;
  ldap.default_role_ids = ldapPayload.default_role_ids ?? [];
}

function setByPath(path: string, value: unknown) {
  const segments = path.split('.');
  let target: any = form;
  for (let i = 0; i < segments.length - 1; i += 1) {
    target = target[segments[i]];
  }
  target[segments[segments.length - 1]] = value;
}

async function loadSettings() {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await apiClient.get<SystemSettingsForm>('/settings/system');
    assignForm(data);
  } catch (err) {
    error.value = '无法加载系统设置，请稍后重试。';
  } finally {
    loading.value = false;
  }
}

async function loadRoleOptions() {
  roleOptionsLoading.value = true;
  try {
    const roles = await fetchRoles();
    roleOptions.value = roles.map((role) => ({ label: role.name, value: role.id }));
  } catch (err) {
    console.error('加载角色列表失败', err);
  } finally {
    roleOptionsLoading.value = false;
  }
}

async function saveSettings() {
  if (certificateThresholdError.value) {
    ElMessage.error(certificateThresholdError.value);
    return;
  }
  saving.value = true;
  error.value = null;
  try {
    const { data: latest } = await apiClient.get<SystemSettingsForm>('/settings/system');
    const payload: SystemSettingsPayload = {
      ...latest,
      platform_name: form.platform_name,
      platform_logo: form.platform_logo,
      default_timezone: form.default_timezone,
      certificate_expiry_threshold_critical_days: form.certificate_expiry_threshold_critical_days,
      certificate_expiry_threshold_warning_days: form.certificate_expiry_threshold_warning_days,
      certificate_expiry_threshold_notice_days: form.certificate_expiry_threshold_notice_days,
      integrations: buildIntegrationsPayload()
    };

    const { data } = await apiClient.put<SystemSettingsForm>('/settings/system', payload);
    assignForm(data);
    branding.applyBranding({ platform_name: data.platform_name, platform_logo: data.platform_logo, theme: data.theme });
    ElMessage.success('设置已保存');
  } catch (err) {
    error.value = '保存失败，请检查输入后重试。';
  } finally {
    saving.value = false;
  }
}

function handleFieldChange({ field, value }: { field: string; value: unknown }) {
  setByPath(field, value);
}

const certificateThresholdError = computed(() => {
  const critical = Number(form.certificate_expiry_threshold_critical_days);
  const warning = Number(form.certificate_expiry_threshold_warning_days);
  const notice = Number(form.certificate_expiry_threshold_notice_days);
  if (![critical, warning, notice].every((value) => Number.isFinite(value) && Number.isInteger(value))) {
    return '证书阈值必须为整数';
  }
  if ([critical, warning, notice].some((value) => value < 1)) {
    return '证书阈值必须大于等于 1 天';
  }
  if (critical > warning || warning > notice) {
    return '证书阈值需满足：严重 ≤ 预警 ≤ 提醒';
  }
  return null;
});

onMounted(() => {
  loadSettings();
  loadRoleOptions();
});

async function triggerLdapSync() {
  if (!form.integrations.ldap.enabled) {
    ElMessage.warning('请先启用 LDAP 并填写连接信息');
    return;
  }
  try {
    await ElMessageBox.confirm('立即同步 LDAP 用户？该操作可能需要数秒时间。', '同步确认', {
      type: 'warning'
    });
  } catch (err) {
    return;
  }

  syncingLdap.value = true;
  try {
    const { result, detail } = await syncLdapUsers();
    const summary = detail || `同步完成，共 ${result.total} 条，新增 ${result.created}，更新 ${result.updated}`;
    ElMessage.success(summary);
  } catch (err: any) {
    const message = err?.response?.data?.detail || '同步失败，请稍后重试';
    ElMessage.error(message);
  } finally {
    syncingLdap.value = false;
  }
}

function buildIntegrationsPayload(): IntegrationsPayload {
  const payload: IntegrationsPayload = { ldap: {} as LDAPIntegrationPayload };
  const ldap = form.integrations.ldap;
  payload.ldap = {
    enabled: ldap.enabled,
    host: ldap.host,
    port: ldap.port,
    use_ssl: ldap.use_ssl,
    base_dn: ldap.base_dn,
    bind_dn: ldap.bind_dn,
    user_filter: ldap.user_filter,
    username_attr: ldap.username_attr,
    display_name_attr: ldap.display_name_attr,
    email_attr: ldap.email_attr,
    sync_filter: ldap.sync_filter,
    default_role_ids: ldap.default_role_ids
  };

  if (typeof ldap.sync_size_limit === 'number') {
    payload.ldap.sync_size_limit = ldap.sync_size_limit;
  }

  if (ldap.bind_password) {
    payload.ldap.bind_password = ldap.bind_password;
  }
  return payload;
}
</script>

<style scoped>
.mb-3 {
  margin-bottom: 1rem;
}

.system-settings-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.system-settings-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 16px;
}

.settings-stack {
  width: 100%;
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  background: var(--oa-bg-panel);
  border: 1px solid var(--oa-border-light);
  box-shadow: var(--oa-shadow-sm);
  cursor: pointer;
  user-select: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.refresh-card:hover {
  border-color: var(--oa-color-primary-light);
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.12);
  transform: translateY(-1px);
}

.refresh-icon {
  transition: transform 0.35s ease;
}

.refresh-icon.spinning {
  animation: spinning 0.9s linear infinite;
}

@keyframes spinning {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
