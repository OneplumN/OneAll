<template>
  <SettingsPageShell section-title="告警" body-padding="0" :panel-bordered="false">
    <template #actions>
      <div class="refresh-card" @click="loadChannels">
        <el-icon class="refresh-icon" :class="{ spinning: loading }"><Refresh /></el-icon>
        <span>刷新</span>
      </div>
    </template>

    <el-alert v-if="error" type="error" :closable="false" class="mb-2" show-icon>{{ error }}</el-alert>

    <div class="list-page">
      <div class="repository-filters">
        <div class="filters-left">
          <el-button class="toolbar-button" @click="goTemplates">模板管理</el-button>
        </div>
        <div class="filters-right">
          <el-input
            v-model="keyword"
            placeholder="搜索通道名称 / 类型"
            clearable
            class="search-input pill-input search-input--compact"
          />
        </div>
      </div>

      <div class="repository-table">
        <div class="repository-table__card">
          <el-table
            v-loading="loading"
            :data="filteredChannels"
            height="100%"
            stripe
            empty-text="暂无通道"
            :header-cell-style="tableHeaderStyle"
            :cell-style="tableCellStyle"
          >
            <el-table-column label="通道" min-width="260" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="channel-name-row">
                  <button type="button" class="channel-link" @click.stop="goDetail(row.type)">
                    <strong class="cell-title">{{ row.name }}</strong>
                  </button>
                  <el-tag size="small" effect="plain" type="info">
                    {{ channelTypeLabel(row.type) || row.type }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="测试状态" width="140">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row)" size="small" effect="plain">{{ statusCopy(row) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="启用" width="120">
              <template #default="{ row }">
                <div class="cell-center" @click.stop>
                  <el-switch
                    :loading="enabling[row.type]"
                    :model-value="row.enabled"
                    @update:model-value="toggleChannel(row, $event)"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="上次测试" width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="muted">{{ row.last_test_at ? formatDate(row.last_test_at) : '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <div class="row-actions" @click.stop>
                  <el-button text size="small" :disabled="!row.enabled" :loading="testing[row.type]" @click="handleTest(row)">
                    测试
                  </el-button>
                  <el-button text size="small" type="primary" @click="goDetail(row.type)">配置</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="repository-table__footer">
        <div class="footer-left">
          <div class="repository-stats">共 {{ filteredChannels.length }} 条</div>
        </div>
      </div>
    </div>
  </SettingsPageShell>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import type { AlertChannelRecord } from '@/services/settingsApi';
import { fetchAlertChannels, testAlertChannel, updateAlertChannel } from '@/services/settingsApi';
import SettingsPageShell from './components/SettingsPageShell.vue';

type ChannelRow = AlertChannelRecord;

const router = useRouter();

const channelTypeOptions = [
  { value: 'email', label: '邮件' },
  { value: 'wecom', label: '企业微信机器人' },
  { value: 'dingtalk', label: '钉钉机器人' },
  { value: 'lark', label: '飞书机器人' },
  { value: 'http', label: 'HTTP 回调' },
  { value: 'script', label: '脚本执行' },
];

const channelTypeMap = channelTypeOptions.reduce<Record<string, string>>((map, item) => {
  map[item.value] = item.label;
  return map;
}, {});

const channelTypeLabel = (type: string) => channelTypeMap[type] || '';

const channels = ref<ChannelRow[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const keyword = ref('');
const enabling = reactive<Record<string, boolean>>({});
const testing = reactive<Record<string, boolean>>({});

const loadChannels = async () => {
  loading.value = true;
  error.value = null;
  try {
    channels.value = await fetchAlertChannels();
  } catch (err) {
    error.value = '无法加载告警通道，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

const filteredChannels = computed(() => {
  const k = keyword.value.trim().toLowerCase();
  if (!k) return channels.value;
  return channels.value.filter((c) => `${c.name} ${c.type}`.toLowerCase().includes(k));
});

const formatDate = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

const statusTagType = (channel: ChannelRow) => {
  if (channel.last_test_status === 'failed') return 'danger';
  if (channel.last_test_status === 'success') return 'success';
  return 'info';
};

const statusCopy = (channel: ChannelRow) => {
  if (channel.last_test_status === 'success') return '正常';
  if (channel.last_test_status === 'failed') return '失败';
  return '待测试';
};

const toggleChannel = async (channel: ChannelRow, value: boolean) => {
  const prev = channel.enabled;
  channel.enabled = value;
  enabling[channel.type] = true;
  try {
    const updated = await updateAlertChannel(channel.type, {
      enabled: value,
      config: channel.config || {},
    });
    channel.enabled = updated.enabled;
    channel.config = { ...updated.config };
    channel.last_test_status = updated.last_test_status;
    channel.last_test_at = updated.last_test_at;
    channel.last_test_message = updated.last_test_message;
    ElMessage.success(value ? '已启用' : '已停用');
  } catch (err: any) {
    channel.enabled = prev;
    const message = err?.response?.data?.detail || '更新失败，请稍后重试';
    ElMessage.error(message);
  } finally {
    enabling[channel.type] = false;
  }
};

const handleTest = async (channel: ChannelRow) => {
  testing[channel.type] = true;
  try {
    const result = await testAlertChannel(channel.type);
    ElMessage.success(result.detail || '测试成功');
    channel.last_test_status = result.status;
    channel.last_test_message = result.detail;
    channel.last_test_at = new Date().toISOString();
  } catch (err: any) {
    const message = err?.response?.data?.detail || '测试失败，请稍后再试';
    ElMessage.error(message);
  } finally {
    testing[channel.type] = false;
  }
};

const goDetail = (type: string) => {
  router.push({ name: 'settings-alert-channel', params: { type } });
};

const goTemplates = () => {
  router.push({ name: 'settings-alert-templates' });
};

const tableHeaderStyle = () => ({
  background: 'var(--oa-bg-muted)',
  color: 'var(--oa-text-secondary)',
  fontWeight: 600,
  height: '44px',
});

const tableCellStyle = () => ({
  height: '44px',
  padding: '6px 8px',
});

onMounted(loadChannels);
</script>

<style scoped>
.mb-2 {
  margin-bottom: 1rem;
}

.list-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.repository-filters {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.filters-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filters-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 220px;
}

.search-input--compact {
  max-width: 360px;
}

.pill-input :deep(.el-input__wrapper) {
  border-radius: 999px;
  padding-left: 0.85rem;
  background: var(--oa-filter-control-bg);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}

.repository-table {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--oa-bg-panel);
  padding: 0 16px 12px;
}

.repository-table__card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: none;
}

.repository-table__card :deep(.el-table) {
  flex: 1;
  overflow-x: hidden;
}

.repository-table__card :deep(.el-table__inner-wrapper) {
  border: none !important;
}

.repository-table__card :deep(.el-table__cell) {
  padding: 8px 10px;
}

.repository-table__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 0px 16px 12px;
  color: var(--oa-text-secondary);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.repository-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.cell-title {
  font-weight: 600;
}

.channel-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.channel-link {
  display: inline-flex;
  align-items: baseline;
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  color: inherit;
}

.channel-link:hover .cell-title {
  text-decoration: underline;
}

.muted {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.sep {
  color: var(--oa-text-muted);
}

.cell-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.row-actions {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
}

.row-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.08);
  cursor: pointer;
  user-select: none;
}

.refresh-card:hover {
  background: rgba(15, 23, 42, 0.06);
}

.refresh-icon {
  transition: transform 0.35s ease;
}

.refresh-icon.spinning {
  animation: spinning 0.9s linear infinite;
}

@keyframes spinning {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
