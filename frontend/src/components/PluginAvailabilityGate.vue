<template>
  <div class="plugin-gate" v-if="loading">
    <el-skeleton :rows="3" animated />
  </div>
  <div v-else-if="isAvailable" class="plugin-gate__content">
    <slot />
  </div>
  <div v-else class="plugin-gate__placeholder">
    <el-empty
      :description="message || '该功能暂未开放或正在维护中，请稍后再试。'"
      image-size="120"
    >
      <template #description>
        <p>{{ message || '该功能暂未开放或正在维护中，请稍后再试。' }}</p>
        <p class="hint">二级菜单仍保持展示，方便你提前了解入口位置。</p>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';

import { usePluginConfigStore } from '@/stores/pluginConfigs';
import { useScriptPluginStore } from '@/stores/scriptPlugins';

const props = defineProps<{ pluginType?: string; scriptPlugin?: string; message?: string }>();

const pluginConfigStore = usePluginConfigStore();
const scriptPluginStore = useScriptPluginStore();
const loading = ref(false);

const pluginRecord = computed(() =>
  props.pluginType ? pluginConfigStore.plugins[props.pluginType] || null : null
);
const scriptPluginRecord = computed(() =>
  props.scriptPlugin ? scriptPluginStore.plugins[props.scriptPlugin] || null : null
);

const isAvailable = computed(() => {
  if (props.scriptPlugin) {
    const record = scriptPluginRecord.value;
    if (!record) return false;
    return record.is_enabled !== false;
  }
  if (!props.pluginType) return true;
  const record = pluginRecord.value;
  if (!record) return true;
  return record.enabled !== false;
});

const ensureAvailabilityLoaded = async () => {
  const tasks: Promise<unknown>[] = [];
  if (props.pluginType && !pluginRecord.value) {
    tasks.push(pluginConfigStore.fetchPluginConfigs());
  }
  if (props.scriptPlugin && !scriptPluginRecord.value) {
    tasks.push(scriptPluginStore.fetchScriptPlugins());
  }
  if (!tasks.length) return;
  loading.value = true;
  try {
    await Promise.all(tasks);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  ensureAvailabilityLoaded();
});

watch(
  () => [props.pluginType, props.scriptPlugin],
  () => {
    ensureAvailabilityLoaded();
  }
);
</script>

<style scoped>
.plugin-gate {
  padding: 2rem 0;
}

.plugin-gate__content {
  height: 100%;
  min-height: 0;
}

.plugin-gate__placeholder {
  padding: 3rem 0;
}

.plugin-gate__placeholder .hint {
  margin-top: 0.5rem;
  color: #909399;
  font-size: 13px;
}
</style>
