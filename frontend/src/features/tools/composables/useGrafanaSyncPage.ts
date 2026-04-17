import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';

import { usePageTitle } from '@/composables/usePageTitle';
import { copyTextWithFallback } from '@/shared/utils/clipboard';
import {
  executeScriptPlugin,
  getScriptPlugin,
  listToolExecutions,
  type ScriptPluginRecord,
  type ToolExecutionRecord,
  updateScriptPlugin,
} from '@/features/tools/api/toolsApi';

const pluginSlug = 'grafana-sync';
const SECRET_MASK = '******';
const pollIntervalMs = 1500;

type CollapsePanel = 'zabbix' | 'grafana';
type ScrollbarLike = {
  wrapRef?: HTMLElement | null;
  setScrollTop?: (value: number) => void;
} | null;

export function useGrafanaSyncPage() {
  const loading = ref(false);
  const saving = ref(false);
  const running = ref(false);
  const executionsLoading = ref(false);
  const plugin = ref<ScriptPluginRecord | null>(null);
  const executions = ref<ToolExecutionRecord[]>([]);
  const currentRunId = ref<string | null>(null);
  const formValues = reactive<Record<string, string>>({
    zabbix_url: '',
    zabbix_token: '',
    grafana_url: '',
    grafana_token: '',
  });
  const configExpanded = ref(true);
  const activePanels = ref<CollapsePanel[]>(['zabbix', 'grafana']);
  const secretState = reactive({
    zabbix_token_set: false,
    grafana_token_set: false,
  });
  const logScrollbarRef = ref<ScrollbarLike>(null);
  const logAutoFollow = ref(true);
  const logWrap = ref(false);
  const logStartIndexByExecutionId = reactive<Record<string, number>>({});

  let pollTimer: number | null = null;

  usePageTitle('Grafana 账号同步');

  const populateForm = (record: ScriptPluginRecord) => {
    const metadata = record.metadata || {};
    const configValues = (metadata.config_values as Record<string, string>) || {};
    formValues.zabbix_url = configValues.zabbix_url || '';
    formValues.zabbix_token = '';
    formValues.grafana_token = '';
    if (configValues.zabbix_token === SECRET_MASK) {
      secretState.zabbix_token_set = true;
    } else {
      formValues.zabbix_token = configValues.zabbix_token || '';
      secretState.zabbix_token_set = Boolean(formValues.zabbix_token);
    }
    formValues.grafana_url = configValues.grafana_url || '';
    if (configValues.grafana_token === SECRET_MASK) {
      secretState.grafana_token_set = true;
    } else {
      formValues.grafana_token = configValues.grafana_token || '';
      secretState.grafana_token_set = Boolean(formValues.grafana_token);
    }
  };

  const fetchExecutionsImpl = async ({ showLoading }: { showLoading: boolean }) => {
    if (showLoading) executionsLoading.value = true;
    try {
      if (!currentRunId.value) {
        executions.value = [];
        return;
      }
      executions.value = await listToolExecutions({ plugin_slug: pluginSlug });
    } catch {
      executions.value = [];
    } finally {
      if (showLoading) executionsLoading.value = false;
    }
  };

  const fetchExecutions = async () => {
    await fetchExecutionsImpl({ showLoading: true });
  };

  const fetchPlugin = async () => {
    loading.value = true;
    try {
      const data = await getScriptPlugin(pluginSlug);
      plugin.value = data;
      populateForm(data);
      if (currentRunId.value) {
        await fetchExecutions();
      }
    } catch {
      ElMessage.error('加载脚本配置失败');
    } finally {
      loading.value = false;
    }
  };

  const zabbixTokenPlaceholder = computed(() =>
    secretState.zabbix_token_set ? '已设置（留空表示不修改）' : 'Zabbix 中生成的 Token'
  );
  const grafanaTokenPlaceholder = computed(() =>
    secretState.grafana_token_set ? '已设置（留空表示不修改）' : 'Grafana 管理员 Token'
  );

  const isZabbixReady = computed(() =>
    Boolean(formValues.zabbix_url && (formValues.zabbix_token || secretState.zabbix_token_set))
  );
  const isGrafanaReady = computed(() =>
    Boolean(formValues.grafana_url && (formValues.grafana_token || secretState.grafana_token_set))
  );
  const canSave = computed(() => Boolean(plugin.value) && isZabbixReady.value && isGrafanaReady.value);
  const canRun = computed(() => isZabbixReady.value && isGrafanaReady.value);

  const buildConfigPayload = () => {
    const payload: Record<string, string> = { ...formValues };
    if (!payload.zabbix_token && secretState.zabbix_token_set) {
      delete payload.zabbix_token;
    }
    if (!payload.grafana_token && secretState.grafana_token_set) {
      delete payload.grafana_token;
    }
    return payload;
  };

  const validateForm = () => {
    if (!isZabbixReady.value) {
      ElMessage.warning('请完善 Zabbix API 信息');
      return false;
    }
    if (!isGrafanaReady.value) {
      ElMessage.warning('请完善 Grafana API 信息');
      return false;
    }
    return true;
  };

  const handleSave = async () => {
    if (!plugin.value || !validateForm()) return;
    saving.value = true;
    try {
      const metadata = {
        ...(plugin.value.metadata || {}),
        config_values: buildConfigPayload(),
      };
      await updateScriptPlugin(pluginSlug, { metadata });
      ElMessage.success('配置已保存');
      secretState.zabbix_token_set = secretState.zabbix_token_set || Boolean(formValues.zabbix_token);
      secretState.grafana_token_set = secretState.grafana_token_set || Boolean(formValues.grafana_token);
      formValues.zabbix_token = '';
      formValues.grafana_token = '';
    } catch {
      ElMessage.error('保存失败，请稍后重试');
    } finally {
      saving.value = false;
    }
  };

  const handleRun = async () => {
    if (!validateForm()) return;
    running.value = true;
    try {
      const result = await executeScriptPlugin(pluginSlug, buildConfigPayload());
      currentRunId.value = result.run_id;
      ElMessage.success('已触发同步任务');
      logAutoFollow.value = true;
      await fetchExecutionsImpl({ showLoading: true });
    } catch {
      ElMessage.error('触发失败，请检查配置');
    } finally {
      running.value = false;
    }
  };

  const copyText = async (text: string) => {
    if (!text) return;
    try {
      await copyTextWithFallback(text);
      ElMessage.success('已复制');
    } catch {
      ElMessage.error('复制失败，请手动选择内容');
    }
  };

  const formatTime = (value: string) => {
    if (!value) return '-';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  };

  const statusText = (status: string) => {
    const normalized = (status || '').toLowerCase();
    if (normalized === 'succeeded') return '成功';
    if (normalized === 'failed') return '失败';
    if (normalized === 'running') return '执行中';
    if (normalized === 'pending') return '排队中';
    return status || '未知';
  };

  const statusTagType = (status: string) => {
    const normalized = (status || '').toLowerCase();
    if (normalized === 'succeeded') return 'success';
    if (normalized === 'failed') return 'danger';
    if (normalized === 'running') return 'info';
    if (normalized === 'pending') return 'warning';
    return 'info';
  };

  const currentExecution = computed(() => {
    if (!currentRunId.value) return null;
    return executions.value.find((item) => item.run_id === currentRunId.value) || null;
  });

  const visibleLogOutput = computed(() => {
    const execution = currentExecution.value;
    if (!execution) return '';
    const output = execution.output || '';
    const startIndex = logStartIndexByExecutionId[execution.id] ?? 0;
    const safeStart = Math.min(Math.max(0, startIndex), output.length);
    return output.slice(safeStart);
  });

  const isRunningStatus = (status?: string) => {
    const normalized = (status || '').toLowerCase();
    return normalized === 'running' || normalized === 'pending';
  };

  const stopPolling = () => {
    if (!pollTimer) return;
    window.clearInterval(pollTimer);
    pollTimer = null;
  };

  const startPolling = () => {
    if (pollTimer) return;
    pollTimer = window.setInterval(async () => {
      if (!currentRunId.value) {
        stopPolling();
        return;
      }
      if (currentExecution.value && !isRunningStatus(currentExecution.value.status)) {
        stopPolling();
        return;
      }
      await fetchExecutionsImpl({ showLoading: false });
    }, pollIntervalMs);
  };

  const scrollLogToBottom = async () => {
    await nextTick();
    const scrollbar = logScrollbarRef.value;
    const wrap = scrollbar?.wrapRef;
    if (!wrap) return;
    scrollbar?.setScrollTop?.(wrap.scrollHeight);
  };

  const handleLogScroll = () => {
    const scrollbar = logScrollbarRef.value;
    const wrap = scrollbar?.wrapRef;
    if (!wrap) return;
    const distanceToBottom = wrap.scrollHeight - (wrap.scrollTop + wrap.clientHeight);
    logAutoFollow.value = distanceToBottom < 48;
  };

  const toggleFollow = async () => {
    logAutoFollow.value = !logAutoFollow.value;
    if (logAutoFollow.value) {
      await scrollLogToBottom();
    }
  };

  const toggleWrap = () => {
    logWrap.value = !logWrap.value;
  };

  const clearLogView = () => {
    const execution = currentExecution.value;
    if (!execution) return;
    const output = execution.output || '';
    logStartIndexByExecutionId[execution.id] = output.length;
  };

  const downloadLog = () => {
    const execution = currentExecution.value;
    if (!execution) return;
    const content = visibleLogOutput.value || '';
    const filename = `grafana-sync_${String(execution.run_id)}.log`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  watch(
    () => [currentRunId.value, currentExecution.value?.status],
    () => {
      if (currentRunId.value && (!currentExecution.value || isRunningStatus(currentExecution.value.status))) {
        startPolling();
        return;
      }
      stopPolling();
    }
  );

  watch(
    () => [currentExecution.value?.id, currentExecution.value?.output],
    async () => {
      if (!logAutoFollow.value) return;
      await scrollLogToBottom();
    }
  );

  watch(
    () => currentExecution.value?.id,
    () => {
      const execution = currentExecution.value;
      if (!execution) return;
      logStartIndexByExecutionId[execution.id] ??= 0;
    }
  );

  onMounted(() => {
    void fetchPlugin();
  });

  onUnmounted(() => {
    stopPolling();
  });

  return {
    activePanels,
    canRun,
    canSave,
    clearLogView,
    configExpanded,
    copyText,
    currentExecution,
    currentRunId,
    downloadLog,
    executionsLoading,
    fetchExecutions,
    fetchPlugin,
    formValues,
    formatTime,
    grafanaTokenPlaceholder,
    handleLogScroll,
    handleRun,
    handleSave,
    isGrafanaReady,
    isRunningStatus,
    isZabbixReady,
    loading,
    logAutoFollow,
    logScrollbarRef,
    logWrap,
    running,
    saving,
    statusTagType,
    statusText,
    toggleFollow,
    toggleWrap,
    visibleLogOutput,
    zabbixTokenPlaceholder,
  };
}
