<template>
  <MonitoringPluginManager
    plugin-type="monitoring_overview"
    title="监控驾驶舱插件 · 管理"
    subtitle="配置驾驶舱数据源别名与同步脚本，并查看插件状态"
    :config-fields="fields"
  />
</template>

<script setup lang="ts">
import MonitoringPluginManager from './components/MonitoringPluginManager.vue';
import type { PluginFieldDefinition } from '@/data/integrationPlugins';

const fields: PluginFieldDefinition[] = [
  { key: 'primary_alias', label: '主数据源别名', placeholder: 'dashboard-db-primary' },
  { key: 'cache_alias', label: '缓存别名', placeholder: 'dashboard-redis' },
  { key: 'metrics_alias', label: '指标库别名', placeholder: 'timescale-prod' },
  { key: 'environment', label: '环境标签', placeholder: 'prod / dr / test' },
  { key: 'sync_script', label: '同步脚本标识', placeholder: 'overview-sync@v2' }
];
</script>
