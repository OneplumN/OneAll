<template>
  <div class="alert-channel-detail-view">
    <SettingsPageShell section-title="告警" :breadcrumb="breadcrumb" body-padding="0" :panel-bordered="false">
      <template #actions>
        <el-button class="toolbar-button" @click="goBack">返回</el-button>
        <div class="refresh-card" @click="reloadAll">
          <el-icon class="refresh-icon" :class="{ spinning: refreshLoading }"><Refresh /></el-icon>
          <span>刷新</span>
        </div>
      </template>

    <el-alert v-if="error" type="error" :closable="false" class="mb-2" show-icon>{{ error }}</el-alert>

    <div v-if="channel" class="detail-page">
      <div class="detail-head">
        <div class="head-left">
          <div class="head-title">{{ channel.name }}</div>
          <div class="head-sub muted">
            <span>{{ channelTypeMap[channel.type] || channel.type }}</span>
            <span class="sep">·</span>
            <span>{{ channel.type }}</span>
            <span v-if="channel.description" class="sep">·</span>
            <span v-if="channel.description">{{ channel.description }}</span>
          </div>
        </div>
        <div class="head-actions">
          <el-tag :type="statusTagType(channel)" effect="plain" size="small">{{ statusCopy(channel) }}</el-tag>
          <div class="head-switch">
            <span class="muted">启用</span>
            <el-switch :loading="enabling" :model-value="channel.enabled" @update:model-value="toggleEnabled" />
          </div>
          <el-button type="default" :disabled="!channel.enabled" :loading="testing" @click="handleTest">测试</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </div>
      </div>

      <div class="detail-scroll">
        <el-card shadow="never" class="form-card">
          <el-form label-width="140px" :disabled="!channel.enabled || saving">
            <el-form-item label="通知模板">
              <div class="template-select">
                <el-select
                  v-model="channel.form.template_id"
                  placeholder="使用默认模板"
                  clearable
                  :loading="templateLoading"
                  :disabled="templateLoading"
                  style="width: 420px"
                >
                  <el-option v-for="tpl in templatesForChannel" :key="tpl.id" :label="tpl.name" :value="tpl.id">
                    <div class="template-option">
                      <span>{{ tpl.name }}</span>
                      <el-tag v-if="tpl.is_default" size="small" type="success" effect="plain">默认</el-tag>
                    </div>
                    <small>{{ tpl.updated_at && formatDate(tpl.updated_at) }}</small>
                  </el-option>
                </el-select>
                <el-button text size="small" @click="goTemplatesWithFilter">管理模板</el-button>
                <p class="form-tip">未选择时将使用该通道默认模板。</p>
              </div>
            </el-form-item>

            <template v-if="isScriptChannel">
              <el-form-item label="脚本仓库">
                <div class="script-selection">
                  <div v-if="scriptRepository" class="script-selection__info">
                    <div class="script-selection__title">
                      <strong>{{ scriptRepository.name }}</strong>
                      <el-tag size="small" type="info" effect="plain">{{ scriptRepository.language }}</el-tag>
                    </div>
                    <p class="script-selection__desc">{{ scriptRepository.description || '暂无描述' }}</p>
                  </div>
                  <p v-else class="script-selection__placeholder">请选择代码管理中的脚本仓库</p>
                  <div class="script-selection__actions">
                    <el-button size="small" type="primary" @click="openScriptDialog">选择脚本</el-button>
                    <el-button v-if="scriptRepository" size="small" text @click="clearScriptSelection">清除</el-button>
                  </div>
                </div>
              </el-form-item>
              <el-form-item label="脚本版本">
                <el-select
                  v-model="channel.form.version_id"
                  placeholder="请选择版本"
                  :disabled="!scriptRepository"
                  :loading="scriptVersionsLoading"
                  style="width: 320px"
                >
                  <el-option v-for="version in scriptVersions" :key="version.id" :label="formatVersionLabel(version)" :value="version.id">
                    <div class="version-option">
                      <span>{{ formatVersionLabel(version) }}</span>
                      <small>{{ formatDate(version.created_at) }}</small>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </template>

            <template v-else>
              <template v-for="field in channel.config_schema" :key="field.key">
                <el-form-item :label="field.label">
                  <el-input
                    v-if="field.type === 'text' || !field.type"
                    v-model="channel.form[field.key]"
                    :placeholder="field.placeholder"
                  />
                  <el-input
                    v-else-if="field.type === 'secret'"
                    type="password"
                    show-password
                    v-model="channel.form[field.key]"
                    :placeholder="field.placeholder"
                  />
                  <el-input
                    v-else-if="field.type === 'textarea'"
                    type="textarea"
                    :rows="3"
                    v-model="channel.form[field.key]"
                    :placeholder="field.placeholder"
                  />
                  <el-switch v-else-if="field.type === 'switch'" v-model="channel.form[field.key]" />
                  <el-input-number
                    v-else-if="field.type === 'number'"
                    :controls="false"
                    v-model="channel.form[field.key]"
                    :placeholder="field.placeholder"
                  />
                  <el-select v-else-if="field.type === 'select'" v-model="channel.form[field.key]" :placeholder="field.placeholder">
                    <el-option v-for="option in field.options || []" :key="option" :label="option" :value="option" />
                  </el-select>
                </el-form-item>
              </template>
            </template>
          </el-form>
        </el-card>
      </div>
    </div>

    <div v-else class="empty-view">
      <el-empty description="未找到通道" />
    </div>
    </SettingsPageShell>

    <ScriptSelectorDialog
      v-model="scriptDialogVisible"
      :selected-id="isScriptChannel ? channel?.form.repository_id : undefined"
      @select="handleScriptSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import ScriptSelectorDialog from '@/components/ScriptSelectorDialog.vue';
import { getRepository, listVersions, type ScriptRepository, type ScriptVersion } from '@/services/codeRepositoryApi';
import type { AlertChannelRecord, AlertTemplateRecord } from '@/services/settingsApi';
import { fetchAlertChannels, fetchAlertTemplates, testAlertChannel, updateAlertChannel } from '@/services/settingsApi';

import SettingsPageShell from './components/SettingsPageShell.vue';

interface ChannelView extends AlertChannelRecord {
  form: Record<string, any>;
}

const route = useRoute();
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

const channel = ref<ChannelView | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const saving = ref(false);
const enabling = ref(false);
const testing = ref(false);

const templates = ref<AlertTemplateRecord[]>([]);
const templateLoading = ref(false);

const scriptDialogVisible = ref(false);
const scriptRepository = ref<ScriptRepository | null>(null);
const scriptVersions = ref<ScriptVersion[]>([]);
const scriptVersionsLoading = ref(false);
let scriptContextToken = 0;

const channelType = computed(() => String(route.params.type || ''));
const breadcrumb = computed(() => channel.value?.name || '通道配置');
const refreshLoading = computed(() => loading.value || templateLoading.value);

const isScriptChannel = computed(() => channel.value?.type === 'script');

const templatesForChannel = computed(() => {
  if (!channel.value) return [] as AlertTemplateRecord[];
  return templates.value.filter((item) => item.channel_type === channel.value?.type);
});

const normalizeChannel = (item: AlertChannelRecord): ChannelView => {
  const form = { ...item.config } as Record<string, any>;
  return { ...item, form } as ChannelView;
};

const loadChannel = async () => {
  const type = channelType.value;
  if (!type) return;
  loading.value = true;
  error.value = null;
  try {
    const all = await fetchAlertChannels();
    const found = all.find((item) => item.type === type);
    channel.value = found ? normalizeChannel(found) : null;
  } catch (err) {
    error.value = '无法加载告警通道，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

const loadTemplates = async () => {
  templateLoading.value = true;
  try {
    templates.value = await fetchAlertTemplates();
  } catch {
    ElMessage.error('无法加载告警模板，请稍后重试');
  } finally {
    templateLoading.value = false;
  }
};

const reloadAll = async () => {
  await Promise.all([loadChannel(), loadTemplates()]);
};

const goBack = () => {
  router.push({ name: 'settings-alerts' });
};

const goTemplates = () => {
  router.push({ name: 'settings-alert-templates' });
};

const goTemplatesWithFilter = () => {
  if (!channel.value) return goTemplates();
  router.push({ name: 'settings-alert-templates', query: { channel_type: channel.value.type } });
};

const openScriptDialog = () => {
  scriptDialogVisible.value = true;
};

const resetScriptContext = () => {
  scriptRepository.value = null;
  scriptVersions.value = [];
  scriptVersionsLoading.value = false;
};

const syncScriptContext = async (presetRepo?: ScriptRepository | null) => {
  if (!channel.value) return;
  const repoId = presetRepo?.id || channel.value.form.repository_id;
  const token = ++scriptContextToken;
  if (!repoId) {
    resetScriptContext();
    return;
  }
  scriptVersionsLoading.value = true;
  try {
    const repository = presetRepo || (await getRepository(repoId));
    if (token !== scriptContextToken) return;
    scriptRepository.value = repository;
    const versions = await listVersions(repoId);
    if (token !== scriptContextToken) return;
    scriptVersions.value = versions;
    if (!versions.length) {
      channel.value.form.version_id = undefined;
    } else if (!channel.value.form.version_id || !versions.some((item) => item.id === channel.value?.form.version_id)) {
      channel.value.form.version_id = versions[0].id;
    }
  } catch {
    if (token === scriptContextToken) {
      resetScriptContext();
      ElMessage.error('无法加载脚本信息，请重新选择');
    }
  } finally {
    if (token === scriptContextToken) scriptVersionsLoading.value = false;
  }
};

const handleScriptSelected = async (repository: ScriptRepository) => {
  if (!channel.value || channel.value.type !== 'script') return;
  channel.value.form.repository_id = repository.id;
  channel.value.form.repository_name = repository.name;
  await syncScriptContext(repository);
};

const clearScriptSelection = () => {
  if (!channel.value || channel.value.type !== 'script') return;
  channel.value.form.repository_id = undefined;
  channel.value.form.version_id = undefined;
  resetScriptContext();
};

const formatVersionLabel = (version: ScriptVersion) => version.version || version.summary || '未命名版本';

const formatDate = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

const statusTagType = (c: AlertChannelRecord) => {
  if (c.last_test_status === 'failed') return 'danger';
  if (c.last_test_status === 'success') return 'success';
  return 'info';
};

const statusCopy = (c: AlertChannelRecord) => {
  if (c.last_test_status === 'success') return '正常';
  if (c.last_test_status === 'failed') return '失败';
  return '待测试';
};

const applyChannelUpdate = (updated: AlertChannelRecord) => {
  if (!channel.value) return;
  channel.value.enabled = updated.enabled;
  channel.value.config = { ...updated.config };
  channel.value.form = { ...updated.config };
  channel.value.last_test_status = updated.last_test_status;
  channel.value.last_test_at = updated.last_test_at;
  channel.value.last_test_message = updated.last_test_message;
};

const toggleEnabled = async (value: boolean) => {
  if (!channel.value) return;
  const prev = channel.value.enabled;
  channel.value.enabled = value;
  enabling.value = true;
  try {
    const updated = await updateAlertChannel(channel.value.type, { enabled: value, config: channel.value.config || {} });
    applyChannelUpdate(updated);
    ElMessage.success(value ? '已启用' : '已停用');
  } catch (err: any) {
    channel.value.enabled = prev;
    const message = err?.response?.data?.detail || '更新失败，请稍后重试';
    ElMessage.error(message);
  } finally {
    enabling.value = false;
  }
};

const handleSave = async () => {
  if (!channel.value) return;
  saving.value = true;
  if (channel.value.type === 'script' && !channel.value.form.repository_id) {
    ElMessage.warning('请选择脚本仓库');
    saving.value = false;
    return;
  }
  try {
    const updated = await updateAlertChannel(channel.value.type, { enabled: channel.value.enabled, config: channel.value.form });
    applyChannelUpdate(updated);
    ElMessage.success('已保存');
  } catch (err: any) {
    const message = err?.response?.data?.detail || '保存失败，请检查配置';
    ElMessage.error(message);
  } finally {
    saving.value = false;
  }
};

const handleTest = async () => {
  if (!channel.value) return;
  testing.value = true;
  try {
    const result = await testAlertChannel(channel.value.type);
    ElMessage.success(result.detail || '测试成功');
    channel.value.last_test_status = result.status;
    channel.value.last_test_message = result.detail;
    channel.value.last_test_at = new Date().toISOString();
  } catch (err: any) {
    const message = err?.response?.data?.detail || '测试失败，请稍后再试';
    ElMessage.error(message);
  } finally {
    testing.value = false;
  }
};

watch(
  () => channelType.value,
  async () => {
    await reloadAll();
  }
);

watch(
  () => channel.value?.type,
  (type) => {
    if (type === 'script') {
      syncScriptContext();
    } else {
      resetScriptContext();
    }
  },
  { immediate: true }
);

watch(templates, () => {
  if (!channel.value) return;
  const templateId = channel.value.form.template_id;
  if (templateId && !templates.value.some((tpl) => tpl.id === templateId)) {
    channel.value.form.template_id = undefined;
  }
});

onMounted(async () => {
  await reloadAll();
});
</script>

<style scoped>
.alert-channel-detail-view {
  height: 100%;
  min-height: 0;
}

.mb-2 {
  margin-bottom: 1rem;
}

.detail-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: #fff;
}

.head-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.head-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--oa-text-primary);
}

.head-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 12px;
}

.head-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.head-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.02);
}

.detail-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #fff;
  padding: 16px;
}

.form-card {
  border-radius: 12px;
  border: 1px solid var(--oa-border-light);
  padding: 12px 16px;
}

.template-select {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.template-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-tip {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.script-selection {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  padding: 12px;
  border: 1px dashed var(--oa-border-light);
  border-radius: 10px;
}

.script-selection__title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.script-selection__desc,
.script-selection__placeholder {
  margin: 0;
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.script-selection__actions {
  display: flex;
  gap: 8px;
}

.version-option {
  display: flex;
  justify-content: space-between;
  width: 100%;
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

.empty-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.muted {
  color: var(--oa-text-secondary);
}

.sep {
  color: var(--oa-text-muted);
}
</style>
