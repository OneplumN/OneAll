<template>
  <div class="monitoring-plugin page-card">
    <header class="page-header">
      <div>
        <h1>{{ title }}</h1>
        <p class="subtitle">
          {{ subtitle }}
        </p>
      </div>
      <el-button
        type="primary"
        :loading="loading"
        @click="loadPlugin"
      >
        刷新状态
      </el-button>
    </header>

    <PluginConfigForm
      v-if="configFields.length"
      :plugin-type="pluginType"
      :fields="configFields"
      :title="title + ' · 插件配置'"
      @saved="loadPlugin"
    />

    <el-card
      class="status-card"
      shadow="never"
    >
      <template #header>
        <div class="status-card__header">
          <span>运行状态</span>
          <el-tag
            :type="statusType(plugin?.status || 'unknown')"
            effect="dark"
          >
            {{ statusLabel(plugin) }}
          </el-tag>
        </div>
      </template>
      <el-descriptions
        :column="2"
        size="small"
      >
        <el-descriptions-item label="启用状态">
          {{ plugin?.enabled === false ? '已停用' : '已启用' }}
        </el-descriptions-item>
        <el-descriptions-item label="最近检查">
          {{ plugin?.last_checked_at ? formatTime(plugin.last_checked_at) : '未记录' }}
        </el-descriptions-item>
        <el-descriptions-item label="最后消息">
          {{ plugin?.last_message || '无告警' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { onMounted, ref } from 'vue';

import PluginConfigForm from './PluginConfigForm.vue';
import { listPluginConfigs, type PluginConfigRecord } from '@/features/monitoring/api/monitoringApi';
import type { PluginFieldDefinition } from '@/data/integrationPlugins';

const props = defineProps<{ pluginType: string; title: string; subtitle: string; configFields: PluginFieldDefinition[] }>();

const plugin = ref<PluginConfigRecord | null>(null);
const loading = ref(false);

const statusType = (status: string) => {
  if (status === 'healthy') return 'success';
  if (status === 'warning') return 'warning';
  if (status === 'critical') return 'danger';
  return 'info';
};

const statusLabel = (record: PluginConfigRecord | null) => {
  if (!record) return '未配置';
  if (record.enabled === false) return '已停用';
  const status = record.status || 'unknown';
  if (status === 'healthy') return '已启用 · 健康';
  if (status === 'warning') return '已启用 · 告警';
  if (status === 'critical') return '已启用 · 异常';
  return '已启用 · 待检测';
};

const formatTime = (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm');

async function loadPlugin() {
  loading.value = true;
  try {
    const items = await listPluginConfigs();
    plugin.value = items.find((item) => item.type === props.pluginType) ?? null;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadPlugin();
});
</script>

<style scoped>
.status-card {
  margin-top: 1rem;
}

.status-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
