<template>
  <div class="settings-panels">
    <section class="panel">
      <header>
        <div>
          <h3>基础设置</h3>
          <p>平台名称与默认时区会同步到各业务模块。</p>
        </div>
      </header>
      <el-form label-width="140px">
        <el-form-item label="平台名称">
          <el-input
            :model-value="form.platform_name"
            placeholder="多维运维平台"
            @update:model-value="(value: string) => updateField('platform_name', value)"
          />
        </el-form-item>
        <el-form-item label="平台 Logo">
          <div class="logo-field">
            <div class="logo-preview">
              <img v-if="form.platform_logo" :src="form.platform_logo" alt="logo" />
              <div v-else class="logo-placeholder">暂无</div>
            </div>
            <div class="logo-actions">
              <input ref="logoInputRef" class="logo-input" type="file" accept="image/png,image/jpeg,image/webp" @change="handleLogoFileChange" />
              <el-button size="small" @click="triggerLogoPick">上传</el-button>
              <el-button v-if="form.platform_logo" size="small" text type="danger" @click="updateField('platform_logo', '')">
                清除
              </el-button>
              <div class="logo-hint">建议 64×64，PNG/JPG/WebP，≤300KB</div>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="默认时区">
          <el-select :model-value="form.default_timezone" @update:model-value="(value: string) => updateField('default_timezone', value)">
            <el-option label="Asia/Shanghai" value="Asia/Shanghai" />
            <el-option label="UTC" value="UTC" />
          </el-select>
        </el-form-item>
      </el-form>
    </section>

    <section class="panel">
      <header>
        <div>
          <h3>证书监测阈值</h3>
          <p>用于驾驶舱「证书有效期监测」的提醒分级（单位：天）。</p>
        </div>
      </header>
      <el-alert
        v-if="certificateThresholdError"
        type="warning"
        show-icon
        :closable="false"
        class="threshold-alert"
      >
        {{ certificateThresholdError }}
      </el-alert>
      <el-form label-width="160px">
        <div class="threshold-grid">
          <el-form-item label="严重阈值（≤）">
            <el-input-number
              :model-value="form.certificate_expiry_threshold_critical_days"
              :min="1"
              :controls="false"
              @update:model-value="(value: number | string) => updateField('certificate_expiry_threshold_critical_days', Number(value))"
            />
          </el-form-item>
          <el-form-item label="预警阈值（≤）">
            <el-input-number
              :model-value="form.certificate_expiry_threshold_warning_days"
              :min="1"
              :controls="false"
              @update:model-value="(value: number | string) => updateField('certificate_expiry_threshold_warning_days', Number(value))"
            />
          </el-form-item>
          <el-form-item label="提醒阈值（≤）">
            <el-input-number
              :model-value="form.certificate_expiry_threshold_notice_days"
              :min="1"
              :controls="false"
              @update:model-value="(value: number | string) => updateField('certificate_expiry_threshold_notice_days', Number(value))"
            />
          </el-form-item>
        </div>
        <div class="threshold-hint">建议：严重 ≤ 预警 ≤ 提醒（例如 15 / 30 / 45）。</div>
      </el-form>
    </section>

    <section class="panel">
      <header>
        <div>
          <h3>LDAP 集成</h3>
          <p>统一维护目录接入参数与同步策略。</p>
        </div>
      </header>
      <div class="ldap-card">
        <div class="ldap-card__head">
          <div class="head-left">
            <div class="head-title">
              <strong>LDAP / AD</strong>
              <span class="sub">同步企业账号，统一登录与用户来源。</span>
            </div>
            <div class="head-summary">
              <span class="summary-item">
                <span class="label">状态</span>
                <el-tag size="small" effect="plain" :type="form.integrations.ldap.enabled ? 'success' : 'info'">
                  {{ form.integrations.ldap.enabled ? '已启用' : '未启用' }}
                </el-tag>
              </span>
              <span class="summary-item">
                <span class="label">地址</span>
                <span class="value">
                  {{ form.integrations.ldap.host ? `${form.integrations.ldap.host}:${form.integrations.ldap.port}` : '未配置' }}
                </span>
              </span>
              <span class="summary-item">
                <span class="label">加密</span>
                <span class="value">{{ form.integrations.ldap.use_ssl ? 'SSL' : '明文' }}</span>
              </span>
              <span class="summary-item">
                <span class="label">默认角色</span>
                <span class="value">{{ form.integrations.ldap.default_role_ids?.length ?? 0 }} 个</span>
              </span>
              <span class="summary-item">
                <span class="label">密码</span>
                <span class="value">{{ form.integrations.ldap.has_bind_password ? '已配置' : '未配置' }}</span>
              </span>
            </div>
          </div>

          <div class="head-actions">
            <el-switch
              :model-value="form.integrations.ldap.enabled"
              inline-prompt
              active-text="启用"
              inactive-text="关闭"
              @update:model-value="(value: boolean) => updateField('integrations.ldap.enabled', value)"
            />
            <el-button
              size="small"
              type="primary"
              plain
              :loading="props.syncingLdap"
              :disabled="!form.integrations.ldap.enabled"
              @click="emit('sync-ldap')"
            >
              立即同步
            </el-button>
            <el-button size="small" text type="primary" @click="toggleLdapExpanded">
              {{ ldapExpanded ? '收起' : '展开' }}
            </el-button>
          </div>
        </div>

        <el-collapse-transition>
          <div v-show="ldapExpanded" class="ldap-card__body">
            <el-form label-position="top" class="ldap-form" :disabled="!form.integrations.ldap.enabled">
              <div class="form-grid">
                <el-form-item label="服务器地址">
                  <el-input
                    :model-value="form.integrations.ldap.host"
                    placeholder="ldap.example.com"
                    @update:model-value="(value: string) => updateField('integrations.ldap.host', value)"
                  />
                </el-form-item>
                <el-form-item label="端口">
                  <el-input-number
                    :model-value="form.integrations.ldap.port"
                    :min="1"
                    :max="65535"
                    controls-position="right"
                    @update:model-value="(value: number | string) => updateField('integrations.ldap.port', Number(value))"
                  />
                </el-form-item>
                <el-form-item label="安全连接">
                  <el-switch
                    :model-value="form.integrations.ldap.use_ssl"
                    active-text="SSL"
                    inactive-text="明文"
                    @update:model-value="(value: boolean) => updateField('integrations.ldap.use_ssl', value)"
                  />
                </el-form-item>
                <el-form-item label="Base DN">
                  <el-input
                    :model-value="form.integrations.ldap.base_dn"
                    placeholder="dc=example,dc=com"
                    @update:model-value="(value: string) => updateField('integrations.ldap.base_dn', value)"
                  />
                </el-form-item>
                <el-form-item label="Bind DN">
                  <el-input
                    :model-value="form.integrations.ldap.bind_dn"
                    placeholder="cn=sync,dc=example,dc=com"
                    @update:model-value="(value: string) => updateField('integrations.ldap.bind_dn', value)"
                  />
                </el-form-item>
                <el-form-item label="Bind 密码">
                  <el-input
                    type="password"
                    show-password
                    placeholder="留空保持原值"
                    :model-value="form.integrations.ldap.bind_password"
                    @update:model-value="(value: string) => updateField('integrations.ldap.bind_password', value)"
                  />
                </el-form-item>
                <el-form-item label="默认角色" class="span-2">
                  <el-select
                    :model-value="form.integrations.ldap.default_role_ids"
                    multiple
                    collapse-tags
                    filterable
                    placeholder="选择自动分配的角色"
                    :loading="rolesLoading"
                    @update:model-value="(value: string[]) => updateField('integrations.ldap.default_role_ids', value)"
                  >
                    <el-option v-for="role in roleOptions" :key="role.value" :label="role.label" :value="role.value" />
                  </el-select>
                </el-form-item>
              </div>

              <div class="advanced-toggle">
                <el-button size="small" text type="primary" @click="toggleLdapAdvanced">
                  {{ ldapAdvanced ? '收起高级配置' : '展开高级配置' }}
                </el-button>
              </div>

              <el-collapse-transition>
                <div v-show="ldapAdvanced" class="advanced-body">
                  <div class="form-grid">
                    <el-form-item label="用户过滤器">
                      <el-input
                        :model-value="form.integrations.ldap.user_filter"
                        placeholder="(uid={username})"
                        @update:model-value="(value: string) => updateField('integrations.ldap.user_filter', value)"
                      />
                    </el-form-item>
                    <el-form-item label="用户名属性">
                      <el-input
                        :model-value="form.integrations.ldap.username_attr"
                        placeholder="uid"
                        @update:model-value="(value: string) => updateField('integrations.ldap.username_attr', value)"
                      />
                    </el-form-item>
                    <el-form-item label="姓名属性">
                      <el-input
                        :model-value="form.integrations.ldap.display_name_attr"
                        placeholder="cn"
                        @update:model-value="(value: string) => updateField('integrations.ldap.display_name_attr', value)"
                      />
                    </el-form-item>
                    <el-form-item label="邮箱属性">
                      <el-input
                        :model-value="form.integrations.ldap.email_attr"
                        placeholder="mail"
                        @update:model-value="(value: string) => updateField('integrations.ldap.email_attr', value)"
                      />
                    </el-form-item>
                    <el-form-item label="同步过滤器">
                      <el-input
                        :model-value="form.integrations.ldap.sync_filter"
                        placeholder="(objectClass=person)"
                        @update:model-value="(value: string) => updateField('integrations.ldap.sync_filter', value)"
                      />
                    </el-form-item>
                    <el-form-item label="同步上限">
                      <el-input-number
                        :model-value="form.integrations.ldap.sync_size_limit ?? undefined"
                        :min="1"
                        :controls="false"
                        placeholder="不限制"
                        @update:model-value="(value: number | string) => updateField('integrations.ldap.sync_size_limit', value === '' ? null : Number(value))"
                      />
                    </el-form-item>
                  </div>
                </div>
              </el-collapse-transition>
            </el-form>
          </div>
        </el-collapse-transition>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';

type RoleOption = {
  label: string;
  value: string;
};

const props = defineProps<{
  form: SystemSettingsForm;
  loading: boolean;
  roleOptions: RoleOption[];
  rolesLoading: boolean;
  syncingLdap: boolean;
  certificateThresholdError?: string | null;
}>();

const emit = defineEmits<{
  (e: 'change', payload: { field: string; value: unknown }): void;
  (e: 'submit'): void;
  (e: 'sync-ldap'): void;
}>();

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
  integrations: {
    ldap: {
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
    };
    [key: string]: any;
  };
}

const certificateThresholdError = computed(() => props.certificateThresholdError || null);

const updateField = (field: string, value: unknown) => {
  emit('change', { field, value });
};

const logoInputRef = ref<HTMLInputElement | null>(null);

const triggerLogoPick = () => {
  logoInputRef.value?.click();
};

const readFileAsDataUrl = (file: File) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(new Error('read_failed'));
    reader.readAsDataURL(file);
  });

const handleLogoFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement | null;
  const file = input?.files?.[0];
  if (!file) return;
  if (input) input.value = '';

  const allowed = ['image/png', 'image/jpeg', 'image/webp'];
  if (!allowed.includes(file.type)) {
    ElMessage.warning('仅支持 PNG/JPG/WebP 格式');
    return;
  }
  if (file.size > 300 * 1024) {
    ElMessage.warning('图片过大，请压缩至 300KB 以内');
    return;
  }

  try {
    const dataUrl = await readFileAsDataUrl(file);
    updateField('platform_logo', dataUrl);
  } catch {
    ElMessage.error('读取图片失败，请重试');
  }
};

const ldapExpanded = ref(false);
const ldapAdvanced = ref(false);

const toggleLdapExpanded = () => {
  ldapExpanded.value = !ldapExpanded.value;
  if (!ldapExpanded.value) ldapAdvanced.value = false;
};

const toggleLdapAdvanced = () => {
  ldapAdvanced.value = !ldapAdvanced.value;
};
</script>

<style scoped>
.settings-panels {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.panel {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  border-radius: 16px;
  border: 1px solid var(--oa-border-color);
  background: var(--oa-bg-panel);
  box-shadow: var(--oa-shadow-md);
}

.panel header h3 {
  margin: 0;
}

.panel header p {
  margin: 0.25rem 0 0;
  color: var(--oa-text-secondary);
}

.threshold-alert {
  margin-top: -6px;
}

.threshold-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.threshold-hint {
  margin-top: 4px;
  font-size: 12px;
  color: var(--oa-text-muted);
}

@media (max-width: 960px) {
  .threshold-grid {
    grid-template-columns: 1fr;
  }
}

.logo-field {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.logo-preview {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid var(--oa-border-color);
  background: var(--oa-bg-muted);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.logo-placeholder {
  font-size: 12px;
  color: var(--oa-text-muted);
}

.logo-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.logo-input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.logo-hint {
  font-size: 12px;
  color: var(--oa-text-muted);
}

.ldap-card {
  border-radius: 16px;
  border: 1px solid var(--oa-border-color);
  background: var(--oa-bg-muted);
  overflow: hidden;
}

.ldap-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 14px 16px;
}

.head-left {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.head-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.head-title .sub {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.head-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.summary-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.summary-item .label {
  color: var(--oa-text-muted);
}

.summary-item .value {
  color: var(--oa-text-primary);
}

.head-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ldap-card__body {
  border-top: 1px solid var(--oa-border-color);
  padding: 16px;
  background: var(--oa-bg-panel);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 14px;
}

.span-2 {
  grid-column: 1 / -1;
}

@media (max-width: 960px) {
  .ldap-card__head {
    flex-direction: column;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}

.advanced-toggle {
  margin-top: 8px;
}

.advanced-body {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--oa-border-color);
}
</style>
