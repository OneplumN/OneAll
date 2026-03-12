<template>
  <div class="overview-status" v-if="pluginRecord">
    <el-card shadow="never" class="status-card">
      <template #header>
        <div class="status-header">
          <div>
            <h4>运行状态</h4>
            <p class="muted">实时了解大屏同步任务的健康度。</p>
          </div>
          <el-button type="primary" plain :loading="actionLoading" @click="triggerRefresh">
            立即刷新数据
          </el-button>
        </div>
      </template>
      <div class="status-grid">
        <div class="status-metric">
          <p class="label">最新成功时间</p>
          <p class="value">{{ status.latest_success || '—' }}</p>
        </div>
        <div class="status-metric">
          <p class="label">连续失败次数</p>
          <p class="value" :class="{ danger: (status.failure_count || 0) > 0 }">
            {{ status.failure_count ?? 0 }}
          </p>
        </div>
        <div class="status-metric">
          <p class="label">当前脚本版本</p>
          <p class="value">{{ config.sync_script || '未配置' }}</p>
        </div>
        <div class="status-metric">
          <p class="label">数据源说明</p>
          <p class="value small">
            {{ status.data_source_note || '配置中心托管，修改别名后请关注系统日志。' }}
          </p>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="history-card">
      <template #header>
        <div class="status-header">
          <div>
            <h4>刷新日志</h4>
            <p class="muted">最多展示最近 10 条执行记录。</p>
          </div>
        </div>
      </template>
      <el-table :data="status.history" v-loading="historyLoading" size="small" empty-text="暂无记录">
        <el-table-column prop="executed_at" label="时间" width="180" />
        <el-table-column prop="triggered_by" label="触发人" width="120" />
        <el-table-column prop="result" label="结果" width="110">
          <template #default="{ row }">
            <el-tag :type="row.result === 'success' ? 'success' : 'danger'" effect="plain">
              {{ row.result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="说明" />
      </el-table>
      <p class="history-note">更详细的执行日志可前往系统日志中心查看。</p>
    </el-card>
  </div>
  <el-empty v-else description="未找到插件配置" />
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';

import { usePluginConfigStore } from '@/stores/pluginConfigs';
import type { PluginConfigRecord } from '@/services/monitoringApi';

interface OverviewStatusItem {
  executed_at: string;
  triggered_by?: string;
  result: 'success' | 'failure';
  message?: string;
}

interface OverviewStatus {
  latest_success?: string;
  failure_count?: number;
  data_source_note?: string;
  history: OverviewStatusItem[];
}

const props = defineProps<{ pluginType: string }>();

const pluginConfigStore = usePluginConfigStore();
const pluginRecord = computed<PluginConfigRecord | null>(() => pluginConfigStore.plugins[props.pluginType] || null);
const config = computed(() => (pluginRecord.value?.config || {}) as Record<string, any>);

const actionLoading = ref(false);
const historyLoading = ref(false);
const status = reactive<OverviewStatus>({ history: [] });

const applyStatus = () => {
  const record = pluginRecord.value;
  if (!record) {
    status.latest_success = undefined;
    status.failure_count = 0;
    status.data_source_note = undefined;
    status.history = [];
    return;
  }
  status.latest_success = (config.value.latest_success as string) || record.last_checked_at || '';
  status.failure_count = (config.value.failure_count as number | undefined) ?? 0;
  status.data_source_note = (config.value.data_source_note as string | undefined) || '';
  status.history = Array.isArray(config.value.history)
    ? ((config.value.history as OverviewStatusItem[]).slice(0, 10))
    : [];
};

const reloadStatus = async () => {
  historyLoading.value = true;
  try {
    await pluginConfigStore.fetchPluginConfigs(true);
    applyStatus();
  } finally {
    historyLoading.value = false;
  }
};

const triggerRefresh = async () => {
  actionLoading.value = true;
  try {
    // TODO: 调用后端刷新接口
    await new Promise((resolve) => setTimeout(resolve, 800));
    ElMessage.success('已触发后台刷新，请关注系统日志');
    await reloadStatus();
  } finally {
    actionLoading.value = false;
  }
};

watch(
  () => pluginRecord.value,
  () => {
    applyStatus();
  },
  { immediate: true }
);

watch(
  () => config.value,
  () => {
    applyStatus();
  }
);

onMounted(() => {
  if (!pluginRecord.value) {
    reloadStatus();
  } else {
    applyStatus();
  }
});
</script>

<style scoped>
.overview-status {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-header h4 {
  margin: 0;
}

.muted {
  color: #909399;
  margin: 4px 0 0;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.status-metric {
  padding: 1rem;
  border-radius: 10px;
  background: #f5f7fa;
}

.status-metric .label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 0.25rem;
}

.status-metric .value {
  font-size: 18px;
  color: #303133;
  margin: 0;
  word-break: break-all;
}

.status-metric .value.small {
  font-size: 14px;
}

.status-metric .value.danger {
  color: #f56c6c;
}

.history-note {
  margin-top: 0.5rem;
  color: #909399;
  font-size: 13px;
}
</style>
