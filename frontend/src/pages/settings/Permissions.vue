<template>
  <SettingsPageShell section-title="权限" body-padding="0" :panel-bordered="false">
    <template #actions>
      <div class="refresh-card" @click="loadRoles">
        <el-icon class="refresh-icon" :class="{ spinning: loading }"><Refresh /></el-icon>
        <span>刷新</span>
      </div>
    </template>

    <el-alert v-if="error" type="error" :closable="false" class="mb-2" show-icon>{{ error }}</el-alert>

    <div class="list-page">
      <div class="repository-filters">
        <div class="filters-left">
          <el-button class="toolbar-button toolbar-button--primary" type="primary" @click="handleCreate">
            新增角色模板
          </el-button>
        </div>
        <div class="filters-right">
          <el-input
            v-model="roleKeyword"
            placeholder="搜索角色名称 / 描述"
            clearable
            class="search-input pill-input search-input--compact"
          />
        </div>
      </div>

      <div class="repository-table">
        <div class="repository-table__card">
          <el-table
            v-loading="loading"
            :data="pagedRoles"
            height="100%"
            stripe
            empty-text="暂无角色"
            :header-cell-style="tableHeaderStyle"
            :cell-style="tableCellStyle"
          >
            <el-table-column prop="name" label="角色名称" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <button type="button" class="cell-link" @click="handleEdit(row)">
                  <strong class="cell-title">{{ row.name }}</strong>
                </button>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span>{{ row.description || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="权限" min-width="280">
              <template #default="{ row }">
                <div v-if="row.permissions?.length" class="perm-brief">
                  <span class="count">已选 {{ row.permissions.length }} 项</span>
                </div>
                <span v-else class="text-muted">未配置</span>
              </template>
            </el-table-column>
            <el-table-column prop="user_count" label="用户数" width="100" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <div class="row-actions">
                  <el-button type="primary" text size="small" @click="handleEdit(row)">编辑</el-button>
                  <el-button type="danger" text size="small" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="repository-table__footer">
        <div class="footer-left">
          <div class="repository-stats">共 {{ filteredRoles.length }} 条</div>
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
        <div class="footer-right">
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

import type { RolePayload } from '@/services/settingsApi';
import { deleteRole, fetchRoles } from '@/services/settingsApi';
import SettingsPageShell from './components/SettingsPageShell.vue';

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
  max-width: 360px;
}

.pill-input :deep(.el-input__wrapper) {
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
  /* justify-content: space-between; */
  gap: 16px;
  flex-wrap: wrap;
  padding: 0px 16px 12px;
  color: var(--oa-text-secondary);
  border-top: none;
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
