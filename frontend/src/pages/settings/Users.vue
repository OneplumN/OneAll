<template>
  <SettingsPageShell section-title="用户" body-padding="0" :panel-bordered="false">
    <template #actions>
      <el-button
        v-if="canSyncLdap"
        class="toolbar-button"
        type="primary"
        plain
        :loading="syncingLdap"
        @click="handleSyncLdap"
      >
        同步 LDAP 用户
      </el-button>
      <div class="refresh-card" @click="loadUsers">
        <el-icon class="refresh-icon" :class="{ spinning: loading }"><Refresh /></el-icon>
        <span>刷新</span>
      </div>
    </template>

    <el-alert v-if="error" type="error" :closable="false" class="mb-2" show-icon>{{ error }}</el-alert>

    <div class="list-page">
      <div class="repository-filters">
        <div class="filters-left">
          <el-button
            v-if="canManageUsers"
            class="toolbar-button toolbar-button--primary"
            type="primary"
            @click="openCreateDialog"
          >
            新增用户
          </el-button>
        </div>
        <div class="filters-right">
          <el-select v-model="authSourceFilter" class="pill-input narrow-select" placeholder="认证来源" clearable>
            <el-option label="本地" value="local" />
            <el-option label="LDAP" value="ldap" />
          </el-select>
          <el-select v-model="roleFilter" class="pill-input narrow-select" placeholder="角色模板" clearable filterable>
            <el-option label="未分配" value="__unassigned__" />
            <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
          <el-input
            v-model="userKeyword"
            placeholder="搜索账号 / 姓名"
            clearable
            class="search-input pill-input search-input--compact"
          />
        </div>
      </div>

      <div class="repository-table">
        <div class="repository-table__card">
          <el-table
            v-loading="loading"
            :data="pagedUsers"
            height="100%"
            stripe
            empty-text="暂无用户"
            :header-cell-style="tableHeaderStyle"
            :cell-style="tableCellStyle"
          >
            <el-table-column label="账号" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <button type="button" class="cell-link" @click="openRoleDrawer(row)">
                  <strong class="cell-title">{{ row.username }}</strong>
                </button>
              </template>
            </el-table-column>
            <el-table-column label="姓名" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span>{{ row.display_name || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="认证来源" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.auth_source === 'ldap'" size="small" effect="plain" type="info">LDAP</el-tag>
                <span v-else>本地</span>
              </template>
            </el-table-column>
            <el-table-column label="角色模板" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">
                <el-tag v-if="row.roles?.length" size="small" round>
                  {{ roleNameById[row.roles[0]] || '未知角色' }}
                </el-tag>
                <span v-else class="muted">未分配</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <div class="row-actions">
                  <div class="row-actions__left">
                    <el-button text size="small" @click="openRoleDrawer(row)">绑定角色</el-button>
                  </div>
                  <div class="row-actions__right">
                    <el-button
                      v-if="canManageUsers"
                      text
                      type="danger"
                      size="small"
                      :disabled="row.id === currentUserId || row.is_superuser"
                      @click="handleDeleteUser(row)"
                    >
                      删除
                    </el-button>
                  </div>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="repository-table__footer">
        <div class="footer-left">
          <div class="repository-stats">共 {{ filteredUsers.length }} 条</div>
          <el-pagination
            :total="filteredUsers.length"
            :current-page="currentPage"
            :page-size="pageSize"
            :page-sizes="pageSizeOptions"
            layout="sizes"
            background
            class="repository-pagination__sizes"
            :disabled="loading"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
        <div class="footer-right">
          <el-pagination
            class="repository-pagination__pager"
            :total="filteredUsers.length"
            :current-page="currentPage"
            :page-size="pageSize"
            layout="prev, pager, next"
            background
            :disabled="loading"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <el-drawer v-model="roleDrawerVisible" title="绑定角色模板" size="520px" append-to-body destroy-on-close>
      <div v-if="drawerUser" class="drawer-body">
        <div class="drawer-card">
          <div class="drawer-card__title">基本信息</div>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="账号">{{ drawerUser.username }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ drawerUser.email || '—' }}</el-descriptions-item>
            <el-descriptions-item label="认证来源">{{ drawerUser.auth_source || 'local' }}</el-descriptions-item>
            <el-descriptions-item label="LDAP 同步时间">
              {{ drawerUser.external_synced_at ? formatSyncTime(drawerUser.external_synced_at) : '—' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="drawer-card">
          <div class="drawer-card__title">角色模板</div>
          <div class="drawer-card__subtitle">每个用户仅可绑定一个角色模板，保存后立即生效。</div>
          <el-radio-group v-model="drawerRoleId" class="role-list">
            <el-radio :label="''" class="role-option">
              <div class="role-option__content">
                <div class="role-option__name">未分配</div>
                <div class="role-option__desc">不授予任何权限</div>
              </div>
            </el-radio>
            <el-radio v-for="role in roles" :key="role.id" :label="role.id" class="role-option">
              <div class="role-option__content">
                <div class="role-option__name">{{ role.name }}</div>
                <div class="role-option__desc">{{ role.description || '未提供描述' }}</div>
              </div>
            </el-radio>
          </el-radio-group>
        </div>
      </div>

      <template #footer>
        <div class="drawer-footer">
          <span v-if="drawerDirty" class="dirty-hint">未保存更改</span>
          <el-button @click="closeRoleDrawer">取消</el-button>
          <el-button type="primary" :disabled="!drawerDirty" :loading="saving" @click="saveDrawerRole">保存</el-button>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="createDialogVisible" title="新增本地用户" width="560px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="账号" required>
          <el-input v-model="createForm.username" placeholder="例如：zhangsan" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="createForm.display_name" placeholder="可选" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="createForm.email" placeholder="可选" />
        </el-form-item>
        <el-form-item label="初始角色模板">
          <el-select v-model="createForm.role_id" placeholder="未分配" clearable filterable style="width: 100%">
            <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" type="password" show-password placeholder="至少 8 位" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="creating" @click="submitCreate">创建</el-button>
        </div>
      </template>
    </el-dialog>
  </SettingsPageShell>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { computed, onMounted, ref } from 'vue';

import type { RolePayload, UserRoleRecord } from '@/services/settingsApi';
import { createLocalUser, deleteUser, fetchRoles, fetchUserRoles, syncLdapUsers, updateUserRoles } from '@/services/settingsApi';
import { useSessionStore } from '@/stores/session';
import SettingsPageShell from './components/SettingsPageShell.vue';

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

const loadUsers = async () => {
  loading.value = true;
  error.value = null;
  try {
    const [userData, roleData] = await Promise.all([fetchUserRoles(), fetchRoles()]);
    users.value = userData;
    roles.value = roleData;
  } catch (err) {
    error.value = '无法加载用户信息，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

const roleNameById = computed(() => Object.fromEntries(roles.value.map((role) => [role.id, role.name])));

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

const handlePageSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
};

const pagedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredUsers.value.slice(start, start + pageSize.value);
});

const formatSyncTime = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

const tableHeaderStyle = () => ({
  background: 'var(--oa-bg-muted)',
  color: 'var(--oa-text-secondary)',
  fontWeight: 600,
  height: '44px'
});

const tableCellStyle = () => ({
  height: '44px',
  padding: '6px 8px'
});

const roleDrawerVisible = ref(false);
const drawerUserId = ref<string | null>(null);
const drawerRoleId = ref('');

const createDialogVisible = ref(false);
const creating = ref(false);
const createForm = ref({
  username: '',
  display_name: '',
  email: '',
  role_id: null as string | null,
  password: '',
});

const drawerUser = computed(() => {
  if (!drawerUserId.value) return null;
  return users.value.find((item) => item.id === drawerUserId.value) || null;
});
const drawerOriginalRoleId = computed(() => drawerUser.value?.roles?.[0] ?? '');
const drawerDirty = computed(() => Boolean(drawerUser.value) && drawerRoleId.value !== drawerOriginalRoleId.value);

const openRoleDrawer = (user: UserRoleRecord) => {
  drawerUserId.value = user.id;
  drawerRoleId.value = user.roles?.[0] ?? '';
  roleDrawerVisible.value = true;
};

const closeRoleDrawer = () => {
  roleDrawerVisible.value = false;
};

const openCreateDialog = () => {
  createForm.value = {
    username: '',
    display_name: '',
    email: '',
    role_id: null,
    password: '',
  };
  createDialogVisible.value = true;
};

const submitCreate = async () => {
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
    const message = err?.response?.data?.detail || err?.response?.data?.username?.[0] || '创建失败，请稍后重试';
    ElMessage.error(message);
  } finally {
    creating.value = false;
  }
};

const handleDeleteUser = async (user: UserRoleRecord) => {
  if (!canManageUsers.value) return;
  if (user.id === currentUserId.value) {
    ElMessage.warning('不能删除当前登录用户');
    return;
  }
  try {
    await ElMessageBox.confirm(`确认删除用户 “${user.display_name || user.username}” 吗？该操作不可恢复。`, '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    });
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
};

const saveDrawerRole = async () => {
  if (!drawerUser.value || saving.value) return;
  saving.value = true;
  try {
    const payload = drawerRoleId.value ? [drawerRoleId.value] : [];
    const updated = await updateUserRoles(drawerUser.value.id, payload);
    users.value = users.value.map((item) => (item.id === updated.id ? updated : item));
    ElMessage.success('角色已更新');
    roleDrawerVisible.value = false;
  } catch (err) {
    ElMessage.error('保存失败，请稍后重试');
  } finally {
    saving.value = false;
  }
};

const handleSyncLdap = async () => {
  if (!canSyncLdap.value || syncingLdap.value) return;
  try {
    await ElMessageBox.confirm('立即同步 LDAP 用户？该操作可能持续数秒。', '同步确认', {
      type: 'warning'
    });
  } catch (err) {
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
};

onMounted(loadUsers);
</script>

<style scoped>
.mb-2 {
  margin-bottom: 1rem;
}

.list-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.repository-filters {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.filters-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filters-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 220px;
}

.search-input--compact {
  max-width: 320px;
}

.narrow-select {
  width: 180px;
}

.pill-input :deep(.el-input__wrapper),
.pill-input :deep(.el-select__wrapper) {
  border-radius: 999px;
  padding-left: 0.85rem;
  background: var(--oa-filter-control-bg);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}

.repository-table {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--oa-bg-panel);
  padding: 0 16px 12px;
}

.repository-table__card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: none;
}

.repository-table__card :deep(.el-table) {
  flex: 1;
  overflow-x: hidden;
}

.repository-table__card :deep(.el-table__inner-wrapper) {
  border: none !important;
}

.repository-table__card :deep(.el-table__cell) {
  padding: 8px 10px;
}

.repository-table__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 0px 16px 12px;
  color: var(--oa-text-secondary);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-right {
  margin-left: auto;
}

.repository-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.cell-title {
  font-weight: 600;
}

.cell-link {
  display: inline-flex;
  align-items: baseline;
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  color: inherit;
}

.cell-link:hover .cell-title {
  text-decoration: underline;
}

.row-actions {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.row-actions__left,
.row-actions__right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.08);
  cursor: pointer;
  user-select: none;
}

.refresh-card:hover {
  background: rgba(15, 23, 42, 0.06);
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

.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 2px;
}

.drawer-card {
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}

.drawer-card__title {
  font-weight: 700;
  color: var(--oa-text-primary);
  margin-bottom: 8px;
}

.drawer-card__subtitle {
  margin-top: -4px;
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.drawer-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.dirty-hint {
  margin-right: auto;
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.muted {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.sep {
  color: var(--oa-text-muted);
}

.role-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-option {
  width: 100%;
  margin-right: 0;
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  padding: 12px 12px;
  background: rgba(255, 255, 255, 0.7);
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.role-option:hover {
  border-color: rgba(64, 158, 255, 0.35);
  background: rgba(64, 158, 255, 0.05);
}

.role-option :deep(.el-radio__label) {
  width: 100%;
}

.role-option__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.role-option__name {
  font-weight: 600;
  color: var(--oa-text-primary);
}

.role-option__desc {
  font-size: 12px;
  color: var(--oa-text-secondary);
}
</style>
