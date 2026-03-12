<template>
  <RepositoryPageShell root-title="集成" :section-title="activeGroupTitle">
    <template #actions>
      <el-button
        class="toolbar-button toolbar-button--primary"
        type="primary"
        :disabled="!canCreatePlugins"
        @click="openCreateDialog"
      >
        <el-icon><Plus /></el-icon>
        新建插件
      </el-button>
      <div class="refresh-card" @click="refresh(true)">
        <el-icon class="refresh-icon" :class="{ spinning: refreshing }"><Refresh /></el-icon>
        <span>刷新</span>
      </div>
    </template>

    <div class="integration-page">
      <div class="integration-content">
        <div class="plugin-grid" v-if="!refreshing && filteredPlugins.length">
          <article
            v-for="plugin in filteredPlugins"
            :key="plugin.key"
            class="plugin-card"
          >
            <div class="plugin-card__head">
              <div>
                <h3>{{ plugin.name }}</h3>
                <p class="muted">{{ plugin.summary || plugin.runtimeDescription }}</p>
              </div>
              <div class="plugin-card__head-meta">
                <el-tag size="small" effect="plain">{{ plugin.groupTitle }}</el-tag>
                <el-switch
                  size="small"
                  :model-value="plugin.enabled"
                  :loading="Boolean(toggling[plugin.key])"
                  :disabled="!canManagePlugins || Boolean(toggling[plugin.key])"
                  @change="togglePlugin(plugin.key, $event)"
                />
              </div>
            </div>
            <dl class="plugin-meta">
              <div>
                <dt>类型</dt>
                <dd>{{ plugin.typeLabel }}</dd>
              </div>
              <div>
                <dt>状态</dt>
                <dd>
                  <el-tag size="small" :type="plugin.enabled ? 'success' : 'info'" effect="plain">
                    {{ plugin.statusLabel }}
                  </el-tag>
                </dd>
              </div>
              <div>
                <dt>组件</dt>
                <dd class="mono">{{ plugin.component || '—' }}</dd>
              </div>
              <div>
                <dt>路由</dt>
                <dd class="mono">{{ plugin.route || '—' }}</dd>
              </div>
              <div>
                <dt>运行</dt>
                <dd>{{ plugin.runtimeDescription }}</dd>
              </div>
              <div v-if="plugin.runtimeScript">
                <dt>脚本</dt>
                <dd class="mono">{{ plugin.runtimeScript }}</dd>
              </div>
            </dl>
            <div class="plugin-card__actions">
              <el-button class="btn-view" size="small" @click="openDetail(plugin.key)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button
                v-if="plugin.canEdit && canManagePlugins"
                class="btn-edit"
                size="small"
                @click="openEditor(plugin.key)"
              >
                <el-icon><EditPen /></el-icon>
                编辑
              </el-button>
              <el-button
                v-if="plugin.canDelete && canManagePlugins"
                class="btn-delete"
                size="small"
                type="danger"
                plain
                @click="deletePlugin(plugin.key)"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </article>
        </div>
        <div v-else-if="refreshing" class="plugin-grid">
          <el-skeleton v-for="n in 6" :key="n" animated :rows="4" class="plugin-card skeleton-card" />
        </div>
        <el-empty v-else description="当前分类暂无插件" />
      </div>
    </div>

    <PluginCreateDialog
      ref="createFormRef"
      v-model="createDialogVisible"
      :group-options="groupSelectOptions"
      :form="newPluginForm"
      :rules="createFormRules"
      :can-create="canCreatePlugins"
      @submit="handleCreate"
    />

    <PluginEditor
      v-if="editorVisible"
      v-model="editorVisible"
      :plugin-key="currentPluginKey"
      :definition="activePluginDefinition"
      @saved="refresh(true)"
    />

    <PluginDetailDrawer
      v-if="detailVisible"
      v-model="detailVisible"
      :plugin-key="detailPluginKey"
      :plugin="detailPlugin"
      :definition="detailDefinition"
    />
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Delete, EditPen, Plus, Refresh, View } from '@element-plus/icons-vue';
import RepositoryPageShell from '@/components/RepositoryPageShell.vue';
import { INTEGRATION_PLUGIN_GROUPS, getPluginDefinition, type IntegrationPluginDefinition, type IntegrationPluginGroupKey } from '@/data/integrationPlugins';
import PluginCreateDialog from '@/pages/integrations/components/PluginCreateDialog.vue';
import PluginDetailDrawer from '@/pages/integrations/components/PluginDetailDrawer.vue';
import PluginEditor from '@/pages/integrations/components/PluginEditor.vue';
import { usePluginConfigStore } from '@/stores/pluginConfigs';
import { useSessionStore } from '@/stores/session';
import { useScriptPluginStore } from '@/stores/scriptPlugins';
import { updatePluginConfig } from '@/services/monitoringApi';
import { updateScriptPlugin } from '@/services/toolsApi';
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus';

type FilterKey = IntegrationPluginGroupKey;

const route = useRoute();
const router = useRouter();

const pluginConfigStore = usePluginConfigStore();
const sessionStore = useSessionStore();
const scriptPluginStore = useScriptPluginStore();

const refreshing = ref(false);
const toggling = ref<Record<string, boolean>>({});
const activeGroup = ref<FilterKey>('monitoring');
const editorVisible = ref(false);
const detailVisible = ref(false);
const createDialogVisible = ref(false);
const currentPluginKey = ref<string | null>(null);
const detailPluginKey = ref<string | null>(null);
const createFormRef = ref<{ validate: FormInstance['validate'] }>();
const newPluginForm = ref({
  name: '',
  key: '',
  group: 'monitoring' as IntegrationPluginGroupKey,
  route: '',
  component: '',
  summary: ''
});

const groupSelectOptions: Array<{ key: IntegrationPluginGroupKey; label: string }> = [
  { key: 'monitoring', label: '监控插件' },
  { key: 'detection', label: '检测工具插件' },
  { key: 'reports', label: '报表插件' },
  { key: 'assets', label: '资产信息插件' },
  { key: 'tools', label: '运维脚本插件' }
];

const createFormRules = {
  name: [{ required: true, message: '请输入插件名称', trigger: 'blur' }],
  key: [{ required: true, message: '请输入唯一标识', trigger: 'blur' }],
  group: [{ required: true, message: '请选择分组', trigger: 'change' }],
  route: [{ required: true, message: '请输入路由', trigger: 'blur' }],
  component: [{ required: true, message: '请输入组件', trigger: 'blur' }]
};

const canCreatePlugins = computed(() => sessionStore.hasPermission('integrations.hub.create'));
const canManagePlugins = computed(() => sessionStore.hasPermission('integrations.hub.manage'));

const staticDefinitions = computed(() =>
  Object.values(INTEGRATION_PLUGIN_GROUPS).flatMap((group) => group.plugins)
);

const scriptDefinitions = computed<IntegrationPluginDefinition[]>(() => {
  const list = Object.values(scriptPluginStore.plugins);
  if (!list.length) return [];
  return list.map((plugin) => ({
    key: plugin.slug,
    name: plugin.name,
    route: plugin.route || '/tools/account-sync',
    component: plugin.component || 'AccountSync.vue',
    group: 'tools' as IntegrationPluginGroupKey,
    builtin: plugin.builtin,
    notes: plugin.summary || plugin.description,
    configFields: [],
    runtime: {
      mode: 'script',
      description: plugin.description || '脚本插件',
      scriptLabel: plugin.runtime_script
    },
    pluginSource: 'script'
  }));
});

const allPlugins = computed(() => [...staticDefinitions.value, ...scriptDefinitions.value]);

const pluginCards = computed(() =>
  allPlugins.value.map((definition) => {
    const group = INTEGRATION_PLUGIN_GROUPS[definition.group];
    const config = pluginConfigStore.plugins[definition.key];
    const script = scriptPluginStore.plugins[definition.key];
    const isScriptSource = definition.pluginSource === 'script';
    const enabled = isScriptSource ? script?.is_enabled !== false : config?.enabled !== false;
    const statusLabel = enabled ? '已启用' : '已禁用';
    return {
      key: definition.key,
      name: definition.name,
      summary: definition.notes || definition.runtime.description,
      route: definition.route,
      component: definition.component,
      groupKey: definition.group,
      groupTitle: group?.title || definition.group,
      typeLabel: definition.builtin ? '内置' : '扩展',
      statusLabel,
      runtimeDescription: definition.runtime.description,
      runtimeScript: definition.runtime.scriptLabel,
      checkedAt: isScriptSource ? (script?.metadata as any)?.last_checked_at : config?.last_checked_at,
      statusMessage: isScriptSource ? (script?.metadata as any)?.last_message : config?.last_message,
      pluginSource: definition.pluginSource ?? 'static',
      configId: config?.id,
      enabled,
      canEdit: true,
      canDelete: !definition.builtin
    };
  })
);

const groupOptions = computed(() =>
  Object.values(INTEGRATION_PLUGIN_GROUPS).map((group) => ({
    key: group.key,
    label: `${group.title}`,
    count: pluginCards.value.filter((p) => p.groupKey === group.key).length
  }))
);

const activeGroupTitle = computed(() => {
  const current = groupOptions.value.find((item) => item.key === activeGroup.value);
  return current?.label || '全部';
});

const activePluginDefinition = computed<IntegrationPluginDefinition | null>(() => {
  if (!currentPluginKey.value) return null;
  return allPlugins.value.find((item) => item.key === currentPluginKey.value) || getPluginDefinition(currentPluginKey.value);
});

const detailDefinition = computed<IntegrationPluginDefinition | null>(() => {
  if (!detailPluginKey.value) return null;
  return allPlugins.value.find((item) => item.key === detailPluginKey.value) || getPluginDefinition(detailPluginKey.value);
});

const detailPlugin = computed(() => {
  if (!detailPluginKey.value) return null;
  return pluginCards.value.find((item) => item.key === detailPluginKey.value) || null;
});

const filteredPlugins = computed(() => {
  return pluginCards.value.filter((plugin) => {
    if (plugin.groupKey !== activeGroup.value) return false;
    return true;
  });
});

const defaultGroupKey = computed<FilterKey>(() => groupOptions.value[0]?.key ?? 'monitoring');

const normalizeGroupKey = (key?: string | null): FilterKey => {
  const found = groupOptions.value.find((g) => g.key === key);
  return (found?.key as FilterKey) || defaultGroupKey.value;
};

const openEditor = (key: string) => {
  currentPluginKey.value = key;
  editorVisible.value = true;
};

const openDetail = (key: string) => {
  detailPluginKey.value = key;
  detailVisible.value = true;
};

const deletePlugin = (key: string) => {
  ElMessageBox.confirm('确定删除该插件吗？此操作不可恢复。', '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
    .then(() => {
      ElMessage.success(`删除指令已发送（示例，无实际接口）：${key}`);
    })
    .catch(() => {});
};

const openCreateDialog = () => {
  createDialogVisible.value = true;
};

const handleCreate = async () => {
  if (!createFormRef.value) return;
  await createFormRef.value.validate((valid) => {
    if (!valid) return;
    ElMessage.success('创建指令已发送（示例，无实际接口）');
    createDialogVisible.value = false;
  });
};

const refresh = async (force = false) => {
  if (refreshing.value) return;
  refreshing.value = true;
  try {
    await Promise.all([pluginConfigStore.fetchPluginConfigs(force), scriptPluginStore.fetchScriptPlugins(force)]);
  } finally {
    refreshing.value = false;
  }
};

const togglePlugin = async (key: string, value: boolean) => {
  if (!canManagePlugins.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  if (toggling.value[key]) return;
  const definition = allPlugins.value.find((item) => item.key === key);
  if (!definition) return;
  const isScriptSource = definition.pluginSource === 'script';

  try {
    toggling.value[key] = true;
    if (isScriptSource) {
      const script = scriptPluginStore.plugins[key];
      if (!script?.slug) {
        ElMessage.warning('脚本插件未初始化，无法切换');
        return;
      }
      await updateScriptPlugin(script.slug, { is_enabled: value });
      await scriptPluginStore.fetchScriptPlugins(true);
    } else {
      const config = pluginConfigStore.plugins[key];
      if (!config) {
        ElMessage.warning('该插件尚未初始化配置，请先创建配置');
        return;
      }
      await updatePluginConfig(config.id, { enabled: value });
      await pluginConfigStore.fetchPluginConfigs(true);
    }
    ElMessage.success(value ? '插件已启用' : '插件已禁用');
  } catch (error) {
    ElMessage.error('操作失败，请稍后重试');
    console.warn('toggle plugin failed', error);
  } finally {
    toggling.value[key] = false;
  }
};

onMounted(async () => refresh());

watch(
  () => route.params.groupKey,
  (groupKey) => {
    const normalized = normalizeGroupKey(groupKey as string | undefined);
    activeGroup.value = normalized;
    const currentPath = route.path;
    const targetPath = `/integrations/${normalized}`;
    if (currentPath !== targetPath) {
      router.replace(targetPath);
    }
  },
  { immediate: true }
);
</script>

<style scoped>
/* 对齐一次性检验/资产信息：PageShell body 内不再额外 padding */
:deep(.page-panel__body) {
  padding: 0;
}

.integration-page {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.integration-content {
  padding: 16px;
  box-sizing: border-box;
}

.plugin-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  align-items: start;
}

.plugin-card {
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--oa-bg-panel);
  min-height: 210px;
  height: auto;
  box-shadow: var(--oa-shadow-sm);
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  position: relative;
  overflow: hidden;
}

.plugin-card:hover {
  border-color: var(--oa-color-primary-light);
  box-shadow: 0 8px 16px -8px rgba(37, 99, 235, 0.18), var(--oa-shadow-md);
  transform: translateY(-2px);
}

.skeleton-card {
  padding: 14px;
  border-radius: 10px;
  border: 1px solid var(--oa-border-light);
  box-shadow: var(--oa-shadow-sm);
}

.plugin-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.03), rgba(37, 99, 235, 0.01));
  pointer-events: none;
}

.plugin-card__head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.plugin-card__head h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
}

.plugin-card__head-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.plugin-card__head .muted {
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.plugin-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 12px;
  color: var(--oa-text-secondary);
  font-size: 12px;
  align-items: start;
}

.plugin-meta dt {
  font-weight: 600;
  color: var(--oa-text-primary);
}

.plugin-meta dd {
  margin: 2px 0 0;
  color: var(--oa-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plugin-card__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--oa-border-light);
}

.plugin-card__actions :deep(.el-button) {
  border-radius: 8px;
  border-color: var(--oa-border-light);
}

.plugin-card__actions :deep(.btn-view) {
  color: var(--oa-color-primary);
  background: rgba(37, 99, 235, 0.1);
  background: color-mix(in srgb, var(--oa-color-primary) 10%, var(--oa-bg-panel));
}

.plugin-card__actions :deep(.btn-view:hover) {
  border-color: var(--oa-color-primary-light);
  background: rgba(37, 99, 235, 0.14);
  background: color-mix(in srgb, var(--oa-color-primary) 14%, var(--oa-bg-panel));
}

.plugin-card__actions :deep(.btn-edit) {
  color: var(--oa-text-secondary);
  background: var(--oa-bg-muted);
  border-color: var(--oa-border-light);
}

.plugin-card__actions :deep(.btn-edit:hover) {
  border-color: var(--oa-border-color);
  background: var(--oa-bg-hover);
}

.plugin-card__actions :deep(.btn-delete) {
  background: rgba(220, 38, 38, 0.1);
  border-color: rgba(220, 38, 38, 0.25);
  background: color-mix(in srgb, var(--oa-color-danger) 10%, var(--oa-bg-panel));
  border-color: color-mix(in srgb, var(--oa-color-danger) 25%, var(--oa-border-light));
}

.plugin-card__actions :deep(.btn-delete:hover) {
  background: rgba(220, 38, 38, 0.14);
  border-color: rgba(220, 38, 38, 0.35);
  background: color-mix(in srgb, var(--oa-color-danger) 14%, var(--oa-bg-panel));
  border-color: color-mix(in srgb, var(--oa-color-danger) 35%, var(--oa-border-light));
}

.mono {
  font-family: 'SFMono-Regular', Consolas, monospace;
  word-break: break-all;
}
</style>
