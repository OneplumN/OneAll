import { ElMessage, ElMessageBox } from 'element-plus';
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router';

import type { PermissionModule, RoleInput, RolePayload } from '@/features/settings/api/settingsApi';
import {
  createRole,
  deleteRole,
  fetchPermissionCatalog,
  fetchRoles,
  updateRole,
} from '@/features/settings/api/settingsApi';

interface PermissionTreeNode {
  id: string;
  label: string;
  moduleKey: string;
  childKey?: string;
  actions?: string[];
  children?: PermissionTreeNode[];
}

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

export function usePermissionRoleDetailPage() {
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
    if (isCreate.value) return '角色模板 / 新增';
    return `角色模板 / ${originalRole.value?.name || '编辑'}`;
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

  const formatActionLabel = (action: string) =>
    ACTION_LABELS[action] ?? action.replace(/_/g, ' ').toUpperCase();

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
            const actionMatches = child.actions?.filter((action) =>
              formatActionLabel(action).toLowerCase().includes(keyword)
            );
            if (moduleMatch || childMatch) return { ...child };
            if (actionMatches && actionMatches.length) return { ...child, actions: actionMatches };
            return null;
          })
          .filter(Boolean) as PermissionTreeNode[];
        if (moduleMatch) {
          return { ...module, children: module.children?.map((child) => ({ ...child })) ?? [] };
        }
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

  const togglePermission = (
    moduleKey: string | undefined,
    childKey: string | undefined,
    action: string,
    checked: boolean
  ) => {
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

  const handleCheckboxChange = (
    moduleKey: string | undefined,
    childKey: string | undefined,
    action: string,
    value: boolean
  ) => {
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
    } catch {
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
    } catch {
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
    } catch {
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

  return {
    isCreate,
    loading,
    saving,
    deleting,
    error,
    originalRole,
    form,
    treeRenderKey,
    expandedKeys,
    search,
    treeProps,
    breadcrumb,
    dirty,
    filteredTreeData,
    formatActionLabel,
    handleSearchInput,
    setAllModulesExpansion,
    toggleModule,
    isChecked,
    handleCheckboxChange,
    reloadAll,
    goBack,
    handleReset,
    handleSave,
    handleDelete,
  };
}
