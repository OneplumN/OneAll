<template>
  <div class="overview-configurator">
    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="config-alert"
    >
      驾驶舱使用 Timescale / Redis 等多种数据源，请保持别名与同步脚本一致，避免修改后导致大屏空白。
    </el-alert>
    <PluginConfigForm
      :plugin-type="pluginType"
      :fields="fields"
      :runtime="definition?.runtime"
      :title="resolvedTitle"
      @saved="handleSaved"
    />

    <el-card shadow="never" class="hint-card">
      <template #header>
        <div class="hint-header">
          <span>字段说明</span>
          <small>根据别名自动绑定后端连接</small>
        </div>
      </template>
      <ul class="hint-list">
        <li v-for="hint in hints" :key="hint.key">
          <div class="hint-key">{{ hint.key }}</div>
          <div class="hint-body">
            <p class="hint-title">{{ hint.label }}</p>
            <p class="hint-desc">{{ hint.desc }}</p>
          </div>
        </li>
      </ul>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import PluginConfigForm from '../../monitoring/components/PluginConfigForm.vue';
import type { IntegrationPluginDefinition, PluginFieldDefinition } from '@/data/integrationPlugins';

const props = defineProps<{
  pluginType: string;
  fields: PluginFieldDefinition[];
  definition?: IntegrationPluginDefinition;
  title?: string;
}>();

const emit = defineEmits(['saved']);

const resolvedTitle = computed(() => props.title || `${props.definition?.name || '驾驶舱'} 插件配置`);

const hints = computed(() =>
  props.fields.map((field) => ({
    key: field.key,
    label: field.label,
    desc: field.placeholder || '用于与运维脚本建立映射'
  }))
);

const handleSaved = () => emit('saved');

const pluginType = props.pluginType;
const fields = props.fields;
</script>

<style scoped>
.overview-configurator {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.config-alert {
  border-radius: 8px;
}

.hint-card {
  border-radius: 12px;
}

.hint-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-weight: 600;
}

.hint-header small {
  color: #909399;
  font-weight: 400;
}

.hint-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.hint-list li {
  display: flex;
  gap: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f2f5;
}

.hint-list li:last-child {
  border-bottom: none;
}

.hint-key {
  width: 140px;
  font-family: ui-monospace, SFMono-Regular, 'JetBrains Mono', Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 13px;
  color: #606266;
}

.hint-body {
  flex: 1;
}

.hint-title {
  margin: 0;
  font-weight: 600;
  color: #303133;
}

.hint-desc {
  margin: 0.25rem 0 0;
  color: #909399;
  font-size: 13px;
}
</style>
