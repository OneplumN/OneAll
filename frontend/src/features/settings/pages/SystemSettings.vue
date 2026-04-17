<template>
  <SettingsPageShell
    section-title="平台配置"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <div
        class="refresh-card"
        @click="loadSettings"
      >
        <el-icon
          class="refresh-icon"
          :class="{ spinning: loading }"
        >
          <Refresh />
        </el-icon>
        <span>刷新</span>
      </div>
    </template>

    <el-alert
      v-if="error"
      type="error"
      show-icon
      :closable="false"
      class="oa-inline-alert"
    >
      {{ error }}
    </el-alert>

    <div class="settings-config-page">
      <div class="settings-config-scroll">
        <section class="settings-section">
          <div class="settings-section__header">
            <div>
              <h3 class="settings-section__title">
                基础信息
              </h3>
              <p class="settings-section__subtitle">
                维护平台名称、品牌标识和默认展示配置。
              </p>
            </div>
          </div>
          <el-form
            label-position="top"
            class="settings-form"
          >
            <div class="settings-grid settings-grid--basic">
              <el-form-item
                label="平台名称"
                required
              >
                <el-input
                  v-model="form.platform_name"
                  placeholder="多维运维平台"
                />
              </el-form-item>
              <el-form-item label="默认时区">
                <el-select v-model="form.default_timezone">
                  <el-option
                    label="Asia/Shanghai"
                    value="Asia/Shanghai"
                  />
                  <el-option
                    label="UTC"
                    value="UTC"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="主题">
                <el-select v-model="form.theme">
                  <el-option
                    label="浅色"
                    value="light"
                  />
                  <el-option
                    label="深色"
                    value="dark"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="全局升级阈值（分钟）">
                <el-input-number
                  v-model="form.alert_escalation_threshold"
                  :min="1"
                  :controls="false"
                />
              </el-form-item>
            </div>

            <el-form-item label="平台 Logo">
              <div class="logo-field">
                <div class="logo-preview">
                  <img
                    v-if="form.platform_logo"
                    :src="form.platform_logo"
                    alt="logo"
                  >
                  <div
                    v-else
                    class="logo-placeholder"
                  >
                    暂无
                  </div>
                </div>
                <div class="logo-actions">
                  <input
                    ref="logoInputRef"
                    class="logo-input"
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    @change="handleLogoFileChange"
                  >
                  <div class="logo-actions__buttons">
                    <el-button
                      size="small"
                      @click="triggerLogoPick"
                    >
                      上传
                    </el-button>
                    <el-button
                      v-if="form.platform_logo"
                      size="small"
                      text
                      type="danger"
                      @click="form.platform_logo = ''"
                    >
                      清除
                    </el-button>
                  </div>
                  <div class="logo-hint">
                    建议 64x64，PNG/JPG/WebP，300KB 以内。
                  </div>
                </div>
              </div>
            </el-form-item>
          </el-form>
        </section>
      </div>
    </div>

    <template #footer>
      <div class="settings-footer">
        <el-button
          type="primary"
          :loading="saving"
          :disabled="loading"
          @click="saveSettings"
        >
          保存
        </el-button>
      </div>
    </template>
  </SettingsPageShell>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { onMounted, reactive, ref } from 'vue';

import {
  fetchSystemSettings,
  updateSystemSettings,
  type SystemSettingsForm,
  type SystemSettingsPayload,
} from '@/features/settings/api/settingsApi';
import { useBrandingStore } from '@/app/stores/branding';

import SettingsPageShell from '@/features/settings/components/SettingsPageShell.vue';
import { assignSystemSettings, buildIntegrationsPayload, createDefaultSystemSettings } from '@/features/settings/utils/systemSettings';

const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const branding = useBrandingStore();
const form = reactive<SystemSettingsForm>(createDefaultSystemSettings());
const logoInputRef = ref<HTMLInputElement | null>(null);

async function loadSettings() {
  loading.value = true;
  error.value = null;
  try {
    const data = await fetchSystemSettings();
    assignSystemSettings(form, data);
  } catch (err) {
    error.value = '无法加载平台配置，请稍后重试。';
  } finally {
    loading.value = false;
  }
}

async function saveSettings() {
  saving.value = true;
  error.value = null;
  try {
    const latest = await fetchSystemSettings();
    const payload: SystemSettingsPayload = {
      ...latest,
      platform_name: form.platform_name,
      platform_logo: form.platform_logo,
      default_timezone: form.default_timezone,
      alert_escalation_threshold: form.alert_escalation_threshold,
      theme: form.theme,
      integrations: buildIntegrationsPayload(latest.integrations),
    };

    const data = await updateSystemSettings(payload);
    assignSystemSettings(form, data);
    branding.applyBranding({
      platform_name: data.platform_name,
      platform_logo: data.platform_logo,
      theme: data.theme,
    });
    ElMessage.success('平台配置已保存');
  } catch (err) {
    error.value = '保存失败，请检查输入后重试。';
  } finally {
    saving.value = false;
  }
}

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
    form.platform_logo = await readFileAsDataUrl(file);
  } catch {
    ElMessage.error('读取图片失败，请重试');
  }
};

onMounted(loadSettings);
</script>

<style scoped>
@import '../styles/settings-config.scss';

.settings-grid {
  display: grid;
  gap: 16px;
}

.settings-grid--basic {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.logo-field {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-preview {
  width: 72px;
  height: 72px;
  border-radius: 14px;
  border: 1px dashed var(--oa-border-light);
  background: var(--oa-bg-body);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.logo-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.logo-placeholder {
  color: var(--oa-text-muted);
  font-size: var(--oa-font-body);
}

.logo-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.logo-actions__buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-hint,
.settings-hint {
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-subtitle);
}

.logo-input {
  display: none;
}

@media (max-width: 960px) {
  .settings-grid--basic {
    grid-template-columns: 1fr;
  }

  .logo-field {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
