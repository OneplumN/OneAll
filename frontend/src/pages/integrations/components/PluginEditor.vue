<template>
  <el-dialog
    v-model="visible"
    :title="definition ? `配置：${definition.name}` : '插件配置'"
    width="720px"
    destroy-on-close
  >
    <div v-if="definition">
      <PluginConfigForm
        v-if="definition.pluginSource !== 'script'"
        :plugin-type="definition.key"
        :fields="definition.configFields"
        :runtime="definition.runtime"
        :title="definition.name"
        @saved="handleSaved"
      />
      <div v-else class="script-editor">
        <el-alert type="info" show-icon :closable="false" class="mb-3">
          选择要关联的脚本库，保存后通过后端执行。
        </el-alert>
        <el-form label-width="120px" class="script-form">
          <el-form-item label="当前脚本">
            <el-input :model-value="scriptLabel || '未选择'" readonly />
          </el-form-item>
          <el-form-item label="选择脚本">
            <ScriptSelectorDialog
              v-model="selectorVisible"
              :selected-id="scriptSelection.id"
              @select="handleSelect"
            />
            <el-button type="primary" plain @click="selectorVisible = true">选择脚本</el-button>
          </el-form-item>
        </el-form>
        <div class="script-actions">
          <el-button @click="emit('update:modelValue', false)">取消</el-button>
          <el-button type="primary" :loading="saving" @click="saveScript">保存</el-button>
        </div>
      </div>
    </div>
    <el-empty v-else description="未选择插件" />
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';

import PluginConfigForm from '@/pages/monitoring/components/PluginConfigForm.vue';
import ScriptSelectorDialog from '@/components/ScriptSelectorDialog.vue';
import type { IntegrationPluginDefinition } from '@/data/integrationPlugins';
import { updateScriptPlugin } from '@/services/toolsApi';
import { useScriptPluginStore } from '@/stores/scriptPlugins';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  modelValue: boolean;
  pluginKey: string | null;
  definition: IntegrationPluginDefinition | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'saved'): void;
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const handleSaved = () => {
  emit('saved');
};

const scriptPluginStore = useScriptPluginStore();
const selectorVisible = ref(false);
const saving = ref(false);
const scriptSelection = reactive<{ id?: string; label?: string }>({});

const scriptRecord = computed(() => (props.pluginKey ? scriptPluginStore.plugins[props.pluginKey] : undefined));
const scriptLabel = computed(() => scriptSelection.label || scriptRecord.value?.metadata?.runtime_script || '');

const syncScriptSelection = () => {
  const record = scriptRecord.value;
  if (!record) {
    scriptSelection.id = undefined;
    scriptSelection.label = undefined;
    return;
  }
  const meta = (record.metadata || {}) as Record<string, any>;
  scriptSelection.id = meta.script_repository_id || undefined;
  scriptSelection.label = meta.script_label || meta.runtime_script || undefined;
};

const handleSelect = (repository: { id: string; name: string }) => {
  scriptSelection.id = repository.id;
  scriptSelection.label = repository.name;
};

const saveScript = async () => {
  if (!props.pluginKey) return;
  const slug = scriptRecord.value?.slug;
  if (!slug) {
    ElMessage.warning('未找到脚本插件记录');
    return;
  }
  if (!scriptSelection.id || !scriptSelection.label) {
    ElMessage.warning('请先选择脚本库');
    return;
  }
  saving.value = true;
  try {
    await updateScriptPlugin(slug, {
      metadata: {
        script_repository_id: scriptSelection.id,
        script_label: scriptSelection.label,
        runtime_script: scriptSelection.label
      }
    });
    await scriptPluginStore.fetchScriptPlugins(true);
    ElMessage.success('脚本已更新');
    emit('saved');
    emit('update:modelValue', false);
  } catch (error) {
    ElMessage.error('保存失败，请稍后再试');
  } finally {
    saving.value = false;
  }
};

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      syncScriptSelection();
    }
  }
);

watch(
  () => props.pluginKey,
  () => {
    syncScriptSelection();
  }
);
</script>

<style scoped>
.script-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.script-form {
  max-width: 520px;
}

.script-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}
</style>
