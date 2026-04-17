import { ElMessage, ElMessageBox } from 'element-plus';
import { computed, onMounted, ref } from 'vue';

import type { RolePayload, UserRoleRecord } from '@/features/settings/api/settingsApi';
import {
  createLocalUser,
  deleteUser,
  fetchRoles,
  fetchUserRoles,
  syncLdapUsers,
  updateUserRoles,
} from '@/features/settings/api/settingsApi';
import { useSessionStore } from '@/app/stores/session';

type CreateUserForm = {
  username: string;
  display_name: string;
  email: string;
  role_id: string | null;
  password: string;
};

export function useUsersPage() {
  const users = ref<UserRoleRecord[]>([]);
  const roles = ref<RolePayload[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const syncingLdap = ref(false);
  const saving = ref(false);

  const sessionStore = useSessionStore();
  const canSyncLdap = computed(() => sessionStore.hasPermission('settings.users.manage'));
  const canManageUsers = computed(() => sessionStore.hasPermission('settings.users.manage'));
  const currentUserId = computed(() => sessionStore.user?.id ?? '');
  const userKeyword = ref('');
  const authSourceFilter = ref<'local' | 'ldap' | ''>('');
  const roleFilter = ref<string>('');

  async function loadUsers() {
    loading.value = true;
    error.value = null;
    try {
      const [userData, roleData] = await Promise.all([fetchUserRoles(), fetchRoles()]);
      users.value = userData;
      roles.value = roleData;
    } catch {
      error.value = '无法加载用户信息，请稍后重试。';
    } finally {
      loading.value = false;
    }
  }

  const roleNameById = computed(() =>
    Object.fromEntries(roles.value.map((role) => [role.id, role.name]))
  );

  const filteredUsers = computed(() => {
    const keyword = userKeyword.value.trim().toLowerCase();
    return users.value.filter((user) => {
      if (authSourceFilter.value) {
        const source = user.auth_source || 'local';
        if (source !== authSourceFilter.value) return false;
      }
      if (roleFilter.value) {
        if (roleFilter.value === '__unassigned__') {
          if (user.roles?.length) return false;
        } else if (user.roles?.[0] !== roleFilter.value) {
          return false;
        }
      }
      if (!keyword) return true;
      const haystack = `${user.display_name || ''} ${user.username} ${user.email || ''}`.toLowerCase();
      return haystack.includes(keyword);
    });
  });

  const pageSizeOptions = [10, 20, 50];
  const currentPage = ref(1);
  const pageSize = ref(20);

  function handlePageSizeChange(size: number) {
    pageSize.value = size;
    currentPage.value = 1;
  }

  function handlePageChange(page: number) {
    currentPage.value = page;
  }

  const pagedUsers = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value;
    return filteredUsers.value.slice(start, start + pageSize.value);
  });

  function formatSyncTime(value?: string | null) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  }

  const roleDrawerVisible = ref(false);
  const drawerUserId = ref<string | null>(null);
  const drawerRoleId = ref('');

  const createDialogVisible = ref(false);
  const creating = ref(false);
  const createForm = ref<CreateUserForm>({
    username: '',
    display_name: '',
    email: '',
    role_id: null,
    password: '',
  });

  const drawerUser = computed(() => {
    if (!drawerUserId.value) return null;
    return users.value.find((item) => item.id === drawerUserId.value) || null;
  });
  const drawerOriginalRoleId = computed(() => drawerUser.value?.roles?.[0] ?? '');
  const drawerDirty = computed(
    () => Boolean(drawerUser.value) && drawerRoleId.value !== drawerOriginalRoleId.value
  );

  function openRoleDrawer(user: UserRoleRecord) {
    drawerUserId.value = user.id;
    drawerRoleId.value = user.roles?.[0] ?? '';
    roleDrawerVisible.value = true;
  }

  function closeRoleDrawer() {
    roleDrawerVisible.value = false;
  }

  function openCreateDialog() {
    createForm.value = {
      username: '',
      display_name: '',
      email: '',
      role_id: null,
      password: '',
    };
    createDialogVisible.value = true;
  }

  async function submitCreate() {
    if (!canManageUsers.value || creating.value) return;
    const username = createForm.value.username.trim();
    const password = createForm.value.password;
    if (!username) {
      ElMessage.warning('请填写账号');
      return;
    }
    if (!password || password.length < 8) {
      ElMessage.warning('密码至少 8 位');
      return;
    }
    creating.value = true;
    try {
      await createLocalUser({
        username,
        display_name: createForm.value.display_name?.trim() || '',
        email: createForm.value.email?.trim() || '',
        password,
        role_id: createForm.value.role_id || null,
      });
      ElMessage.success('用户已创建');
      createDialogVisible.value = false;
      await loadUsers();
    } catch (err: any) {
      const message =
        err?.response?.data?.detail || err?.response?.data?.username?.[0] || '创建失败，请稍后重试';
      ElMessage.error(message);
    } finally {
      creating.value = false;
    }
  }

  async function handleDeleteUser(user: UserRoleRecord) {
    if (!canManageUsers.value) return;
    if (user.id === currentUserId.value) {
      ElMessage.warning('不能删除当前登录用户');
      return;
    }
    try {
      await ElMessageBox.confirm(
        `确认删除用户 “${user.display_name || user.username}” 吗？该操作不可恢复。`,
        '提示',
        {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
      );
    } catch {
      return;
    }

    try {
      await deleteUser(user.id);
      users.value = users.value.filter((item) => item.id !== user.id);
      if (drawerUserId.value === user.id) {
        roleDrawerVisible.value = false;
        drawerUserId.value = null;
      }
      if (currentPage.value > 1 && pagedUsers.value.length === 1) {
        currentPage.value = currentPage.value - 1;
      }
      ElMessage.success('用户已删除');
    } catch (err: any) {
      const message = err?.response?.data?.detail || '删除失败，请稍后重试';
      ElMessage.error(message);
    }
  }

  async function saveDrawerRole() {
    if (!drawerUser.value || saving.value) return;
    saving.value = true;
    try {
      const payload = drawerRoleId.value ? [drawerRoleId.value] : [];
      const updated = await updateUserRoles(drawerUser.value.id, payload);
      users.value = users.value.map((item) => (item.id === updated.id ? updated : item));
      ElMessage.success('角色已更新');
      roleDrawerVisible.value = false;
    } catch {
      ElMessage.error('保存失败，请稍后重试');
    } finally {
      saving.value = false;
    }
  }

  async function handleSyncLdap() {
    if (!canSyncLdap.value || syncingLdap.value) return;
    try {
      await ElMessageBox.confirm('立即同步 LDAP 用户？该操作可能持续数秒。', '同步确认', {
        type: 'warning',
      });
    } catch {
      return;
    }

    syncingLdap.value = true;
    try {
      const { result } = await syncLdapUsers();
      await loadUsers();
      ElMessage.success(`同步完成，共 ${result.total} 条，新增 ${result.created}，更新 ${result.updated}`);
    } catch (err: any) {
      const message = err?.response?.data?.detail || '同步失败，请稍后重试';
      ElMessage.error(message);
    } finally {
      syncingLdap.value = false;
    }
  }

  onMounted(loadUsers);

  return {
    users,
    roles,
    loading,
    error,
    syncingLdap,
    saving,
    canSyncLdap,
    canManageUsers,
    currentUserId,
    userKeyword,
    authSourceFilter,
    roleFilter,
    loadUsers,
    roleNameById,
    filteredUsers,
    pageSizeOptions,
    currentPage,
    pageSize,
    handlePageSizeChange,
    handlePageChange,
    pagedUsers,
    formatSyncTime,
    roleDrawerVisible,
    drawerRoleId,
    createDialogVisible,
    creating,
    createForm,
    drawerUser,
    drawerDirty,
    openRoleDrawer,
    closeRoleDrawer,
    openCreateDialog,
    submitCreate,
    handleDeleteUser,
    saveDrawerRole,
    handleSyncLdap,
  };
}
