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

const pluginSlug = 'account-sync';
const SECRET_MASK = '******';
const pollIntervalMs = 1500;

type CollapsePanel = 'ldap' | 'zabbix';
type ScrollbarLike = {
  wrapRef?: HTMLElement | null;
  setScrollTop?: (value: number) => void;
} | null;

export function useAccountSyncPage() {
  const loading = ref(false);
  const saving = ref(false);
  const running = ref(false);
  const executionsLoading = ref(false);
  const plugin = ref<ScriptPluginRecord | null>(null);
  const executions = ref<ToolExecutionRecord[]>([]);
  const currentRunId = ref<string | null>(null);
  const formValues = reactive<Record<string, string>>({
    ldap_domain: '',
    ldap_dc: '',
    ldap_user: '',
    ldap_pwd: '',
    zabbix_url: '',
    zabbix_token: '',
  });
  const configExpanded = ref(true);
  const secretState = reactive({
    ldap_pwd_set: false,
    zabbix_token_set: false,
  });
  const activePanels = ref<CollapsePanel[]>(['ldap', 'zabbix']);
  const logScrollbarRef = ref<ScrollbarLike>(null);
  const logAutoFollow = ref(true);
  const logWrap = ref(false);
  const logStartIndexByExecutionId = reactive<Record<string, number>>({});

  let pollTimer: number | null = null;

  usePageTitle('账号同步助手');

  const populateForm = (record: ScriptPluginRecord) => {
    const metadata = record.metadata || {};
    const configValues = (metadata.config_values as Record<string, string>) || {};
    formValues.ldap_domain = configValues.ldap_domain || configValues.ldap_host || '';
    formValues.ldap_dc = configValues.ldap_dc || configValues.base_dn || '';
    formValues.ldap_user = configValues.ldap_user || configValues.bind_dn || '';
    formValues.ldap_pwd = '';
    formValues.zabbix_token = '';

    const savedLdapPwd = configValues.ldap_pwd ?? configValues.bind_password;
    secretState.ldap_pwd_set = Boolean(savedLdapPwd) && savedLdapPwd !== SECRET_MASK;
    secretState.zabbix_token_set =
      Boolean(configValues.zabbix_token) && configValues.zabbix_token !== SECRET_MASK;

    if (savedLdapPwd === SECRET_MASK) {
      secretState.ldap_pwd_set = true;
    } else if (typeof savedLdapPwd === 'string') {
      formValues.ldap_pwd = savedLdapPwd || '';
      secretState.ldap_pwd_set = Boolean(formValues.ldap_pwd);
    }

    formValues.zabbix_url = configValues.zabbix_url || '';
    if (configValues.zabbix_token === SECRET_MASK) {
      secretState.zabbix_token_set = true;
    } else {
      formValues.zabbix_token = configValues.zabbix_token || '';
      secretState.zabbix_token_set = Boolean(formValues.zabbix_token);
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

  const ldapPasswordPlaceholder = computed(() =>
    secretState.ldap_pwd_set ? '已设置（留空表示不修改）' : '请输入密码'
  );
  const zabbixTokenPlaceholder = computed(() =>
    secretState.zabbix_token_set ? '已设置（留空表示不修改）' : 'Zabbix 中生成的 Token'
  );

  const isLdapReady = computed(() =>
    Boolean(
      formValues.ldap_domain &&
        formValues.ldap_dc &&
        formValues.ldap_user &&
        (formValues.ldap_pwd || secretState.ldap_pwd_set)
    )
  );
  const isZabbixReady = computed(() =>
    Boolean(formValues.zabbix_url && (formValues.zabbix_token || secretState.zabbix_token_set))
  );
  const canSave = computed(() => Boolean(plugin.value) && isLdapReady.value && isZabbixReady.value);
  const canRun = computed(() => isLdapReady.value && isZabbixReady.value);

  const validateForm = () => {
    if (
      !formValues.ldap_domain ||
      !formValues.ldap_dc ||
      !formValues.ldap_user ||
      !(formValues.ldap_pwd || secretState.ldap_pwd_set)
    ) {
      ElMessage.warning('请完善 LDAP 连接信息');
      return false;
    }
    if (!formValues.zabbix_url || !(formValues.zabbix_token || secretState.zabbix_token_set)) {
      ElMessage.warning('请完善 Zabbix API 地址与 Token');
      return false;
    }
    return true;
  };

  const buildConfigPayload = () => {
    const payload: Record<string, string> = { ...formValues };
    if (!payload.ldap_pwd && secretState.ldap_pwd_set) {
      delete payload.ldap_pwd;
    }
    if (!payload.zabbix_token && secretState.zabbix_token_set) {
      delete payload.zabbix_token;
    }
    return payload;
  };

  const handleSave = async () => {
    if (!plugin.value) return;
    if (!validateForm()) return;
    saving.value = true;
    try {
      const metadata = {
        ...(plugin.value.metadata || {}),
        config_values: buildConfigPayload(),
      };
      await updateScriptPlugin(pluginSlug, { metadata });
      ElMessage.success('配置已保存');
      secretState.ldap_pwd_set = secretState.ldap_pwd_set || Boolean(formValues.ldap_pwd);
      secretState.zabbix_token_set = secretState.zabbix_token_set || Boolean(formValues.zabbix_token);
      formValues.ldap_pwd = '';
      formValues.zabbix_token = '';
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
    const filename = `account-sync_${String(execution.run_id)}.log`;
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
    handleLogScroll,
    handleRun,
    handleSave,
    isRunningStatus,
    isLdapReady,
    isZabbixReady,
    ldapPasswordPlaceholder,
    loading,
    logAutoFollow,
    logScrollbarRef,
    logWrap,
    plugin,
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
