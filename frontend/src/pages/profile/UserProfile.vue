<template>
  <RepositoryPageShell root-title="个人" section-title="我的资料">
    <template #actions>
      <el-button
        class="toolbar-button toolbar-button--primary"
        type="primary"
        :loading="saving"
        :disabled="!profile || !isDirty"
        @click="saveProfile"
      >
        保存修改
      </el-button>
      <el-button class="toolbar-button" :loading="loading" @click="loadProfile">刷新</el-button>
    </template>

    <div class="profile-page" v-loading="loading">
      <el-row class="profile-grid" :gutter="12">
        <el-col :xs="24" :lg="8">
          <el-card shadow="never" class="profile-sidebar">
            <div class="profile-hero profile-hero--sidebar">
              <el-avatar :size="52" class="profile-avatar">{{ avatarText }}</el-avatar>
              <div class="profile-hero__main">
                <div class="profile-name">{{ profileDisplayName }}</div>
                <div class="profile-sub">
                  <span v-if="profile?.username">账号：{{ profile.username }}</span>
                  <span class="dot">·</span>
                  <el-tag size="small" effect="plain">{{ authSourceLabel }}</el-tag>
                </div>
                <div class="profile-role">
                  <div class="meta-label">当前角色</div>
                  <el-tag size="small" effect="plain" type="info">{{ primaryRoleName }}</el-tag>
                </div>
              </div>
            </div>

            <el-divider />

            <div class="profile-quick profile-quick--stack">
              <div class="quick-item">
                <div class="quick-label">显示名称</div>
                <div class="quick-value">{{ profile?.display_name || '-' }}</div>
              </div>
              <div class="quick-item">
                <div class="quick-label">邮箱</div>
                <div class="quick-value">{{ profile?.email || '-' }}</div>
              </div>
              <div class="quick-item">
                <div class="quick-label">手机号</div>
                <div class="quick-value">{{ profile?.phone || '-' }}</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="16">
          <div class="profile-editor">
            <el-card shadow="never" class="profile-editor__card">
              <template #header>
                <div class="card-header">
                  <div class="card-header__title">资料维护</div>
                  <div class="card-header__desc">
                    <span v-if="isLdapUser">LDAP 账号默认仅允许修改手机号。</span>
                    <span v-else>更新显示名称、邮箱或手机号。</span>
                  </div>
                </div>
              </template>

              <el-form ref="formRef" :model="form" label-width="96px" @submit.prevent>
                <el-form-item label="账号">
                  <el-input :model-value="profile?.username || ''" disabled />
                </el-form-item>
                <el-form-item label="显示名称">
                  <el-input
                    v-model="form.display_name"
                    :disabled="!canEditDisplayName"
                    placeholder="例如：张三"
                  />
                  <div v-if="!canEditDisplayName" class="hint">LDAP 用户的显示名称由目录同步。</div>
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="form.email" :disabled="!canEditEmail" placeholder="name@example.com" />
                  <div v-if="!canEditEmail" class="hint">LDAP 用户的邮箱由目录同步。</div>
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="form.phone" placeholder="用于接收通知/联系" />
                </el-form-item>
              </el-form>
            </el-card>

            <el-card v-if="showPasswordSection" shadow="never" class="profile-editor__card">
              <template #header>
                <div class="card-header card-header--row">
                  <div class="card-header__left">
                    <div class="card-header__title">安全设置</div>
                    <div class="card-header__desc">仅本地账号可在平台内修改密码。</div>
                  </div>
                  <el-checkbox v-model="passwordVisible">明文显示</el-checkbox>
                </div>
              </template>

              <el-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                label-width="96px"
                @submit.prevent
              >
                <el-form-item label="当前密码" prop="current_password">
                  <el-input
                    v-model="passwordForm.current_password"
                    :type="passwordVisible ? 'text' : 'password'"
                    autocomplete="current-password"
                  />
                </el-form-item>
                <el-form-item label="新密码" prop="new_password">
                  <el-input
                    v-model="passwordForm.new_password"
                    :type="passwordVisible ? 'text' : 'password'"
                    autocomplete="new-password"
                    @input="scheduleValidateConfirmPassword"
                  />
                </el-form-item>
                <el-form-item label="确认新密码" prop="confirm_new_password">
                  <el-input
                    v-model="passwordForm.confirm_new_password"
                    :type="passwordVisible ? 'text' : 'password'"
                    autocomplete="new-password"
                    @input="scheduleValidateConfirmPassword"
                  />
                </el-form-item>
              </el-form>

              <template #footer>
                <div class="card-footer">
                  <el-button type="primary" :loading="changingPassword" @click="changePassword">
                    修改密码
                  </el-button>
                </div>
              </template>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';

import RepositoryPageShell from '@/components/RepositoryPageShell.vue';
import { changeMyPassword, fetchMyProfile, updateMyProfile, type ProfileRecord } from '@/services/profileApi';
import { useSessionStore } from '@/stores/session';

const sessionStore = useSessionStore();

const formRef = ref<FormInstance>();
const passwordFormRef = ref<FormInstance>();

const loading = ref(false);
const saving = ref(false);
const changingPassword = ref(false);
const profile = ref<ProfileRecord | null>(null);
const initialForm = ref({ display_name: '', email: '', phone: '' });

const form = reactive({
  display_name: '',
  email: '',
  phone: ''
});

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_new_password: ''
});
const passwordVisible = ref(false);

const passwordRules: FormRules = {
  current_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
  confirm_new_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      trigger: 'blur',
      validator: (_rule, value, callback) => {
        const text = String(value || '');
        if (!text) return callback();
        if (text !== String(passwordForm.new_password || '')) {
          callback(new Error('两次输入的新密码不一致'));
          return;
        }
        callback();
      }
    }
  ]
};

const isLdapUser = computed(() => (profile.value?.auth_source || 'local') === 'ldap');
const canEditDisplayName = computed(() => !isLdapUser.value);
const canEditEmail = computed(() => !isLdapUser.value);
const showPasswordSection = computed(() => !isLdapUser.value);

const isDirty = computed(() => {
  const initial = initialForm.value;
  if (canEditDisplayName.value && (form.display_name || '') !== (initial.display_name || '')) return true;
  if (canEditEmail.value && (form.email || '') !== (initial.email || '')) return true;
  return (form.phone || '') !== (initial.phone || '');
});

const authSourceLabel = computed(() => {
  const source = profile.value?.auth_source || 'local';
  if (source === 'ldap') return 'LDAP';
  return '本地';
});

const avatarText = computed(() => {
  const name = profile.value?.display_name || profile.value?.username || 'U';
  return name.slice(0, 1).toUpperCase();
});

const profileDisplayName = computed(() => profile.value?.display_name || profile.value?.username || '我的资料');

const primaryRoleName = computed(() => {
  const roles = profile.value?.roles || [];
  if (!roles.length) return '未分配';
  return roles[0];
});

let confirmValidateTimer: number | undefined;
function scheduleValidateConfirmPassword() {
  window.clearTimeout(confirmValidateTimer);
  confirmValidateTimer = window.setTimeout(() => {
    if (!passwordFormRef.value) return;
    passwordFormRef.value.validateField('confirm_new_password').catch(() => undefined);
  }, 120);
}

async function loadProfile() {
  loading.value = true;
  try {
    await sessionStore.fetchProfile();
    const data = (sessionStore.user as unknown as ProfileRecord) || (await fetchMyProfile());
    profile.value = data;
    form.display_name = data.display_name || '';
    form.email = data.email || '';
    form.phone = data.phone || '';
    initialForm.value = {
      display_name: form.display_name || '',
      email: form.email || '',
      phone: form.phone || ''
    };
  } catch (error) {
    console.warn('Failed to load profile', error);
    ElMessage.error('加载个人资料失败');
  } finally {
    loading.value = false;
  }
}

async function saveProfile() {
  if (!profile.value) return;
  if (!isDirty.value) return;
  saving.value = true;
  try {
    const payload: Record<string, string> = {
      phone: form.phone || ''
    };
    if (canEditDisplayName.value) payload.display_name = form.display_name || '';
    if (canEditEmail.value) payload.email = form.email || '';

    const updated = await updateMyProfile(payload);
    profile.value = updated;
    ElMessage.success('已保存');
    await loadProfile();
  } catch (error: any) {
    console.warn('Failed to update profile', error);
    const detail = error?.response?.data?.detail;
    ElMessage.error(typeof detail === 'string' ? detail : '保存失败，请稍后重试');
  } finally {
    saving.value = false;
  }
}

async function changePassword() {
  if (!passwordFormRef.value) return;
  try {
    await passwordFormRef.value.validate();
  } catch {
    return;
  }
  changingPassword.value = true;
  try {
    await changeMyPassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
      confirm_new_password: passwordForm.confirm_new_password
    });
    passwordForm.current_password = '';
    passwordForm.new_password = '';
    passwordForm.confirm_new_password = '';
    passwordFormRef.value?.clearValidate();
    ElMessage.success('密码已更新');
  } catch (error: any) {
    console.warn('Failed to change password', error);
    const detail = error?.response?.data?.detail;
    ElMessage.error(typeof detail === 'string' ? detail : '修改密码失败');
  } finally {
    changingPassword.value = false;
  }
}

onMounted(() => {
  loadProfile();
});
</script>

<style scoped>
.profile-page {
  padding: 16px;
}

.profile-grid {
  align-items: flex-start;
}

.profile-sidebar :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-editor__card {
  width: 100%;
  max-width: 880px;
}

.profile-editor__card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-editor__card :deep(.el-form) {
  max-width: 640px;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-header--row {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-header__left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.card-header__title {
  font-weight: 600;
  color: var(--oa-text-primary);
}

.card-header__desc {
  font-size: 12px;
  color: var(--oa-text-muted);
}

.profile-hero {
  display: flex;
  align-items: center;
  gap: 14px;
}

.profile-hero--sidebar {
  align-items: flex-start;
}

.profile-avatar {
  background: color-mix(in srgb, var(--oa-color-primary) 20%, var(--oa-bg-panel));
  color: var(--oa-color-primary);
  font-weight: 700;
}

.profile-hero__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.profile-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--oa-text-primary);
}

.profile-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--oa-text-secondary);
  flex-wrap: wrap;
}

.profile-sub .dot {
  color: var(--oa-text-muted);
}

.profile-role {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-label {
  font-size: 12px;
  color: var(--oa-text-muted);
}

.profile-quick {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.profile-quick--stack {
  grid-template-columns: 1fr;
}

.quick-item {
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  padding: 10px 12px;
  background: var(--oa-bg-muted);
  min-height: 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
}

.quick-item--clickable {
  cursor: pointer;
}

.quick-item--clickable:hover {
  border-color: var(--oa-color-primary-light);
  background: var(--oa-bg-hover);
  transform: translateY(-1px);
}

.quick-label {
  font-size: 12px;
  color: var(--oa-text-muted);
}

.quick-value {
  font-weight: 600;
  color: var(--oa-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}

.hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--oa-text-muted);
}

@media (max-width: 1200px) {
  .profile-page {
    padding: 12px;
  }
}
</style>
