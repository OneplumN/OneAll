import { ElMessage } from 'element-plus';
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router';

import type { AlertTemplateRecord } from '@/features/settings/api/settingsApi';
import {
  createAlertTemplate,
  deleteAlertTemplate,
  fetchAlertTemplates,
  updateAlertTemplate,
} from '@/features/settings/api/settingsApi';

const CHANNEL_TYPE_OPTIONS = [
  { value: 'email', label: '邮件' },
  { value: 'wecom', label: '企业微信机器人' },
  { value: 'dingtalk', label: '钉钉机器人' },
  { value: 'lark', label: '飞书机器人' },
  { value: 'http', label: 'HTTP 回调' },
  { value: 'script', label: '脚本执行' },
];

const AVAILABLE_VARIABLES: Record<string, string> = {
  title: '告警标题',
  severity: '告警级别，例如 critical/warning',
  status: '告警状态，如 triggered/resolved',
  timestamp: '触发时间 (ISO 格式)',
  task_name: '任务名称或目标',
  probe_name: '探针或执行节点名称',
  message: '详细描述或错误信息',
  result_url: '控制台查看详情链接',
};

export function useAlertTemplatesPage() {
  const route = useRoute();
  const router = useRouter();

  const channelTypeOptions = CHANNEL_TYPE_OPTIONS;
  const channelTypeMap = channelTypeOptions.reduce<Record<string, string>>((map, item) => {
    map[item.value] = item.label;
    return map;
  }, {});

  const templates = ref<AlertTemplateRecord[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const keyword = ref('');
  const channelTypeFilter = ref<string>('');

  const pageSizeOptions = [10, 20, 50];
  const currentPage = ref(1);
  const pageSize = ref(20);

  const templateDialog = reactive({
    visible: false,
    loading: false,
    record: null as AlertTemplateRecord | null,
    form: {
      channel_type: 'email',
      name: '',
      description: '',
      subject: '',
      body: '',
      is_default: false,
    },
    variables: AVAILABLE_VARIABLES as Record<string, string>,
  });

  async function loadTemplates() {
    loading.value = true;
    error.value = null;
    try {
      templates.value = await fetchAlertTemplates();
    } catch {
      error.value = '无法加载通知模板，请稍后重试。';
    } finally {
      loading.value = false;
    }
  }

  const filteredTemplates = computed(() => {
    const query = keyword.value.trim().toLowerCase();
    return templates.value.filter((tpl) => {
      if (channelTypeFilter.value && tpl.channel_type !== channelTypeFilter.value) return false;
      if (!query) return true;
      return `${tpl.name} ${tpl.description || ''}`.toLowerCase().includes(query);
    });
  });

  const pagedTemplates = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value;
    return filteredTemplates.value.slice(start, start + pageSize.value);
  });

  function handlePageSizeChange(size: number) {
    pageSize.value = size;
    currentPage.value = 1;
  }

  function handlePageChange(page: number) {
    currentPage.value = page;
  }

  function formatDate(value?: string | null) {
    if (!value) return '';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  }

  function openTemplateDialog(record?: AlertTemplateRecord) {
    templateDialog.visible = true;
    templateDialog.record = record || null;
    templateDialog.form = {
      channel_type: record?.channel_type || (channelTypeFilter.value || 'email'),
      name: record?.name || '',
      description: record?.description || '',
      subject: record?.subject || '',
      body: record?.body || '',
      is_default: record?.is_default || false,
    };
    templateDialog.variables = record?.variables || AVAILABLE_VARIABLES;
  }

  async function submitTemplate() {
    templateDialog.loading = true;
    try {
      if (templateDialog.record) {
        await updateAlertTemplate(templateDialog.record.id, templateDialog.form);
      } else {
        await createAlertTemplate(templateDialog.form);
      }
      templateDialog.visible = false;
      await loadTemplates();
      ElMessage.success('模板已保存');
    } catch (err: any) {
      const detail = err?.response?.data?.detail || '保存模板失败';
      ElMessage.error(detail);
    } finally {
      templateDialog.loading = false;
    }
  }

  async function handleTemplateDelete(record: AlertTemplateRecord) {
    try {
      await deleteAlertTemplate(record.id);
      await loadTemplates();
      ElMessage.success('模板已删除');
    } catch {
      ElMessage.error('删除模板失败');
    }
  }

  async function setTemplateDefault(record: AlertTemplateRecord) {
    if (record.is_default) return;
    try {
      await updateAlertTemplate(record.id, { is_default: true });
      await loadTemplates();
      ElMessage.success('已设为默认模板');
    } catch {
      ElMessage.error('设置默认模板失败');
    }
  }

  function goChannels() {
    router.push({ name: 'settings-notifications' });
  }

  watch(
    () => [keyword.value, channelTypeFilter.value] as const,
    () => {
      currentPage.value = 1;
    }
  );

  watch(
    () => [filteredTemplates.value.length, pageSize.value] as const,
    () => {
      const maxPage = Math.max(1, Math.ceil(filteredTemplates.value.length / pageSize.value));
      if (currentPage.value > maxPage) currentPage.value = maxPage;
    }
  );

  onMounted(async () => {
    const preset = route.query.channel_type;
    if (typeof preset === 'string' && preset) channelTypeFilter.value = preset;
    await loadTemplates();
  });

  onBeforeRouteLeave(async () => {
    templateDialog.visible = false;
    await nextTick();
  });

  return {
    channelTypeOptions,
    channelTypeMap,
    templates,
    loading,
    error,
    keyword,
    channelTypeFilter,
    pageSizeOptions,
    currentPage,
    pageSize,
    templateDialog,
    filteredTemplates,
    pagedTemplates,
    loadTemplates,
    handlePageSizeChange,
    handlePageChange,
    formatDate,
    openTemplateDialog,
    submitTemplate,
    handleTemplateDelete,
    setTemplateDefault,
    goChannels,
  };
}
