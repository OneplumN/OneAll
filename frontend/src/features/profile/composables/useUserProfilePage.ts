import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';

import { changeMyPassword, fetchMyProfile, updateMyProfile, type ProfileRecord } from '@/features/profile/api/profileApi';
import { useSessionStore } from '@/app/stores/session';

export function useUserProfilePage() {
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
    phone: '',
  });

  const passwordForm = reactive({
    current_password: '',
    new_password: '',
    confirm_new_password: '',
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
        },
      },
    ],
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

  const profileDisplayName = computed(
    () => profile.value?.display_name || profile.value?.username || '我的资料'
  );

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
        phone: form.phone || '',
      };
    } catch (error) {
      console.warn('Failed to load profile', error);
      ElMessage.error('加载个人资料失败');
    } finally {
      loading.value = false;
    }
  }

  async function saveProfile() {
    if (!profile.value || !isDirty.value) return;
    saving.value = true;
    try {
      const payload: Record<string, string> = {
        phone: form.phone || '',
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
        confirm_new_password: passwordForm.confirm_new_password,
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
    void loadProfile();
  });

  return {
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
  };
}
