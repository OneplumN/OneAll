<template>
  <SettingsPageShell
    section-title="用户与权限"
    breadcrumb="用户管理"
    body-padding="0"
    :panel-bordered="false"
  >
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
      <div
        class="refresh-card"
        @click="loadUsers"
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
      :closable="false"
      class="oa-inline-alert"
      show-icon
    >
      {{ error }}
    </el-alert>

    <div class="oa-list-page">
      <div class="page-toolbar page-toolbar--panel">
        <div class="page-toolbar__left">
          <el-button
            v-if="canManageUsers"
            class="toolbar-button toolbar-button--primary"
            type="primary"
            @click="openCreateDialog"
          >
            新增用户
          </el-button>
        </div>
        <div class="page-toolbar__right">
          <el-select
            v-model="authSourceFilter"
            class="pill-input narrow-select"
            placeholder="认证来源"
            clearable
          >
            <el-option
              label="本地"
              value="local"
            />
            <el-option
              label="LDAP"
              value="ldap"
            />
          </el-select>
          <el-select
            v-model="roleFilter"
            class="pill-input narrow-select"
            placeholder="角色模板"
            clearable
            filterable
          >
            <el-option
              label="未分配"
              value="__unassigned__"
            />
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
          <el-input
            v-model="userKeyword"
            placeholder="搜索账号 / 姓名"
            clearable
            class="search-input pill-input search-input--compact"
          />
        </div>
      </div>

      <div class="oa-table-panel">
        <div class="oa-table-panel__card">
          <el-table
            v-loading="loading"
            :data="pagedUsers"
            class="oa-table"
            height="100%"
            stripe
            empty-text="暂无用户"
          >
            <el-table-column
              label="账号"
              min-width="180"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <button
                  type="button"
                  class="oa-cell-link"
                  @click="openRoleDrawer(row)"
                >
                  <strong class="oa-table-title">{{ row.username }}</strong>
                </button>
              </template>
            </el-table-column>
            <el-table-column
              label="姓名"
              min-width="180"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span>{{ row.display_name || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="认证来源"
              width="120"
            >
              <template #default="{ row }">
                <el-tag
                  v-if="row.auth_source === 'ldap'"
                  size="small"
                  effect="plain"
                  type="info"
                >
                  LDAP
                </el-tag>
                <span v-else>本地</span>
              </template>
            </el-table-column>
            <el-table-column
              label="角色模板"
              min-width="160"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <el-tag
                  v-if="row.roles?.length"
                  size="small"
                  round
                >
                  {{ roleNameById[row.roles[0]] || '未知角色' }}
                </el-tag>
                <span
                  v-else
                  class="oa-table-meta"
                >未分配</span>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="200"
              fixed="right"
            >
              <template #default="{ row }">
                <div class="row-actions">
                  <div class="row-actions__left">
                    <el-button
                      text
                      size="small"
                      class="oa-table-action oa-table-action--primary"
                      @click="openRoleDrawer(row)"
                    >
                      绑定角色
                    </el-button>
                  </div>
                  <div class="row-actions__right">
                    <el-button
                      v-if="canManageUsers"
                      text
                      size="small"
                      class="oa-table-action oa-table-action--danger"
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

      <div class="oa-panel-footer">
        <div class="oa-panel-footer__left">
          <div class="oa-panel-stats">
            共 {{ filteredUsers.length }} 条
          </div>
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
        <div class="oa-panel-footer__right">
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

    <UserRoleDrawer
      v-model:visible="roleDrawerVisible"
      v-model:role-id="drawerRoleId"
      :user="drawerUser"
      :roles="roles"
      :dirty="drawerDirty"
      :saving="saving"
      :format-sync-time="formatSyncTime"
      @cancel="closeRoleDrawer"
      @save="saveDrawerRole"
    />

    <CreateUserDialog
      v-model:visible="createDialogVisible"
      v-model:form="createForm"
      :roles="roles"
      :loading="creating"
      @submit="submitCreate"
    />
  </SettingsPageShell>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue';

import CreateUserDialog from '@/features/settings/components/CreateUserDialog.vue';
import SettingsPageShell from '@/features/settings/components/SettingsPageShell.vue';
import UserRoleDrawer from '@/features/settings/components/UserRoleDrawer.vue';
import { useUsersPage } from '@/features/settings/composables/useUsersPage';

const {
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
} = useUsersPage();
</script>

<style scoped>
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

.sep {
  color: var(--oa-text-muted);
}
</style>
