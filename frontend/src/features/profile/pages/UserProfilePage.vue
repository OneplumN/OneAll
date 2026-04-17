<template>
  <RepositoryPageShell
    root-title="个人"
    section-title="我的资料"
    body-padding="0"
    :panel-bordered="false"
  >
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
      <div
        class="refresh-card"
        @click="loadProfile"
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

    <div
      v-loading="loading"
      class="profile-page"
    >
      <el-row
        class="profile-grid"
        :gutter="12"
      >
        <el-col
          :xs="24"
          :lg="8"
        >
          <UserProfileSidebar
            :profile="profile"
            :avatar-text="avatarText"
            :profile-display-name="profileDisplayName"
            :auth-source-label="authSourceLabel"
            :primary-role-name="primaryRoleName"
          />
        </el-col>

        <el-col
          :xs="24"
          :lg="16"
        >
          <div class="profile-editor">
            <el-card
              shadow="never"
              class="profile-editor__card"
            >
              <template #header>
                <div class="card-header">
                  <div class="card-header__title">
                    资料维护
                  </div>
                  <div class="card-header__desc">
                    <span v-if="isLdapUser">LDAP 账号默认仅允许修改手机号。</span>
                    <span v-else>更新显示名称、邮箱或手机号。</span>
                  </div>
                </div>
              </template>

              <el-form
                ref="formRef"
                :model="form"
                label-width="96px"
                @submit.prevent
              >
                <el-form-item label="账号">
                  <el-input
                    :model-value="profile?.username || ''"
                    disabled
                  />
                </el-form-item>
                <el-form-item label="显示名称">
                  <el-input
                    v-model="form.display_name"
                    :disabled="!canEditDisplayName"
                    placeholder="例如：张三"
                  />
                  <div
                    v-if="!canEditDisplayName"
                    class="hint"
                  >
                    LDAP 用户的显示名称由目录同步。
                  </div>
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input
                    v-model="form.email"
                    :disabled="!canEditEmail"
                    placeholder="name@example.com"
                  />
                  <div
                    v-if="!canEditEmail"
                    class="hint"
                  >
                    LDAP 用户的邮箱由目录同步。
                  </div>
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input
                    v-model="form.phone"
                    placeholder="用于接收通知/联系"
                  />
                </el-form-item>
              </el-form>
            </el-card>

            <UserProfilePasswordCard
              v-model:password-visible="passwordVisible"
              v-model:form-ref="passwordFormRef"
              v-model:password-form="passwordForm"
              :show-password-section="showPasswordSection"
              :password-rules="passwordRules"
              :changing-password="changingPassword"
              @schedule-validate="scheduleValidateConfirmPassword"
              @change-password="changePassword"
            />
          </div>
        </el-col>
      </el-row>
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue';

import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import UserProfileSidebar from '@/features/profile/components/UserProfileSidebar.vue';
import UserProfilePasswordCard from '@/features/profile/components/UserProfilePasswordCard.vue';
import { useUserProfilePage } from '@/features/profile/composables/useUserProfilePage';

const {
  formRef,
  passwordFormRef,
  loading,
  saving,
  changingPassword,
  profile,
  form,
  passwordForm,
  passwordVisible,
  passwordRules,
  isLdapUser,
  canEditDisplayName,
  canEditEmail,
  showPasswordSection,
  isDirty,
  authSourceLabel,
  avatarText,
  profileDisplayName,
  primaryRoleName,
  scheduleValidateConfirmPassword,
  loadProfile,
  saveProfile,
  changePassword,
} = useUserProfilePage();
</script>

<style scoped>
.profile-page {
  padding: var(--oa-spacing-md);
}

.profile-grid {
  align-items: flex-start;
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

.hint {
  margin-top: 6px;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-muted);
}

@media (max-width: 1200px) {
  .profile-page {
    padding: 12px;
  }
}
</style>
