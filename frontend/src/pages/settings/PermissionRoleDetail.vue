<template>
  <div class="permission-role-detail-view">
    <SettingsPageShell section-title="权限" :breadcrumb="breadcrumb" body-padding="0" :panel-bordered="false">
      <template #actions>
        <el-button class="toolbar-button" @click="goBack">返回</el-button>
        <div class="refresh-card" @click="reloadAll">
          <el-icon class="refresh-icon" :class="{ spinning: loading }"><Refresh /></el-icon>
          <span>刷新</span>
        </div>
      </template>

      <el-alert v-if="error" type="error" :closable="false" class="mb-2" show-icon>{{ error }}</el-alert>

      <div class="detail-page">
        <div class="detail-head">
          <div class="head-left">
            <div class="head-title">{{ isCreate ? '新增角色模板' : originalRole?.name || '角色模板' }}</div>
            <div class="head-sub muted">
              <span v-if="!isCreate">用户数 {{ originalRole?.user_count ?? 0 }}</span>
              <span v-if="!isCreate" class="sep">·</span>
              <span>勾选权限后保存生效</span>
              <span v-if="dirty" class="sep">·</span>
              <span v-if="dirty" class="dirty-hint">未保存更改</span>
            </div>
          </div>
          <div class="head-actions">
            <el-button v-if="!isCreate && originalRole" :disabled="saving || !dirty" @click="handleReset">重置</el-button>
            <el-button v-if="!isCreate && originalRole" type="danger" plain :loading="deleting" @click="handleDelete">删除</el-button>
            <el-button type="primary" :disabled="!dirty" :loading="saving" @click="handleSave">保存</el-button>
          </div>
        </div>

        <div class="detail-scroll">
          <div class="detail-grid">
            <el-card shadow="never" class="card">
              <div class="card-title">基本信息</div>
              <div class="card-subtitle">用于展示与检索角色模板。</div>
              <el-form label-position="top" class="mt-12">
                <el-form-item label="名称" required>
                  <el-input v-model="form.name" placeholder="例如：运维管理员" />
                </el-form-item>
                <el-form-item label="描述">
                  <el-input v-model="form.description" placeholder="可选" />
                </el-form-item>
              </el-form>
            </el-card>

            <el-card shadow="never" class="card">
              <div class="perm-head">
                <div>
                  <div class="card-title">功能权限</div>
                  <div class="card-subtitle">模块可全选/全清；支持搜索与展开折叠。</div>
                </div>
                <div class="perm-head__right">
                  <el-input v-model="search" placeholder="搜索模块或动作" clearable @input="handleSearchInput">
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                </div>
              </div>

              <div class="perm-toolbar">
                <div class="toolbar-left">
                  <strong>权限目录</strong>
                </div>
                <div class="toolbar-actions">
                  <el-button size="small" text @click="setAllModulesExpansion(true)">全部展开</el-button>
                  <el-divider direction="vertical" />
                  <el-button size="small" text @click="setAllModulesExpansion(false)">全部折叠</el-button>
                </div>
              </div>

              <el-tree
                :key="treeRenderKey"
                class="perm-tree"
                :data="filteredTreeData"
                :props="treeProps"
                node-key="id"
                :default-expanded-keys="expandedKeys"
                :expand-on-click-node="false"
              >
                <template #default="{ data }">
                  <div class="node-row" :class="{ 'is-leaf': data.actions }">
                    <template v-if="!data.actions">
                      <strong class="module-title">{{ data.label }}</strong>
                      <div class="module-actions">
                        <el-button text size="small" @click.stop="toggleModule(data.moduleKey, true)">全选</el-button>
                        <el-button text size="small" @click.stop="toggleModule(data.moduleKey, false)">全清</el-button>
                      </div>
                    </template>
                    <template v-else>
                      <span class="child-label">{{ data.label }}</span>
                      <div class="action-group">
                        <el-checkbox
                          v-for="action in data.actions"
                          :key="action"
                          :label="formatActionLabel(action)"
                          :model-value="isChecked(data.moduleKey, data.childKey, action)"
                          @change="handleCheckboxChange(data.moduleKey, data.childKey, action, $event as boolean)"
                        />
                      </div>
                    </template>
                  </div>
                </template>
              </el-tree>
            </el-card>
          </div>
        </div>
      </div>
    </SettingsPageShell>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh, Search } from '@element-plus/icons-vue';
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router';

import type { PermissionModule, RoleInput, RolePayload } from '@/services/settingsApi';
import { createRole, deleteRole, fetchPermissionCatalog, fetchRoles, updateRole } from '@/services/settingsApi';
import SettingsPageShell from './components/SettingsPageShell.vue';

interface PermissionTreeNode {
  id: string;
  label: string;
  moduleKey: string;
  childKey?: string;
  actions?: string[];
  children?: PermissionTreeNode[];
}

const route = useRoute();
const router = useRouter();

const isCreate = computed(() => route.name === 'settings-permissions-new');
const roleId = computed(() => String(route.params.roleId || ''));

const loading = ref(false);
const saving = ref(false);
const deleting = ref(false);
const error = ref<string | null>(null);

const originalRole = ref<RolePayload | null>(null);
const form = reactive({
  name: '',
  description: '',
  permissions: [] as string[],
});

const permissionCatalog = ref<PermissionModule[]>([]);
const treeData = ref<PermissionTreeNode[]>([]);
const treeRenderKey = ref(0);
const expandedKeys = ref<string[]>([]);
const search = ref('');
const treeProps = { children: 'children' };

const breadcrumb = computed(() => {
  if (isCreate.value) return '新增角色模板';
  return originalRole.value?.name || '';
});

const normalizePermissions = (perms: string[]) => Array.from(new Set(perms)).sort();
const dirty = computed(() => {
  if (isCreate.value) {
    return Boolean(form.name.trim() || form.description.trim() || form.permissions.length);
  }
  if (!originalRole.value) return false;
  const nameChanged = form.name !== originalRole.value.name;
  const descChanged = (form.description || '') !== (originalRole.value.description || '');
  const permsChanged =
    JSON.stringify(normalizePermissions(form.permissions)) !==
    JSON.stringify(normalizePermissions(originalRole.value.permissions || []));
  return nameChanged || descChanged || permsChanged;
});

const ACTION_LABELS: Record<string, string> = {
  access: '模块访问',
  view: '查看',
  manage: '管理',
  manage_templates: '模板管理',
  execute: '执行',
  submit: '提交',
  approve: '审批',
  create: '创建',
  update: '更新',
  delete: '删除',
  rotate_token: '轮换令牌',
  sync: '同步',
  export: '导出',
  schedule: '调度',
  execute_script: '脚本执行',
  commit: '提交',
  rollback: '回滚',
  review: '审核',
  toggle: '启停',
  configure: '配置',
  assign_roles: '分配角色',
  test: '测试',
  submit_request: '提交申请',
  approve_request: '审批申请',
};

const formatActionLabel = (action: string) => ACTION_LABELS[action] ?? action.replace(/_/g, ' ').toUpperCase();

const buildTree = () => {
  treeData.value = permissionCatalog.value.map((module) => ({
    id: module.key,
    label: module.label,
    moduleKey: module.key,
    children:
      module.children?.map((child) => ({
        id: `${module.key}.${child.key}`,
        label: child.label,
        moduleKey: module.key,
        childKey: child.key,
        actions: child.actions,
      })) ?? [],
  }));
  setExpandedKeys(treeData.value.map((node) => node.id));
};

const filteredTreeData = computed<PermissionTreeNode[]>(() => {
  const keyword = search.value.trim().toLowerCase();
  if (!keyword) return treeData.value;
  return treeData.value
    .map((module) => {
      const moduleMatch = module.label.toLowerCase().includes(keyword);
      const children = module.children
        ?.map((child) => {
          const childMatch = child.label.toLowerCase().includes(keyword);
          const actionMatches = child.actions?.filter((action) => formatActionLabel(action).toLowerCase().includes(keyword));
          if (moduleMatch || childMatch) return { ...child };
          if (actionMatches && actionMatches.length) return { ...child, actions: actionMatches };
          return null;
        })
        .filter(Boolean) as PermissionTreeNode[];
      if (moduleMatch) return { ...module, children: module.children?.map((child) => ({ ...child })) ?? [] };
      if (children && children.length) return { ...module, children };
      return null;
    })
    .filter(Boolean) as PermissionTreeNode[];
});

const setExpandedKeys = (keys: string[]) => {
  expandedKeys.value = Array.from(new Set(keys));
  treeRenderKey.value += 1;
};

const updateExpansionForFilter = () => {
  if (search.value.trim()) {
    setExpandedKeys(filteredTreeData.value.map((node) => node.id));
  } else {
    setExpandedKeys(treeData.value.map((node) => node.id));
  }
};

const handleSearchInput = () => {
  updateExpansionForFilter();
};

const setAllModulesExpansion = (expand: boolean) => {
  if (expand) setExpandedKeys(treeData.value.map((node) => node.id));
  else setExpandedKeys([]);
};

const addPermission = (perm: string) => {
  if (!form.permissions.includes(perm)) form.permissions.push(perm);
};

const removePermission = (perm: string) => {
  form.permissions = form.permissions.filter((item) => item !== perm);
};

const reconcileModuleAccess = (moduleKey: string | undefined) => {
  if (!moduleKey) return;
  const modulePerm = `${moduleKey}.module.access`;
  const prefix = `${moduleKey}.`;
  const hasOther = form.permissions.some((perm) => perm.startsWith(prefix) && perm !== modulePerm);
  if (!hasOther) removePermission(modulePerm);
};

const ensureModuleAccess = (moduleKey: string | undefined) => {
  if (!moduleKey) return;
  addPermission(`${moduleKey}.module.access`);
};

const togglePermission = (moduleKey: string | undefined, childKey: string | undefined, action: string, checked: boolean) => {
  if (!moduleKey || !childKey) return;
  const perm = `${moduleKey}.${childKey}.${action}`;
  if (checked) {
    addPermission(perm);
    if (!(childKey === 'module' && action === 'access')) ensureModuleAccess(moduleKey);
  } else {
    removePermission(perm);
    reconcileModuleAccess(moduleKey);
  }
};

const isChecked = (moduleKey: string | undefined, childKey: string | undefined, action: string) => {
  if (!moduleKey || !childKey) return false;
  return form.permissions.includes(`${moduleKey}.${childKey}.${action}`);
};

const toggleModule = (moduleKey: string | undefined, select: boolean) => {
  if (!moduleKey) return;
  const moduleSpec = permissionCatalog.value.find((item) => item.key === moduleKey);
  moduleSpec?.children?.forEach((child) => {
    child.actions?.forEach((action) => togglePermission(moduleKey, child.key, action, select));
  });
  if (select) ensureModuleAccess(moduleKey);
  else removePermission(`${moduleKey}.module.access`);
};

const handleCheckboxChange = (moduleKey: string | undefined, childKey: string | undefined, action: string, value: boolean) => {
  togglePermission(moduleKey, childKey, action, Boolean(value));
};

const loadAll = async () => {
  loading.value = true;
  error.value = null;
  try {
    const [catalogData, roleData] = await Promise.all([
      fetchPermissionCatalog(),
      isCreate.value ? Promise.resolve([] as RolePayload[]) : fetchRoles(),
    ]);
    permissionCatalog.value = catalogData;
    buildTree();

    if (isCreate.value) {
      originalRole.value = null;
      form.name = '';
      form.description = '';
      form.permissions = [];
      return;
    }

    const found = roleData.find((role) => String(role.id) === roleId.value) || null;
    originalRole.value = found;
    form.name = found?.name ?? '';
    form.description = found?.description ?? '';
    form.permissions = found?.permissions ? [...found.permissions] : [];

    if (!found) {
      error.value = '未找到该角色模板，可能已被删除。';
    }
  } catch (err) {
    error.value = '无法加载角色数据，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

const reloadAll = async () => {
  await loadAll();
};

const confirmDiscardIfDirty = async () => {
  if (!dirty.value) return true;
  try {
    await ElMessageBox.confirm('当前更改尚未保存，是否放弃更改？', '提示', {
      confirmButtonText: '放弃更改',
      cancelButtonText: '取消',
      type: 'warning',
    });
    return true;
  } catch {
    return false;
  }
};

const goBack = async () => {
  const ok = await confirmDiscardIfDirty();
  if (!ok) return;
  router.push({ name: 'settings-permissions' });
};

const handleReset = async () => {
  if (!dirty.value) return;
  try {
    await ElMessageBox.confirm('确认重置为上次保存状态？', '提示', {
      confirmButtonText: '重置',
      cancelButtonText: '取消',
      type: 'warning',
    });
  } catch {
    return;
  }
  if (!originalRole.value) return;
  form.name = originalRole.value.name;
  form.description = originalRole.value.description || '';
  form.permissions = originalRole.value.permissions ? [...originalRole.value.permissions] : [];
};

const handleSave = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请填写角色名称');
    return;
  }
  const payload: RoleInput = {
    name: form.name.trim(),
    description: form.description,
    permissions: form.permissions,
  };
  saving.value = true;
  try {
    let saved: RolePayload;
    if (isCreate.value) {
      saved = await createRole(payload);
      originalRole.value = saved;
      ElMessage.success('角色已创建');
      router.replace({ name: 'settings-permissions-detail', params: { roleId: String(saved.id) } });
    } else if (originalRole.value) {
      saved = await updateRole(originalRole.value.id, payload);
      originalRole.value = saved;
      form.name = saved.name;
      form.description = saved.description || '';
      form.permissions = saved.permissions ? [...saved.permissions] : [];
      ElMessage.success('角色已保存');
    }
  } catch (err) {
    ElMessage.error('保存失败，请检查输入');
  } finally {
    saving.value = false;
  }
};

const handleDelete = async () => {
  if (!originalRole.value) return;
  try {
    await ElMessageBox.confirm(`确认删除角色模板 “${originalRole.value.name}” 吗？`, '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    });
  } catch {
    return;
  }
  deleting.value = true;
  try {
    await deleteRole(originalRole.value.id);
    ElMessage.success('角色已删除');
    router.push({ name: 'settings-permissions' });
  } catch (err) {
    ElMessage.error('删除失败，请稍后重试');
  } finally {
    deleting.value = false;
  }
};

watch(search, () => {
  updateExpansionForFilter();
});

onBeforeRouteLeave(async () => {
  const ok = await confirmDiscardIfDirty();
  if (!ok) return false;
  return true;
});

onMounted(async () => {
  await loadAll();
});
</script>

<style scoped>
.permission-role-detail-view {
  height: 100%;
  min-height: 0;
}

.mb-2 {
  margin-bottom: 1rem;
}

.detail-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: #fff;
}

.head-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.head-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--oa-text-primary);
}

.head-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 12px;
}

.dirty-hint {
  color: var(--el-color-warning);
}

.head-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.detail-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #fff;
  padding: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

@media (max-width: 1100px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}

.card {
  border-radius: 12px;
  border: 1px solid var(--oa-border-light);
}

.card-title {
  font-weight: 700;
  color: var(--oa-text-primary);
}

.card-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.mt-12 {
  margin-top: 12px;
}

.perm-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.perm-head__right {
  min-width: 240px;
  max-width: 420px;
  width: 100%;
}

.perm-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  background: var(--el-fill-color-light);
  margin-bottom: 10px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.perm-tree {
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  padding: 8px 12px;
}

.perm-tree :deep(.el-tree-node__content) {
  height: auto !important;
  align-items: flex-start !important;
  padding: 6px 0 !important;
}

.node-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  flex-wrap: wrap;
}

.node-row.is-leaf {
  align-items: flex-start;
  gap: 8px;
}

.module-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.module-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

.child-label {
  flex: 0 0 140px;
  font-weight: 500;
  color: var(--el-text-color-regular);
  word-break: break-all;
}

.action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  flex: 1;
}

.muted {
  color: var(--oa-text-secondary);
}

.sep {
  color: var(--oa-text-muted);
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
</style>
