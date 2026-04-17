<template>
  <SettingsPageShell
    section-title="通知管理"
    breadcrumb="通知渠道"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <div class="settings-actions">
        <el-button
          class="toolbar-button"
          @click="goTemplates"
        >
          通知模板
        </el-button>
        <div
          class="refresh-card"
          @click="loadChannels"
        >
          <el-icon
            class="refresh-icon"
            :class="{ spinning: loading }"
          >
            <Refresh />
          </el-icon>
          <span>刷新</span>
        </div>
      </div>
    </template>

    <el-alert
      v-if="error"
      type="error"
      :closable="false"
      class="oa-inline-alert"
      show-icon
    >
      {{ error }}
    </el-alert>

    <div class="oa-list-page">
      <div class="page-toolbar page-toolbar--panel">
        <div class="page-toolbar__left" />
        <div class="page-toolbar__right">
          <el-input
            v-model="keyword"
            placeholder="搜索通知渠道 / 类型"
            clearable
            class="search-input pill-input search-input--compact"
          />
        </div>
      </div>

      <div class="oa-table-panel">
        <div class="oa-table-panel__card">
          <el-table
            v-loading="loading"
            :data="filteredChannels"
            class="oa-table"
            height="100%"
            stripe
            empty-text="暂无通知渠道"
          >
            <el-table-column
              label="通知渠道"
              min-width="260"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <div class="channel-name-row">
                  <button
                    type="button"
                    class="oa-cell-link"
                    @click.stop="goDetail(row.type)"
                  >
                    <strong class="oa-table-title">{{ row.name }}</strong>
                  </button>
                  <el-tag
                    size="small"
                    effect="plain"
                    type="info"
                  >
                    {{ channelTypeLabel(row.type) || row.type }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              label="测试状态"
              width="140"
            >
              <template #default="{ row }">
                <el-tag
                  :type="statusTagType(row)"
                  size="small"
                  effect="plain"
                >
                  {{ statusCopy(row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="启用"
              width="120"
            >
              <template #default="{ row }">
                <div
                  class="cell-center"
                  @click.stop
                >
                  <el-switch
                    :loading="enabling[row.type]"
                    :model-value="row.enabled"
                    @update:model-value="toggleChannel(row, $event)"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column
              label="上次测试"
              width="200"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span class="oa-table-meta">{{ row.last_test_at ? formatDate(row.last_test_at) : '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="200"
              fixed="right"
            >
              <template #default="{ row }">
                <div
                  class="row-actions"
                  @click.stop
                >
                  <el-button
                    text
                    size="small"
                    class="oa-table-action oa-table-action--warning"
                    :disabled="!row.enabled"
                    :loading="testing[row.type]"
                    @click="handleTest(row)"
                  >
                    测试
                  </el-button>
                  <el-button
                    text
                    size="small"
                    class="oa-table-action oa-table-action--primary"
                    @click="goDetail(row.type)"
                  >
                    配置
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="oa-panel-footer">
        <div class="oa-panel-footer__left">
          <div class="oa-panel-stats">
            共 {{ filteredChannels.length }} 条
          </div>
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

import type { AlertChannelRecord } from '@/features/settings/api/settingsApi';
import { fetchAlertChannels, testAlertChannel, updateAlertChannel } from '@/features/settings/api/settingsApi';
import SettingsPageShell from '@/features/settings/components/SettingsPageShell.vue';

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
    error.value = '无法加载通知渠道，请稍后重试。';
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
  router.push({ name: 'settings-notification-channel', params: { type } });
};

const goTemplates = () => {
  router.push({ name: 'settings-notification-templates' });
};

onMounted(loadChannels);
</script>

<style scoped>
.settings-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.channel-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
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
</style>
