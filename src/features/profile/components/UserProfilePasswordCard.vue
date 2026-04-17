<template>
  <el-card
    v-if="showPasswordSection"
    shadow="never"
    class="profile-editor__card"
  >
    <template #header>
      <div class="card-header card-header--row">
        <div class="card-header__left">
          <div class="card-header__title">
            安全设置
          </div>
          <div class="card-header__desc">
            仅本地账号可在平台内修改密码。
          </div>
        </div>
        <el-checkbox v-model="passwordVisibleModel">
          明文显示
        </el-checkbox>
      </div>
    </template>

    <el-form
      ref="passwordFormRef"
      :model="passwordFormModel"
      :rules="passwordRules"
      label-width="96px"
      @submit.prevent
    >
      <el-form-item
        label="当前密码"
        prop="current_password"
      >
        <el-input
          v-model="passwordFormModel.current_password"
          :type="passwordVisibleModel ? 'text' : 'password'"
          autocomplete="current-password"
        />
      </el-form-item>
      <el-form-item
        label="新密码"
        prop="new_password"
      >
        <el-input
          v-model="passwordFormModel.new_password"
          :type="passwordVisibleModel ? 'text' : 'password'"
          autocomplete="new-password"
          @input="emit('scheduleValidate')"
        />
      </el-form-item>
      <el-form-item
        label="确认新密码"
        prop="confirm_new_password"
      >
        <el-input
          v-model="passwordFormModel.confirm_new_password"
          :type="passwordVisibleModel ? 'text' : 'password'"
          autocomplete="new-password"
          @input="emit('scheduleValidate')"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="card-footer">
        <el-button
          type="primary"
          :loading="changingPassword"
          @click="emit('changePassword')"
        >
          修改密码
        </el-button>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus';

type PasswordForm = {
  current_password: string;
  new_password: string;
  confirm_new_password: string;
};

defineProps<{
  showPasswordSection: boolean;
  passwordRules: FormRules;
  changingPassword: boolean;
}>();

const passwordVisibleModel = defineModel<boolean>('passwordVisible', { required: true });
const passwordFormRef = defineModel<FormInstance | undefined>('formRef', { required: true });
const passwordFormModel = defineModel<PasswordForm>('passwordForm', { required: true });

const emit = defineEmits<{
  (event: 'scheduleValidate'): void;
  (event: 'changePassword'): void;
}>();
</script>

<style scoped>
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
  font-size: var(--oa-font-meta);
  color: var(--oa-text-muted);
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
