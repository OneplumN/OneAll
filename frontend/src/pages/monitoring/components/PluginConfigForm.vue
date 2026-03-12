<template>
  <el-card shadow="never" class="plugin-form integration-config-card">
    <template #header>
      <div class="header">
        <span>{{ title || '插件配置' }}</span>
        <div class="header-actions">
          <el-switch
            v-model="pluginEnabled"
            active-text="已启用"
            inactive-text="已停用"
            :disabled="loading || !plugin"
          />
          <el-button type="primary" text :loading="loading" @click="loadConfig">刷新</el-button>
        </div>
      </div>
    </template>

    <div v-if="loading" class="form-loading">
      <el-skeleton :rows="3" animated />
    </div>
    <div v-else>
      <el-alert v-if="!plugin" type="warning" show-icon :closable="false">
        未找到此插件配置，请联系管理员在“系统设置 > 插件”中创建。
      </el-alert>
      <div v-else class="plugin-form__body">
        <div class="plugin-form__meta">
          <span class="meta-text" v-if="plugin?.last_message">{{ plugin.last_message }}</span>
          <span class="meta-text" v-if="plugin?.last_checked_at">
            最近检查：{{ plugin.last_checked_at }}
          </span>
        </div>

        <div v-if="isScriptRuntime">
          <p class="script-default" v-if="defaultScriptLabel">
            默认脚本：{{ defaultScriptLabel }}
          </p>
          <div class="script-picker">
            <el-input
              :model-value="scriptDisplayLabel"
              readonly
              :placeholder="defaultScriptLabel ? `默认脚本：${defaultScriptLabel}` : '请选择代码管理中的脚本'"
            />
            <el-button type="primary" plain @click="openScriptPicker">
              选择脚本
            </el-button>
          </div>
          <p class="script-hint">
            {{ scriptDisplayLabel ? `当前脚本：${scriptDisplayLabel}` : '尚未选择脚本，请先选择并保存。' }}
          </p>
        </div>

        <el-form v-else-if="fields.length" label-width="140px" class="plugin-form__body-inner">
          <el-form-item
            v-for="field in fields"
            :key="field.key"
            :label="field.label"
          >
            <template v-if="field.type === 'textarea'">
              <el-input
                type="textarea"
                :rows="3"
                v-model="form[field.key]"
                :placeholder="field.placeholder"
              />
            </template>
            <el-input
              v-else
              v-model="form[field.key]"
              :placeholder="field.placeholder"
            />
          </el-form-item>
        </el-form>

        <el-alert
          v-else
          type="info"
          show-icon
          :closable="false"
          class="no-config-alert"
        >
          该插件已封装，无需额外配置。
        </el-alert>

        <div class="actions">
          <el-button type="primary" :loading="saving" :disabled="!plugin" @click="handleSave">
            保存配置
          </el-button>
          <slot name="actions"></slot>
        </div>
      </div>
    </div>

    <ScriptSelectorDialog
      v-model="scriptDialogVisible"
      :selected-id="scriptSelection.id"
      @select="handleScriptSelected"
    />
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch, computed } from 'vue';
import { ElMessage } from 'element-plus';

import ScriptSelectorDialog from '@/components/ScriptSelectorDialog.vue';
import { usePluginConfigStore } from '@/stores/pluginConfigs';
import { updatePluginConfig, type PluginConfigRecord } from '@/services/monitoringApi';
import type { ScriptRepository } from '@/services/codeRepositoryApi';
import type { PluginRuntimeDefinition } from '@/data/integrationPlugins';

interface FieldDef {
  key: string;
  label: string;
  placeholder?: string;
  type?: 'textarea' | 'input' | 'script';
}

const props = defineProps<{
  pluginType: string;
  fields: FieldDef[];
  title?: string;
  runtime?: PluginRuntimeDefinition;
}>();
const emit = defineEmits(['saved']);

const pluginConfigStore = usePluginConfigStore();
const plugin = ref<PluginConfigRecord | null>(pluginConfigStore.plugins[props.pluginType] || null);
const loading = ref(false);
const saving = ref(false);
const pluginEnabled = ref(true);
const form = reactive<Record<string, any>>({});
const scriptDialogVisible = ref(false);
const scriptSelection = reactive<{ id?: string; label?: string }>({});

const isScriptRuntime = computed(() => props.runtime?.mode === 'script');
const defaultScriptLabel = computed(() => props.runtime?.scriptLabel || '');
const scriptDisplayLabel = computed(() => scriptSelection.label || defaultScriptLabel.value || '');

const applyPlugin = () => {
  plugin.value = pluginConfigStore.plugins[props.pluginType] || null;
  const current = plugin.value;
  pluginEnabled.value = current?.enabled ?? true;
  props.fields.forEach((field) => {
    const value = current?.config?.[field.key] ?? '';
    form[field.key] = value;
  });
  if (isScriptRuntime.value) {
    const cfg = current?.config || {};
    scriptSelection.id = typeof cfg.script_repository_id === 'string' ? cfg.script_repository_id : undefined;
    scriptSelection.label = typeof cfg.script_label === 'string' ? cfg.script_label : '';
  } else {
    scriptSelection.id = undefined;
    scriptSelection.label = undefined;
  }
};

async function loadConfig() {
  loading.value = true;
  try {
    await pluginConfigStore.fetchPluginConfigs(true);
    applyPlugin();
  } finally {
    loading.value = false;
  }
}

async function handleSave() {
  if (!plugin.value) return;
  saving.value = true;
  try {
    const config: Record<string, any> = {
      ...(plugin.value.config || {}),
      ...form
    };
    if (isScriptRuntime.value) {
      config.script_repository_id = scriptSelection.id || null;
      config.script_label = scriptSelection.label || defaultScriptLabel.value || null;
    }
    await updatePluginConfig(plugin.value.id, {
      enabled: pluginEnabled.value,
      config
    });
    await pluginConfigStore.reload();
    applyPlugin();
    ElMessage.success('配置已保存');
    emit('saved');
  } catch (error) {
    ElMessage.error('保存失败，请稍后重试');
  } finally {
    saving.value = false;
  }
}

watch(
  () => pluginConfigStore.plugins,
  () => {
    applyPlugin();
  }
);

watch(
  () => props.pluginType,
  () => {
    applyPlugin();
    if (!plugin.value) {
      loadConfig();
    }
  }
);

onMounted(() => {
  applyPlugin();
  if (!plugin.value) {
    loadConfig();
  }
});

const title = props.title;

const openScriptPicker = () => {
  scriptDialogVisible.value = true;
};

const handleScriptSelected = (repository: ScriptRepository) => {
  scriptSelection.id = repository.id;
  scriptSelection.label = `${repository.name}${repository.latest_version ? ` @ ${repository.latest_version}` : ''}`;
  scriptDialogVisible.value = false;
};
</script>

<style scoped>
.plugin-form {
  margin-bottom: 1rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
}

.integration-config-card :deep(.el-card__body) {
  background: linear-gradient(135deg, #f7f9fc, #f2f7ff);
  border-radius: 18px;
}

.plugin-form__meta {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 12px;
  color: #909399;
  margin-bottom: 0.5rem;
}

.actions {
  display: flex;
  gap: 0.75rem;
}

.form-loading {
  padding: 1rem 0;
}

.plugin-form__body,
.plugin-form__body-inner {
  margin-top: 0.5rem;
}

.script-picker {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.script-picker :deep(.el-input) {
  flex: 1;
}

.script-hint {
  margin: 0.35rem 0 0;
  font-size: 12px;
  color: #475569;
}

.no-config-alert {
  margin-top: 0.5rem;
}

.script-default {
  margin: 0 0 0.35rem;
  font-size: 13px;
  color: #606266;
}
</style>
