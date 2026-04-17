import { ElMessage } from 'element-plus';
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import type {
  AlertChannelRecord,
  AlertTemplateRecord,
} from '@/features/settings/api/settingsApi';
import {
  fetchAlertChannels,
  fetchAlertTemplates,
  testAlertChannel,
  updateAlertChannel,
} from '@/features/settings/api/settingsApi';
import { getRepository, listVersions, type ScriptRepository, type ScriptVersion } from '@/features/tools/api/codeRepositoryApi';

export interface ChannelView extends AlertChannelRecord {
  form: Record<string, any>;
}

const channelTypeOptions = [
  { value: 'email', label: '邮件' },
  { value: 'wecom', label: '企业微信机器人' },
  { value: 'dingtalk', label: '钉钉机器人' },
  { value: 'lark', label: '飞书机器人' },
  { value: 'http', label: 'HTTP 回调' },
  { value: 'script', label: '脚本执行' },
];

export function useAlertChannelDetailPage() {
  const route = useRoute();
  const router = useRouter();

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
  const breadcrumb = computed(() => `通知渠道 / ${channel.value?.name || '配置'}`);
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

  async function loadChannel() {
    const type = channelType.value;
    if (!type) return;
    loading.value = true;
    error.value = null;
    try {
      const all = await fetchAlertChannels();
      const found = all.find((item) => item.type === type);
      channel.value = found ? normalizeChannel(found) : null;
    } catch {
      error.value = '无法加载通知渠道，请稍后重试。';
    } finally {
      loading.value = false;
    }
  }

  async function loadTemplates() {
    templateLoading.value = true;
    try {
      templates.value = await fetchAlertTemplates();
    } catch {
      ElMessage.error('无法加载通知模板，请稍后重试');
    } finally {
      templateLoading.value = false;
    }
  }

  async function reloadAll() {
    await Promise.all([loadChannel(), loadTemplates()]);
  }

  const goBack = () => {
    router.push({ name: 'settings-notifications' });
  };

  const goTemplates = () => {
    router.push({ name: 'settings-notification-templates' });
  };

  const goTemplatesWithFilter = () => {
    if (!channel.value) return goTemplates();
    router.push({ name: 'settings-notification-templates', query: { channel_type: channel.value.type } });
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
      } else if (
        !channel.value.form.version_id ||
        !versions.some((item) => item.id === channel.value?.form.version_id)
      ) {
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

  const formatVersionLabel = (version: ScriptVersion) =>
    version.version || version.summary || '未命名版本';

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
      const updated = await updateAlertChannel(channel.value.type, {
        enabled: value,
        config: channel.value.config || {},
      });
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
      const updated = await updateAlertChannel(channel.value.type, {
        enabled: channel.value.enabled,
        config: channel.value.form,
      });
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
        void syncScriptContext();
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

  return {
    channelTypeMap,
    channelTypeOptions,
    channel,
    error,
    saving,
    enabling,
    testing,
    templates,
    templateLoading,
    scriptDialogVisible,
    scriptRepository,
    scriptVersions,
    scriptVersionsLoading,
    breadcrumb,
    refreshLoading,
    isScriptChannel,
    templatesForChannel,
    reloadAll,
    goBack,
    goTemplatesWithFilter,
    openScriptDialog,
    handleScriptSelected,
    clearScriptSelection,
    formatVersionLabel,
    formatDate,
    statusTagType,
    statusCopy,
    toggleEnabled,
    handleSave,
    handleTest,
  };
}
