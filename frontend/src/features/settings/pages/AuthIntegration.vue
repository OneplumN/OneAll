<template>
  <SettingsPageShell
    section-title="认证接入"
    breadcrumb="LDAP 接入"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <el-button
        class="toolbar-button"
        type="primary"
        plain
        :loading="syncingLdap"
        :disabled="!form.integrations.ldap.enabled"
        @click="triggerLdapSync"
      >
        同步 LDAP 用户
      </el-button>
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
                连接配置
              </h3>
              <p class="settings-section__subtitle">
                维护 LDAP 目录服务连接参数和默认角色映射。
              </p>
            </div>
            <el-switch
              v-model="form.integrations.ldap.enabled"
              inline-prompt
              active-text="启用"
              inactive-text="关闭"
            />
          </div>

          <el-form
            label-position="top"
            class="settings-form"
            :disabled="!form.integrations.ldap.enabled"
          >
            <div class="settings-grid settings-grid--two">
              <el-form-item label="LDAP 主机">
                <el-input
                  v-model="form.integrations.ldap.host"
                  placeholder="ldap.example.com"
                />
              </el-form-item>
              <el-form-item label="端口">
                <el-input-number
                  v-model="form.integrations.ldap.port"
                  :min="1"
                  :max="65535"
                  :controls="false"
                />
              </el-form-item>
              <el-form-item label="连接方式">
                <el-switch
                  v-model="form.integrations.ldap.use_ssl"
                  active-text="SSL"
                  inactive-text="明文"
                />
              </el-form-item>
              <el-form-item label="Base DN">
                <el-input
                  v-model="form.integrations.ldap.base_dn"
                  placeholder="dc=example,dc=com"
                />
              </el-form-item>
              <el-form-item label="Bind DN">
                <el-input
                  v-model="form.integrations.ldap.bind_dn"
                  placeholder="cn=sync,dc=example,dc=com"
                />
              </el-form-item>
              <el-form-item label="Bind 密码">
                <el-input
                  v-model="form.integrations.ldap.bind_password"
                  type="password"
                  show-password
                  placeholder="留空保持原值"
                />
              </el-form-item>
              <el-form-item
                label="默认角色"
                class="settings-grid-span-2"
              >
                <el-select
                  v-model="form.integrations.ldap.default_role_ids"
                  multiple
                  collapse-tags
                  filterable
                  :loading="roleOptionsLoading"
                  placeholder="选择同步后自动绑定的角色模板"
                >
                  <el-option
                    v-for="role in roleOptions"
                    :key="role.value"
                    :label="role.label"
                    :value="role.value"
                  />
                </el-select>
              </el-form-item>
            </div>
          </el-form>
        </section>

        <section class="settings-section">
          <div class="settings-section__header">
            <div>
              <h3 class="settings-section__title">
                目录字段映射
              </h3>
              <p class="settings-section__subtitle">
                定义登录查询、用户同步和属性字段的取值方式。
              </p>
            </div>
          </div>

          <el-form
            label-position="top"
            class="settings-form"
            :disabled="!form.integrations.ldap.enabled"
          >
            <div class="settings-grid settings-grid--two">
              <el-form-item label="用户过滤器">
                <el-input
                  v-model="form.integrations.ldap.user_filter"
                  placeholder="(uid={username})"
                />
              </el-form-item>
              <el-form-item label="同步过滤器">
                <el-input
                  v-model="form.integrations.ldap.sync_filter"
                  placeholder="(uid=*)"
                />
              </el-form-item>
              <el-form-item label="用户名属性">
                <el-input
                  v-model="form.integrations.ldap.username_attr"
                  placeholder="uid"
                />
              </el-form-item>
              <el-form-item label="姓名属性">
                <el-input
                  v-model="form.integrations.ldap.display_name_attr"
                  placeholder="cn"
                />
              </el-form-item>
              <el-form-item label="邮箱属性">
                <el-input
                  v-model="form.integrations.ldap.email_attr"
                  placeholder="mail"
                />
              </el-form-item>
              <el-form-item label="同步上限">
                <el-input-number
                  v-model="syncSizeLimitProxy"
                  :min="1"
                  :controls="false"
                  placeholder="不限制"
                />
              </el-form-item>
            </div>
          </el-form>
        </section>
      </div>
    </div>

    <template #footer>
      <div class="settings-footer">
        <el-button
          type="primary"
          :loading="saving"
          @click="saveSettings"
        >
          保存
        </el-button>
      </div>
    </template>
  </SettingsPageShell>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { computed, onMounted, reactive, ref } from 'vue';

import {
  fetchRoles,
  fetchSystemSettings,
  syncLdapUsers,
  updateSystemSettings,
  type SystemSettingsForm,
  type SystemSettingsPayload,
} from '@/features/settings/api/settingsApi';

import SettingsPageShell from '@/features/settings/components/SettingsPageShell.vue';
import { assignSystemSettings, buildIntegrationsPayload, createDefaultSystemSettings } from '@/features/settings/utils/systemSettings';

type RoleOption = { label: string; value: string };

const loading = ref(false);
const saving = ref(false);
const syncingLdap = ref(false);
const error = ref<string | null>(null);
const roleOptions = ref<RoleOption[]>([]);
const roleOptionsLoading = ref(false);
const form = reactive<SystemSettingsForm>(createDefaultSystemSettings());

const syncSizeLimitProxy = computed<number | undefined>({
  get: () => form.integrations.ldap.sync_size_limit ?? undefined,
  set: (value) => {
    form.integrations.ldap.sync_size_limit = typeof value === 'number' ? value : null;
  },
});

async function loadSettings() {
  loading.value = true;
  error.value = null;
  try {
    const data = await fetchSystemSettings();
    assignSystemSettings(form, data);
  } catch (err) {
    error.value = '无法加载认证接入配置，请稍后重试。';
  } finally {
    loading.value = false;
  }
}

async function loadRoleOptions() {
  roleOptionsLoading.value = true;
  try {
    const roles = await fetchRoles();
    roleOptions.value = roles.map((role) => ({ label: role.name, value: role.id }));
  } catch {
    roleOptions.value = [];
  } finally {
    roleOptionsLoading.value = false;
  }
}

async function saveSettings() {
  saving.value = true;
  error.value = null;
  try {
    const latest = await fetchSystemSettings();
    assignSystemSettings(latest, {
      integrations: {
        ldap: form.integrations.ldap,
      },
    });
    const payload: SystemSettingsPayload = {
      ...latest,
      integrations: buildIntegrationsPayload(latest.integrations),
    };
    const data = await updateSystemSettings(payload);
    assignSystemSettings(form, data);
    ElMessage.success('认证接入配置已保存');
  } catch (err) {
    error.value = '保存失败，请检查配置后重试。';
  } finally {
    saving.value = false;
  }
}

async function triggerLdapSync() {
  if (!form.integrations.ldap.enabled) {
    ElMessage.warning('请先启用 LDAP 并保存连接配置');
    return;
  }

  try {
    await ElMessageBox.confirm('立即同步 LDAP 用户？该操作可能持续数秒。', '同步确认', {
      type: 'warning',
    });
  } catch {
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

onMounted(() => {
  loadSettings();
  loadRoleOptions();
});
</script>

<style scoped>
@import '../styles/settings-config.scss';

.settings-grid-span-2 {
  grid-column: 1 / -1;
}

@media (max-width: 960px) {
  .settings-grid-span-2 {
    grid-column: auto;
  }
}
</style>
