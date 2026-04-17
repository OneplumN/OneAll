<template>
  <SettingsPageShell
    section-title="用户与权限"
    breadcrumb="角色模板"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <div
        class="refresh-card"
        @click="loadRoles"
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
            class="toolbar-button toolbar-button--primary"
            type="primary"
            @click="handleCreate"
          >
            新增角色模板
          </el-button>
        </div>
        <div class="page-toolbar__right">
          <el-input
            v-model="roleKeyword"
            placeholder="搜索角色名称 / 描述"
            clearable
            class="search-input pill-input search-input--compact"
          />
        </div>
      </div>

      <div class="oa-table-panel">
        <div class="oa-table-panel__card">
          <el-table
            v-loading="loading"
            :data="pagedRoles"
            class="oa-table"
            height="100%"
            stripe
            empty-text="暂无角色"
          >
            <el-table-column
              prop="name"
              label="角色名称"
              min-width="200"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <button
                  type="button"
                  class="oa-cell-link"
                  @click="handleEdit(row)"
                >
                  <strong class="oa-table-title">{{ row.name }}</strong>
                </button>
              </template>
            </el-table-column>
            <el-table-column
              prop="description"
              label="描述"
              min-width="200"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span>{{ row.description || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="权限"
              min-width="280"
            >
              <template #default="{ row }">
                <div
                  v-if="row.permissions?.length"
                  class="perm-brief"
                >
                  <span class="count">已选 {{ row.permissions.length }} 项</span>
                </div>
                <span
                  v-else
                  class="text-muted"
                >未配置</span>
              </template>
            </el-table-column>
            <el-table-column
              prop="user_count"
              label="用户数"
              width="100"
            />
            <el-table-column
              label="操作"
              width="200"
              fixed="right"
            >
              <template #default="{ row }">
                <div class="row-actions">
                  <el-button
                    type="primary"
                    text
                    size="small"
                    class="oa-table-action oa-table-action--success"
                    @click="handleEdit(row)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    type="danger"
                    text
                    size="small"
                    class="oa-table-action oa-table-action--danger"
                    @click="handleDelete(row)"
                  >
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="oa-panel-footer">
        <div class="oa-panel-footer__left">
          <div class="oa-panel-stats">
            共 {{ filteredRoles.length }} 条
          </div>
          <el-pagination
            :total="filteredRoles.length"
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
            :total="filteredRoles.length"
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
  </SettingsPageShell>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

import type { RolePayload } from '@/features/settings/api/settingsApi';
import { deleteRole, fetchRoles } from '@/features/settings/api/settingsApi';
import SettingsPageShell from '@/features/settings/components/SettingsPageShell.vue';

const router = useRouter();

const roles = ref<RolePayload[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const roleKeyword = ref('');

const filteredRoles = computed(() => {
  const keyword = roleKeyword.value.trim().toLowerCase();
  if (!keyword) return roles.value;
  return roles.value.filter((role) => `${role.name} ${role.description || ''}`.toLowerCase().includes(keyword));
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

const pagedRoles = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredRoles.value.slice(start, start + pageSize.value);
});

const loadRoles = async () => {
  loading.value = true;
  error.value = null;
  try {
    const roleData = await fetchRoles();
    roles.value = roleData;
  } catch (err) {
    error.value = '无法加载角色数据，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

const handleCreate = () => {
  router.push({ name: 'settings-permissions-new' });
};

const handleEdit = (role: RolePayload) => {
  router.push({ name: 'settings-permissions-detail', params: { roleId: String(role.id) } });
};

const handleDelete = async (role: RolePayload) => {
  try {
    await ElMessageBox.confirm(`确认删除角色 “${role.name}” 吗？`, '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    });
  } catch {
    return;
  }
  try {
    await deleteRole(role.id);
    roles.value = roles.value.filter((item) => item.id !== role.id);
    ElMessage.success('角色已删除');
  } catch (err) {
    ElMessage.error('删除失败，请稍后重试');
  }
};

watch(roleKeyword, () => {
  currentPage.value = 1;
});

watch(
  () => [filteredRoles.value.length, pageSize.value] as const,
  () => {
    const maxPage = Math.max(1, Math.ceil(filteredRoles.value.length / pageSize.value));
    if (currentPage.value > maxPage) currentPage.value = maxPage;
  }
);

onMounted(() => {
  loadRoles();
});

</script>

<style scoped>
.row-actions {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
}

.row-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.perm-brief {
  display: flex;
  align-items: center;
  gap: 8px;
}

.perm-brief .count {
  color: var(--el-text-color-regular);
}

.text-muted {
  color: var(--el-text-color-secondary);
}
</style>
