<template>
  <RepositoryPageShell root-title="运维工具" section-title="账号同步" scroll-mode="page">
    <template #actions>
      <div class="refresh-card" @click="fetchPlugin">
        <el-icon class="refresh-icon" :class="{ spinning: loading }">
          <Refresh />
        </el-icon>
        <span>刷新</span>
      </div>
      <el-button class="toolbar-button toolbar-button--primary" type="primary" :loading="saving" :disabled="!canSave" @click="handleSave">
        保存配置
      </el-button>
      <el-button class="toolbar-button" type="success" :loading="running" :disabled="!canRun" @click="handleRun">立即同步</el-button>
    </template>

    <div class="layout-grid">
      <el-card shadow="never" class="card">
        <template #header>
          <div class="card-head">
            <div>
              <div class="card-title">连接配置</div>
              <div class="card-subtitle">配置 LDAP 与 Zabbix 连接信息后，可一键触发同步。</div>
            </div>
            <div class="card-meta">
              <el-tag size="small" effect="plain" :type="isLdapReady ? 'success' : 'info'">
                LDAP：{{ isLdapReady ? '已配置' : '未配置' }}
              </el-tag>
              <el-tag size="small" effect="plain" :type="isZabbixReady ? 'success' : 'info'">
                Zabbix：{{ isZabbixReady ? '已配置' : '未配置' }}
              </el-tag>
              <el-button size="small" text type="primary" @click="configExpanded = !configExpanded">
                {{ configExpanded ? '收起' : '展开' }}
              </el-button>
            </div>
          </div>
        </template>

        <el-collapse-transition>
          <div v-show="configExpanded" class="card-body">
            <el-collapse v-model="activePanels" class="config-collapse">
              <el-collapse-item name="ldap" title="LDAP 连接信息">
                <div class="section-hint">脚本会从 LDAP 读取用户列表，并将用户同步到 Zabbix。</div>
                <el-form label-position="top" :model="formValues">
                  <div class="form-grid">
                    <el-form-item label="LDAP 地址" required>
                      <el-input v-model="formValues.ldap_domain" placeholder="172.31.226.3:589" />
                    </el-form-item>
                    <el-form-item label="LDAP Base DN" required>
                      <el-input v-model="formValues.ldap_dc" placeholder="ou=ou,dc=xxx,dc=com" />
                    </el-form-item>
                    <el-form-item label="绑定 DN" required>
                      <el-input v-model="formValues.ldap_user" placeholder="uid=xxxx,ou=ldapaccount,dc=xxx,dc=com" />
                    </el-form-item>
                    <el-form-item label="绑定密码" required>
                      <el-input
                        v-model="formValues.ldap_pwd"
                        :placeholder="ldapPasswordPlaceholder"
                        type="password"
                        show-password
                      />
                    </el-form-item>
                  </div>
                </el-form>
              </el-collapse-item>
              <el-collapse-item name="zabbix" title="Zabbix 连接信息">
                <div class="section-hint">需要管理员 API Token；用户组/角色等逻辑在脚本内维护。</div>
                <el-form label-position="top" :model="formValues">
                  <div class="form-grid">
                    <el-form-item label="Zabbix API 地址" required>
                      <el-input v-model="formValues.zabbix_url" placeholder="https://zabbix/api_jsonrpc.php" />
                    </el-form-item>
                    <el-form-item label="Zabbix Token" required>
                      <el-input v-model="formValues.zabbix_token" :placeholder="zabbixTokenPlaceholder" type="password" show-password />
                    </el-form-item>
                  </div>
                </el-form>
              </el-collapse-item>
            </el-collapse>
            <div class="form-hint">敏感字段不会在页面回填；留空表示保持已保存的密钥不变。</div>
          </div>
        </el-collapse-transition>
      </el-card>

      <el-card shadow="never" class="card execution-card" :body-style="{ padding: '0' }">
        <template #header>
          <div class="card-head">
            <div>
              <div class="card-title">执行中心</div>
              <div class="card-subtitle">仅展示本次同步的状态、run_id 与实时日志。</div>
            </div>
            <div class="card-meta">
              <el-tag
                v-if="currentExecution"
                size="small"
                effect="plain"
                :type="statusTagType(currentExecution.status)"
              >
                本次：{{ statusText(currentExecution.status) }}
              </el-tag>
              <el-tag v-else-if="currentRunId" size="small" effect="plain" type="info">本次：已触发</el-tag>
              <el-button
                size="small"
                text
                :disabled="!currentRunId"
                :loading="executionsLoading"
                @click="fetchExecutions"
              >刷新日志</el-button>
            </div>
          </div>
        </template>

        <div class="execution-live">
          <template v-if="currentRunId">
            <template v-if="currentExecution">
              <div class="detail-head">
                <div class="detail-head__meta">
                  <el-tag size="small" effect="plain" :type="statusTagType(currentExecution.status)">
                    {{ statusText(currentExecution.status) }}
                  </el-tag>
                  <span class="mono">run_id: {{ currentExecution.run_id }}</span>
                  <span class="muted">{{ formatTime(currentExecution.finished_at || currentExecution.created_at || '') }}</span>
                </div>
                <el-button text :icon="DocumentCopy" @click="copyText(String(currentExecution.run_id))">复制 run_id</el-button>
              </div>
              <el-alert v-if="currentExecution.error_message" type="error" show-icon :closable="false" class="mt-12">
                {{ currentExecution.error_message }}
              </el-alert>
              <el-divider />
              <div class="terminal">
                <div class="terminal__toolbar">
                  <div class="terminal__toolbar-left">
                    <span class="terminal__title">执行日志</span>
                    <span v-if="isRunningStatus(currentExecution.status)" class="terminal__badge terminal__badge--running">实时</span>
                    <span v-else class="terminal__badge">本次</span>
                  </div>
                  <div class="terminal__toolbar-actions">
                    <el-button text size="small" :type="logAutoFollow ? 'primary' : 'info'" @click="toggleFollow">
                      跟随
                    </el-button>
                    <el-button text size="small" :type="logWrap ? 'primary' : 'info'" @click="toggleWrap">换行</el-button>
                    <el-button text size="small" :icon="DocumentCopy" @click="copyText(visibleLogOutput)">复制</el-button>
                    <el-button text size="small" :icon="Download" @click="downloadLog">下载</el-button>
                    <el-button text size="small" type="danger" @click="clearLogView">清空</el-button>
                  </div>
                </div>
                <el-scrollbar ref="logScrollbarRef" class="terminal__body" @scroll="handleLogScroll">
                  <pre
                    v-if="visibleLogOutput"
                    class="terminal__output mono"
                    :class="{ 'terminal__output--wrap': logWrap }"
                  >{{ visibleLogOutput }}</pre>
                  <div v-else class="terminal__empty">无输出</div>
                </el-scrollbar>
              </div>
            </template>
            <el-empty v-else description="任务已触发，正在等待执行记录创建…" />
          </template>
          <el-empty v-else description="点击“立即同步”开始" />
        </div>
      </el-card>
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { DocumentCopy, Download, Refresh } from '@element-plus/icons-vue';

import {
  executeScriptPlugin,
  getScriptPlugin,
  listToolExecutions,
  type ScriptPluginRecord,
  type ToolExecutionRecord,
  updateScriptPlugin
} from '@/services/toolsApi';
import { usePageTitle } from '@/composables/usePageTitle';
import RepositoryPageShell from '@/components/RepositoryPageShell.vue';

const pluginSlug = 'account-sync';
const SECRET_MASK = '******';
const pollIntervalMs = 1500;
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
  zabbix_token: ''
});
const configExpanded = ref(true);
const secretState = reactive({
  ldap_pwd_set: false,
  zabbix_token_set: false
});
const activePanels = ref<Array<'ldap' | 'zabbix'>>(['ldap', 'zabbix']);
const logScrollbarRef = ref<any>(null);
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
  secretState.zabbix_token_set = Boolean(configValues.zabbix_token) && configValues.zabbix_token !== SECRET_MASK;

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

const fetchPlugin = async () => {
  loading.value = true;
  try {
    const data = await getScriptPlugin(pluginSlug);
    plugin.value = data;
    populateForm(data);
    if (currentRunId.value) {
      await fetchExecutions();
    }
  } catch (error) {
    ElMessage.error('加载脚本配置失败');
  } finally {
    loading.value = false;
  }
};

const fetchExecutions = async () => {
  return await fetchExecutionsImpl({ showLoading: true });
};

const fetchExecutionsImpl = async ({ showLoading }: { showLoading: boolean }) => {
  if (showLoading) executionsLoading.value = true;
  try {
    if (!currentRunId.value) {
      executions.value = [];
      return;
    }
    executions.value = await listToolExecutions({ plugin_slug: pluginSlug });
  } catch (error) {
    executions.value = [];
  } finally {
    if (showLoading) executionsLoading.value = false;
  }
};

const ldapPasswordPlaceholder = computed(() => (secretState.ldap_pwd_set ? '已设置（留空表示不修改）' : '请输入密码'));
const zabbixTokenPlaceholder = computed(() => (secretState.zabbix_token_set ? '已设置（留空表示不修改）' : 'Zabbix 中生成的 Token'));

const isLdapReady = computed(() => {
  return Boolean(
    formValues.ldap_domain &&
      formValues.ldap_dc &&
      formValues.ldap_user &&
      (formValues.ldap_pwd || secretState.ldap_pwd_set)
  );
});
const isZabbixReady = computed(() => {
  return Boolean(formValues.zabbix_url && (formValues.zabbix_token || secretState.zabbix_token_set));
});
const canSave = computed(() => Boolean(plugin.value) && Boolean(isLdapReady.value && isZabbixReady.value));
const canRun = computed(() => Boolean(isLdapReady.value && isZabbixReady.value));

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
  if (!payload.ldap_pwd && secretState.ldap_pwd_set) delete payload.ldap_pwd;
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
      config_values: buildConfigPayload()
    };
    await updateScriptPlugin(pluginSlug, { metadata });
    ElMessage.success('配置已保存');
    secretState.ldap_pwd_set = secretState.ldap_pwd_set || Boolean(formValues.ldap_pwd);
    secretState.zabbix_token_set = secretState.zabbix_token_set || Boolean(formValues.zabbix_token);
    formValues.ldap_pwd = '';
    formValues.zabbix_token = '';
  } catch (error) {
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
  } catch (error) {
    ElMessage.error('触发失败，请检查配置');
  } finally {
    running.value = false;
  }
};

const copyText = async (text: string) => {
  if (!text) return;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
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
  const key = execution.id;
  const startIndex = logStartIndexByExecutionId[key] ?? 0;
  const safeStart = Math.min(Math.max(0, startIndex), output.length);
  return output.slice(safeStart);
});

const isRunningStatus = (status?: string) => {
  const normalized = (status || '').toLowerCase();
  return normalized === 'running' || normalized === 'pending';
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

const stopPolling = () => {
  if (!pollTimer) return;
  window.clearInterval(pollTimer);
  pollTimer = null;
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
  fetchPlugin();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.layout-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

.card {
  border-radius: 16px;
  border: 1px solid var(--oa-border-light);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.card-title {
  font-weight: 700;
  color: var(--oa-text-primary);
}

.card-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.meta-sep {
  color: var(--oa-text-muted);
}

.card-body {
  padding: 4px 2px 0;
}

.config-collapse :deep(.el-collapse-item__header) {
  font-weight: 600;
}

.section-hint {
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.execution-card :deep(.el-card__body) {
  height: 100%;
}

.execution-live {
  min-width: 0;
  padding: 12px 12px 12px 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 520px;
}

.mono {
  font-family: 'JetBrains Mono', Consolas, 'Courier New', monospace;
}

.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-head__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.muted {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.mt-12 {
  margin-top: 12px;
}

.terminal {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: #1e1e1e;
}

.terminal__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(255, 255, 255, 0.03);
}

.terminal__toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.terminal__title {
  font-size: 12px;
  font-weight: 600;
  color: rgba(226, 232, 240, 0.92);
}

.terminal__badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.14);
  color: rgba(226, 232, 240, 0.75);
}

.terminal__badge--running {
  background: rgba(34, 197, 94, 0.18);
  color: rgba(134, 239, 172, 0.95);
}

.terminal__toolbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.terminal__toolbar-actions :deep(.el-button) {
  padding: 0 8px;
  height: 28px;
}

.terminal__body {
  flex: 1;
  min-height: 0;
  padding: 10px 12px;
}

.terminal__output {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: rgba(226, 232, 240, 0.92);
  white-space: pre;
  word-break: normal;
}

.terminal__output--wrap {
  white-space: pre-wrap;
  word-break: break-word;
}

.terminal__empty {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.85);
}

@media (max-width: 768px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }
}
</style>
