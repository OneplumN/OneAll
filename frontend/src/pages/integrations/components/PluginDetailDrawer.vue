<template>
<el-drawer
  v-model="visible"
  :title="plugin ? `插件详情：${plugin.name}` : '插件详情'"
  direction="rtl"
  size="420px"
  destroy-on-close
>
  <div v-if="plugin" class="drawer-body">
    <el-descriptions :column="1" border>
      <el-descriptions-item label="名称">{{ plugin.name }}</el-descriptions-item>
      <el-descriptions-item label="标识"><span class="mono">{{ plugin.key }}</span></el-descriptions-item>
      <el-descriptions-item label="分组">{{ plugin.groupTitle }}</el-descriptions-item>
      <el-descriptions-item label="类型">{{ plugin.typeLabel }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="plugin.enabled ? 'success' : 'info'" effect="plain">{{ plugin.statusLabel }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="路由"><span class="mono">{{ plugin.route || '—' }}</span></el-descriptions-item>
      <el-descriptions-item label="组件"><span class="mono">{{ plugin.component || '—' }}</span></el-descriptions-item>
      <el-descriptions-item label="运行模式">
        {{ definition?.runtime.description || plugin.runtimeDescription || '—' }}
      </el-descriptions-item>
      <el-descriptions-item v-if="plugin.runtimeScript" label="脚本">
        <span class="mono">{{ plugin.runtimeScript }}</span>
      </el-descriptions-item>
      <el-descriptions-item label="最近检查">
        {{ plugin.checkedAt || '—' }}
      </el-descriptions-item>
      <el-descriptions-item label="状态消息">
        <span class="mono">{{ plugin.statusMessage || '—' }}</span>
      </el-descriptions-item>
    </el-descriptions>
  </div>
  <el-empty v-else description="未选择插件" />
</el-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { IntegrationPluginDefinition } from '@/data/integrationPlugins';

type PluginSummary = {
  key: string;
  name: string;
  groupTitle: string;
  typeLabel: string;
  statusLabel: string;
  route?: string;
  component?: string;
  runtimeDescription?: string;
  runtimeScript?: string;
  checkedAt?: string;
  statusMessage?: string;
  enabled: boolean;
};

const props = defineProps<{
  modelValue: boolean;
  pluginKey: string | null;
  plugin: PluginSummary | null;
  definition: IntegrationPluginDefinition | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});
</script>

<style scoped>
.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.muted {
  color: var(--oa-text-muted);
  margin: 0;
}

.mono {
  font-family: 'SFMono-Regular', Consolas, monospace;
}
</style>
