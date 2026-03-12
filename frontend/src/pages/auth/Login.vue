<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="login-hero" aria-hidden="true">
        <LoginIllustration class="login-hero__image" />
        <div class="login-hero__caption">
          <div class="login-hero__tagline">探针拨测与智能运维平台</div>
          <div class="login-hero__tags">
            <span class="login-tag">拨测</span>
            <span class="login-tag">监控</span>
            <span class="login-tag">工单</span>
          </div>
        </div>
      </section>

      <section class="login-panel">
        <el-card class="login-card" shadow="never">
          <div class="login-brand">
            <div class="login-brand__logo">
              <img v-if="branding.platformLogo" :src="branding.platformLogo" alt="logo">
              <div v-else class="logo-fallback">OA</div>
            </div>
            <div class="login-brand__text">
              <div class="login-brand__title">{{ branding.platformName }}</div>
              <div class="login-brand__subtitle">控制台登录</div>
            </div>
          </div>
          <div class="login-divider" />
          <h2 class="login-title">{{ t('auth.login') }}</h2>
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            class="login-form"
            hide-required-asterisk
            @submit.prevent="handleSubmit"
          >
            <el-form-item
              prop="username"
              :label="t('auth.username')"
              :show-message="showValidationMessages"
            >
              <el-input v-model="form.username" autocomplete="username" size="large">
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item
              prop="password"
              :label="t('auth.password')"
              :show-message="showValidationMessages"
            >
              <el-input
                v-model="form.password"
                type="password"
                autocomplete="current-password"
                show-password
                size="large"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-button
              class="login-submit"
              type="primary"
              :loading="session.loading"
              native-type="submit"
              size="large"
              block
            >
              {{ t('auth.login') }}
            </el-button>
          </el-form>
        </el-card>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { isAxiosError } from 'axios';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { Lock, User } from '@element-plus/icons-vue';
import { reactive, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';

import { useSessionStore } from '@/stores/session';
import { usePageTitle } from '@/composables/usePageTitle';
import { useBrandingStore } from '@/stores/branding';
import LoginIllustration from './LoginIllustration.vue';

type LoginForm = {
  username: string;
  password: string;
};

const session = useSessionStore();
const router = useRouter();
const route = useRoute();
const { t } = useI18n();
const branding = useBrandingStore();

const formRef = ref<FormInstance>();
const showValidationMessages = ref(false);
const form = reactive<LoginForm>({
  username: '',
  password: ''
});

const rules: FormRules = {
  username: [{ required: true, message: t('auth.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('auth.passwordRequired'), trigger: 'blur' }]
};

usePageTitle('auth.loginTitle', () => ({ app: branding.platformName }));

const resolveLoginErrorMessage = (err: unknown) => {
  if (isAxiosError(err)) {
    if (!err.response) return t('auth.backendUnavailable');
    if (err.response.status === 401) return t('auth.invalidCredentials');
    return (err.response.data as any)?.detail || err.message || t('auth.loginFailed');
  }
  if (err instanceof Error) return err.message;
  return t('auth.loginFailed');
};

const handleSubmit = async () => {
  showValidationMessages.value = true;
  const validateResult = await formRef.value?.validate().catch(() => false);
  if (validateResult === false) return;

  try {
    await session.login({ username: form.username.trim(), password: form.password });
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
    await router.replace(redirect);
  } catch (err) {
    ElMessage.error(resolveLoginErrorMessage(err));
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100dvh;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  overflow: hidden;
  background:
    radial-gradient(1000px circle at 12% 18%, rgba(37, 99, 235, 0.18), transparent 58%),
    radial-gradient(900px circle at 90% 80%, rgba(37, 99, 235, 0.12), transparent 60%),
    linear-gradient(180deg, var(--oa-bg-body), var(--oa-bg-muted));
}

.login-shell {
  width: min(1040px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 440px);
  align-items: center;
  gap: 24px;
}

.login-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  position: relative;
}

.login-hero::before {
  content: '';
  position: absolute;
  inset: -18px -12px;
  background:
    radial-gradient(520px circle at 50% 35%, rgba(37, 99, 235, 0.14), transparent 62%),
    radial-gradient(520px circle at 30% 78%, rgba(37, 99, 235, 0.10), transparent 60%);
  border-radius: 28px;
  pointer-events: none;
}

.login-hero__image {
  width: 100%;
  height: auto;
  filter: drop-shadow(0 18px 40px rgba(15, 23, 42, 0.18));
  position: relative;
}

.login-hero__caption {
  margin-top: 12px;
  text-align: center;
  position: relative;
}

.login-hero__tagline {
  margin-top: 2px;
  font-size: 13px;
  color: var(--oa-text-secondary);
}

.login-hero__tags {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: center;
}

.login-tag {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  color: var(--oa-color-primary);
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.18);
}

.login-panel {
  display: flex;
  justify-content: center;
}

.login-card {
  width: 100%;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.32) !important;
}

.login-card :deep(.el-card__body) {
  padding: 28px 28px 26px;
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.login-brand__logo {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(37, 99, 235, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(37, 99, 235, 0.18);
}

.login-brand__logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.logo-fallback {
  font-weight: 700;
  color: #1d4ed8;
  letter-spacing: 0.08em;
}

.login-brand__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.login-brand__title {
  font-size: 15px;
  font-weight: 700;
  color: var(--oa-text-primary);
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.login-brand__subtitle {
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.login-divider {
  height: 1px;
  background: rgba(148, 163, 184, 0.35);
  margin: 10px 0 16px;
}

.login-title {
  margin: 0 0 16px;
  font-size: 17px;
  line-height: 1.25;
  letter-spacing: -0.02em;
  color: var(--oa-text-primary);
}

.login-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.login-form :deep(.el-form-item__label) {
  padding-bottom: 6px;
  font-size: 13px;
  color: var(--oa-text-secondary);
}

.login-form :deep(.el-form-item:last-of-type) {
  margin-bottom: 18px;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 44px;
  border-radius: 10px;
  background: var(--oa-bg-panel);
  box-shadow: inset 0 0 0 1px var(--oa-border-color);
  transition: box-shadow 0.18s ease, transform 0.18s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: inset 0 0 0 1px var(--oa-border-color-dark);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: inset 0 0 0 2px rgba(37, 99, 235, 0.35);
}

.login-submit {
  height: 44px;
  border-radius: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.22);
  transition: box-shadow 0.18s ease, transform 0.18s ease, background-color 0.18s ease;
}

.login-submit:hover {
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.26);
  transform: translateY(-1px);
}

.login-submit:active {
  transform: translateY(0);
}

.login-submit.is-loading,
.login-submit:disabled {
  transform: none;
  box-shadow: none;
}

[data-theme='dark'] .login-submit {
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.35);
}

[data-theme='dark'] .login-page {
  background:
    radial-gradient(1000px circle at 12% 18%, rgba(59, 130, 246, 0.22), transparent 58%),
    radial-gradient(900px circle at 90% 80%, rgba(37, 99, 235, 0.16), transparent 60%),
    linear-gradient(180deg, var(--oa-bg-body), #0b1220);
}

@media (max-width: 960px) {
  .login-shell {
    grid-template-columns: 1fr;
    max-width: 440px;
  }

  .login-hero {
    display: none;
  }
}
</style>
