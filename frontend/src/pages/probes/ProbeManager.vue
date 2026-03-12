<template>
  <div class="probe-page">
    <PageWrapper :loading="loading.nodes">
      <div class="probe-manager">
        <header class="page-heading">
          <div class="heading-title">
            <span class="header__title">探针节点</span>
          </div>
          <div class="heading-actions">
            <el-button type="primary" @click="openNodeDialog">新增探针</el-button>
            <div class="refresh-card" @click="loadNodes">
              <el-icon class="refresh-icon" :class="{ spinning: loading.nodes }"><Refresh /></el-icon>
              <span>刷新</span>
            </div>
          </div>
        </header>

        <div class="stat-grid">
        <div
          class="stat-card clickable"
          :class="{ active: activeFilter === 'all' }"
          @click="setFilter('all')"
          tabindex="-1"
        >
          <div class="stat-card__left">
              <span class="stat-badge neutral"></span>
              <el-icon class="stat-icon neutral"><DataBoard /></el-icon>
            </div>
            <div class="stat-card__right">
              <p class="label">总节点</p>
              <p class="value">{{ totalCount }}</p>
            </div>
          </div>
        <div
          class="stat-card success clickable"
          :class="{ active: activeFilter === 'online' }"
          @click="setFilter('online')"
          tabindex="-1"
        >
          <div class="stat-card__left">
            <span class="stat-badge success"></span>
            <el-icon class="stat-icon success"><CircleCheck /></el-icon>
          </div>
          <div class="stat-card__right">
            <p class="label">在线</p>
            <p class="value">{{ onlineCount }}</p>
          </div>
        </div>
        <div
          class="stat-card warning clickable"
          :class="{ active: activeFilter === 'maintenance' }"
          @click="setFilter('maintenance')"
          tabindex="-1"
        >
          <div class="stat-card__left">
            <span class="stat-badge warning"></span>
            <el-icon class="stat-icon warning"><Tools /></el-icon>
          </div>
          <div class="stat-card__right">
            <p class="label">维护中</p>
            <p class="value">{{ maintenanceCount }}</p>
          </div>
        </div>
        <div
          class="stat-card danger clickable"
          :class="{ active: activeFilter === 'offline' }"
          @click="setFilter('offline')"
          tabindex="-1"
        >
          <div class="stat-card__left">
            <span class="stat-badge danger"></span>
            <el-icon class="stat-icon danger"><WarningFilled /></el-icon>
          </div>
          <div class="stat-card__right">
            <p class="label">离线/异常</p>
            <p class="value">{{ offlineCount }}</p>
          </div>
        </div>
        </div>

        <div v-if="loading.nodes" class="probe-card-grid">
          <el-skeleton
            v-for="n in 6"
            :key="n"
            animated
            class="probe-card"
            :rows="5"
            style="padding: 12px;"
          />
        </div>

        <div v-else-if="filteredProbes.length" class="probe-card-grid">
          <article v-for="probe in filteredProbes" :key="probe.id" class="probe-card">
            <header class="probe-card__header">
              <div>
                <div class="title-row">
                  <strong class="probe-card__name">{{ probe.name }}</strong>
                  <el-tag :type="statusTagType(probe.status)">{{ statusLabel(probe.status) }}</el-tag>
                </div>
                <p class="probe-card__location">
                  {{ probe.location || '未设置' }} · {{ networkTypeLabel(probe.network_type) }}
                </p>
              </div>
              <el-button text size="small" @click="copyNodeId(probe.id)">复制 ID</el-button>
            </header>
            <div class="probe-card__body">
              <div class="probe-card__line">
                <span class="label">节点 ID</span>
                <span class="value"><code class="probe-id">{{ probe.id }}</code></span>
              </div>
              <div class="probe-card__line">
                <span class="label">IP</span>
                <span class="value">{{ probe.ip_address ?? '—' }}</span>
              </div>
              <div class="probe-card__line">
                <span class="label">最后心跳</span>
                <span class="value">
                  {{ probe.last_heartbeat_at ? heartbeatAgo(probe.last_heartbeat_at) : '未上报' }}
                </span>
              </div>
              <div class="probe-card__line">
                <span class="label">最近认证</span>
                <span class="value">
                  {{ probe.last_authenticated_at ? formatAuth(probe.last_authenticated_at) : '未认证' }}
                </span>
              </div>
              <div class="probe-card__line">
                <span class="label">支持协议</span>
                <span class="value">
                  <el-space wrap>
                    <el-tag v-for="proto in probe.supported_protocols" :key="proto" size="small">
                      {{ proto }}
                    </el-tag>
                  </el-space>
                </span>
              </div>
              <div class="probe-card__line">
                <span class="label">Token</span>
                <span class="value">
                  {{ probe.api_token_hint ? `***${probe.api_token_hint}` : '未配置' }}
                </span>
              </div>
            </div>
            <footer class="probe-card__actions">
              <el-button size="small" type="primary" link @click="openRuntime(probe)">运行概览</el-button>
              <el-button size="small" link @click="rotateToken(probe)">重置 Token</el-button>
            </footer>
          </article>
        </div>

        <el-empty v-else description="当前筛选下暂无探针节点">
          <div class="empty-actions">
            <el-button type="primary" @click="openNodeDialog">新增探针</el-button>
            <el-button text @click="loadNodes">重新加载</el-button>
          </div>
        </el-empty>
      </div>
    </PageWrapper>

    <el-dialog v-model="nodeDialogVisible" title="新增探针" width="520px">
      <el-form :model="nodeForm" label-position="top">
        <el-form-item label="名称" required>
          <el-input v-model="nodeForm.name" data-test="probe-name-input" placeholder="探针名称" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="nodeForm.location" data-test="probe-location-input" placeholder="所在机房" />
        </el-form-item>
        <el-form-item label="网络类型" required>
          <el-select v-model="nodeForm.network_type" placeholder="选择网络类型">
            <el-option label="内网" value="internal" />
            <el-option label="外网" value="external" />
          </el-select>
        </el-form-item>
        <el-form-item label="支持协议" required>
          <el-select
            v-model="nodeForm.supported_protocols"
            multiple
            placeholder="支持的协议"
            data-test="probe-protocols-select"
          >
            <el-option label="HTTP" value="HTTP" />
            <el-option label="HTTPS" value="HTTPS" />
            <el-option label="Telnet" value="Telnet" />
            <el-option label="WSS" value="WSS" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="nodeDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="submitDisabled" :loading="creatingNode" @click="handleNodeSubmit">
          保存
        </el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="runtimeVisible" title="探针运行概览" size="40%">
      <div v-if="currentProbe" class="runtime-panel">
        <div class="runtime-header">
          <div>
            <p class="eyebrow">节点</p>
            <h3>{{ currentProbe.name }}</h3>
            <p class="subtitle">
              状态：<el-tag :type="statusTagType(currentProbe.status)" size="small">{{ statusLabel(currentProbe.status) }}</el-tag>
              <span class="divider">·</span>
              心跳：{{ currentProbe.last_heartbeat_at ? heartbeatAgo(currentProbe.last_heartbeat_at) : '未上报' }}
            </p>
          </div>
          <el-button text size="small" @click="reloadAgentConfig">刷新配置</el-button>
        </div>
        <section class="runtime-section">
          <h4>基础信息</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="节点 ID">
              <code class="probe-id">{{ currentProbe.id }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="IP">{{ currentProbe.ip_address ?? '—' }}</el-descriptions-item>
            <el-descriptions-item label="位置">{{ currentProbe.location || '—' }}</el-descriptions-item>
            <el-descriptions-item label="网络类型">{{ networkTypeLabel(currentProbe.network_type) }}</el-descriptions-item>
            <el-descriptions-item label="支持协议">
              <el-space wrap>
                <el-tag v-for="proto in currentProbe.supported_protocols" :key="proto" size="small">
                  {{ proto }}
                </el-tag>
              </el-space>
            </el-descriptions-item>
            <el-descriptions-item label="最近认证">
              {{ currentProbe.last_authenticated_at ? formatAuth(currentProbe.last_authenticated_at) : '未认证' }}
            </el-descriptions-item>
            <el-descriptions-item label="Token">
              {{ currentProbe.api_token_hint ? `***${currentProbe.api_token_hint}` : '未配置' }}
            </el-descriptions-item>
          </el-descriptions>
        </section>
        <section class="runtime-section">
          <div class="section-headline">
            <h4>远程配置</h4>
            <span class="section-tip">当前版本：{{ configVersionDisplay }}</span>
          </div>
          <el-form
            v-loading="configLoading"
            :model="agentConfig"
            label-width="140px"
            class="config-form"
          >
            <el-form-item label="心跳间隔 (秒)">
              <el-input-number v-model="agentConfig.heartbeat_interval" :min="5" :max="300" />
            </el-form-item>
            <el-form-item label="任务轮询间隔 (秒)">
              <el-input-number v-model="agentConfig.task_poll_interval" :min="5" :max="300" />
            </el-form-item>
            <el-form-item label="最大并发任务">
              <el-input-number v-model="agentConfig.max_concurrent_tasks" :min="1" :max="20" />
            </el-form-item>
            <el-form-item label="日志级别">
              <el-select v-model="agentConfig.log_level" placeholder="选择日志级别" clearable>
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARN" value="WARN" />
                <el-option label="ERROR" value="ERROR" />
              </el-select>
            </el-form-item>
          </el-form>
          <div class="config-actions">
            <el-button @click="reloadAgentConfig">重载</el-button>
            <el-button type="primary" :loading="configSaving" @click="saveAgentConfig">保存配置</el-button>
          </div>
        </section>
      </div>
      <el-empty v-else description="请选择探针节点" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { ElMessage, ElMessageBox } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { Refresh, DataBoard, CircleCheck, Tools, WarningFilled } from '@element-plus/icons-vue';
import PageWrapper from '@/components/PageWrapper.vue';

import apiClient from '@/services/apiClient';
import {
  fetchProbeAgentConfig,
  updateProbeAgentConfig,
  type ProbeAgentConfig
} from '@/services/probeNodeApi';

interface ProbeNode {
  id: string;
  name: string;
  ip_address?: string | null;
  location: string;
  network_type: string;
  supported_protocols: string[];
  status: string;
  last_heartbeat_at: string | null;
  last_authenticated_at: string | null;
  api_token_hint?: string | null;
}

interface CreateProbeForm {
  name: string;
  location: string;
  network_type: string;
  supported_protocols: string[];
}

const formatHeartbeat = (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm:ss');
const formatAuth = (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm:ss');

const probes = ref<ProbeNode[]>([]);
const loading = reactive({ nodes: false });
const nodeDialogVisible = ref(false);
const creatingNode = ref(false);
const runtimeVisible = ref(false);
const currentProbe = ref<ProbeNode | null>(null);
const agentConfig = reactive<ProbeAgentConfig>({});
const configLoading = ref(false);
const configSaving = ref(false);
const configVersion = ref<string>('');
const activeProbeId = ref<string | null>(null);
type FilterKey = 'all' | 'online' | 'maintenance' | 'offline';
const activeFilter = ref<FilterKey>('all');
const searchText = ref('');

const nodeForm = reactive<CreateProbeForm>({
  name: '',
  location: '',
  network_type: 'internal',
  supported_protocols: ['HTTP']
});

const resetNodeForm = () => {
  nodeForm.name = '';
  nodeForm.location = '';
  nodeForm.network_type = 'internal';
  nodeForm.supported_protocols = ['HTTP'];
};

const statusTagType = (status: string) => {
  switch (status) {
    case 'online':
      return 'success';
    case 'maintenance':
      return 'warning';
    default:
      return 'info';
  }
};

const onlineCount = computed(() => probes.value.filter((p) => p.status === 'online').length);
const maintenanceCount = computed(() => probes.value.filter((p) => p.status === 'maintenance').length);
const offlineCount = computed(() =>
  probes.value.filter((p) => p.status !== 'online' && p.status !== 'maintenance').length
);
const totalCount = computed(() => probes.value.length);
const filteredProbes = computed(() => {
  const keyword = searchText.value.trim().toLowerCase();
  const base = (() => {
    if (activeFilter.value === 'all') return probes.value;
    if (activeFilter.value === 'offline') {
      return probes.value.filter((p) => p.status !== 'online' && p.status !== 'maintenance');
    }
    return probes.value.filter((p) => p.status === activeFilter.value);
  })();
  if (!keyword) return base;
  return base.filter((p) => {
    return (
      p.name.toLowerCase().includes(keyword) ||
      (p.ip_address ?? '').toLowerCase().includes(keyword) ||
      p.id.toLowerCase().includes(keyword)
    );
  });
});

const setFilter = (key: string | FilterKey) => {
  activeFilter.value = key as FilterKey;
};

const filterLabel = computed(() => {
  switch (activeFilter.value) {
    case 'online':
      return '在线';
    case 'maintenance':
      return '维护中';
    case 'offline':
      return '离线/异常';
    default:
      return '全部节点';
  }
});

const loadNodes = async () => {
  loading.nodes = true;
  try {
    const { data } = await apiClient.get<ProbeNode[]>('/probes/nodes/');
    probes.value = data;
  } catch (error) {
    ElMessage.error('探针节点加载失败');
  } finally {
    loading.nodes = false;
  }
};

const openNodeDialog = () => {
  nodeDialogVisible.value = true;
};

const handleNodeSubmit = async () => {
  if (submitDisabled.value) {
    ElMessage.warning('请完整填写必填信息');
    return;
  }
  creatingNode.value = true;
  try {
    const payload = { ...nodeForm };
    const { data } = await apiClient.post<ProbeNode>('/probes/nodes/', payload);
    probes.value = [data, ...probes.value];
    nodeDialogVisible.value = false;
    resetNodeForm();
    ElMessage.success('探针已创建');
  } catch (error) {
    ElMessage.error('创建失败，请重试');
  } finally {
    creatingNode.value = false;
  }
};

const copyNodeId = async (id: string) => {
  const useClipboard = typeof navigator !== 'undefined' && navigator.clipboard;
  try {
    if (useClipboard) {
      await navigator.clipboard.writeText(id);
    } else {
      throw new Error('clipboard unsupported');
    }
    ElMessage.success('节点 ID 已复制');
  } catch (error) {
    const textarea = document.createElement('textarea');
    textarea.value = id;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'absolute';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    ElMessage.success('节点 ID 已复制');
  }
};

onMounted(loadNodes);

const rotateToken = async (probe: ProbeNode) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入新的探针 Token（至少16位）', '重置令牌', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^.{16,}$/,
      inputErrorMessage: '长度至少 16 位',
      inputPlaceholder: '例如：Probe#2024!Token',
    });
    const { data } = await apiClient.post<{ token: string; token_hint: string }>(
      `/probes/nodes/${probe.id}/token/`,
      { token: value }
    );
    ElMessage.success(`令牌已更新（末尾 ${data.token_hint}）`);
    probes.value = probes.value.map((item) =>
      item.id === probe.id ? { ...item, api_token_hint: data.token_hint } : item
    );
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置失败，请重试');
    }
  }
};

const openRuntime = (probe: ProbeNode) => {
  runtimeVisible.value = true;
  currentProbe.value = probe;
  activeProbeId.value = probe.id;
  loadAgentConfig(probe.id);
};

const statusLabel = (status: string) => {
  switch (status) {
    case 'online':
      return '在线';
    case 'maintenance':
      return '维护中';
    case 'offline':
      return '离线';
    default:
      return status || '未知';
  }
};

const networkTypeLabel = (networkType: string) => {
  if (networkType === 'internal') return '内网';
  if (networkType === 'external') return '外网';
  return networkType || '未知网络';
};

const heartbeatAgo = (value: string) => {
  const seconds = dayjs().diff(dayjs(value), 'second');
  if (seconds < 60) return `${seconds}s 前`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
};

const submitDisabled = computed(
  () => !nodeForm.name || !nodeForm.network_type || !nodeForm.supported_protocols.length
);

const assignAgentConfig = (config: ProbeAgentConfig) => {
  Object.keys(agentConfig).forEach((key) => {
    delete (agentConfig as Record<string, unknown>)[key];
  });
  Object.entries(config || {}).forEach(([key, value]) => {
    (agentConfig as Record<string, unknown>)[key] = value;
  });
};

const loadAgentConfig = async (probeId: string) => {
  configLoading.value = true;
  try {
    const data = await fetchProbeAgentConfig(probeId);
    assignAgentConfig(data || {});
    configVersion.value = (data?.version as string) || '';
  } catch (error) {
    console.error(error);
    assignAgentConfig({});
    configVersion.value = '';
  } finally {
    configLoading.value = false;
  }
};

const reloadAgentConfig = () => {
  if (activeProbeId.value) {
    loadAgentConfig(activeProbeId.value);
  }
};

const saveAgentConfig = async () => {
  if (!activeProbeId.value) return;
  configSaving.value = true;
  try {
    const payload: ProbeAgentConfig = { ...agentConfig };
    const data = await updateProbeAgentConfig(activeProbeId.value, payload);
    assignAgentConfig(data || {});
    configVersion.value = (data?.version as string) || '';
    ElMessage.success('配置已下发');
  } catch (error) {
    ElMessage.error('配置保存失败，请稍后重试');
  } finally {
    configSaving.value = false;
  }
};

const configVersionDisplay = computed(() => configVersion.value || '未配置');
</script>

<style scoped>
.probe-page {
  width: 100%;
  padding: 0 16px 16px;
  box-sizing: border-box;
}

.probe-manager {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  padding: 0;
  box-sizing: border-box;
}

.page-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
}

.heading-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.heading-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header__title {
  font-weight: 600;
  color: var(--oa-text-primary);
  font-size: 14px;
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--oa-border-light);
  border-radius: 8px;
  background: var(--oa-bg-panel);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
  box-shadow: var(--oa-shadow-sm);
}

.refresh-card:hover {
  border-color: var(--oa-color-primary-light);
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.12);
  transform: translateY(-1px);
}

.refresh-icon.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--oa-text-muted);
  letter-spacing: 0.5px;
}

.subtitle {
  margin: 4px 0 0;
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 12px;
}

.stat-card {
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  padding: 12px 14px;
  background: var(--oa-bg-panel);
  box-shadow: var(--oa-shadow-sm);
  position: relative;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
  display: flex;
  align-items: center;
  gap: 12px;
  outline: none;
}

.stat-card:focus,
.stat-card:focus-visible,
.stat-card:focus-within {
  outline: none !important;
  box-shadow: var(--oa-shadow-sm);
}

.stat-card:focus,
.stat-card:focus-visible {
  outline: none;
}

.stat-card__left {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: var(--oa-bg-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.stat-card__right {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 12px;
}

.stat-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--oa-bg-muted);
  color: var(--oa-text-muted);
  font-size: 18px;
}

.stat-icon.success {
  background: rgba(5, 150, 105, 0.12);
  background: color-mix(in srgb, var(--oa-color-success) 12%, var(--oa-bg-panel));
  color: var(--oa-color-success);
}

.stat-icon.warning {
  background: rgba(217, 119, 6, 0.12);
  background: color-mix(in srgb, var(--oa-color-warning) 12%, var(--oa-bg-panel));
  color: var(--oa-color-warning);
}

.stat-icon.danger {
  background: rgba(220, 38, 38, 0.12);
  background: color-mix(in srgb, var(--oa-color-danger) 12%, var(--oa-bg-panel));
  color: var(--oa-color-danger);
}

.stat-card .label {
  margin: 0;
  color: var(--oa-text-muted);
  font-size: 13px;
}

.stat-card .value {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.stat-badge {
  position: absolute;
  left: 6px;
  top: 6px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--oa-text-muted);
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.03);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--oa-border-color) 40%, transparent);
}

.stat-badge.success {
  background: var(--oa-color-success);
  box-shadow: 0 0 0 4px rgba(5, 150, 105, 0.18);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--oa-color-success) 22%, transparent);
}

.stat-badge.warning {
  background: var(--oa-color-warning);
  box-shadow: 0 0 0 4px rgba(217, 119, 6, 0.18);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--oa-color-warning) 22%, transparent);
}

.stat-badge.danger {
  background: var(--oa-color-danger);
  box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.18);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--oa-color-danger) 22%, transparent);
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  transform: translateY(-1px);
  box-shadow: var(--oa-shadow-md);
}

.stat-card.active {
  border-color: var(--oa-border-light);
  box-shadow: var(--oa-shadow-sm);
}

.stat-card.success {
  border-color: rgba(5, 150, 105, 0.25);
  border-color: color-mix(in srgb, var(--oa-color-success) 25%, var(--oa-border-color));
  background: rgba(5, 150, 105, 0.06);
  background: color-mix(in srgb, var(--oa-color-success) 6%, var(--oa-bg-panel));
}

.stat-card.warning {
  border-color: rgba(217, 119, 6, 0.25);
  border-color: color-mix(in srgb, var(--oa-color-warning) 25%, var(--oa-border-color));
  background: rgba(217, 119, 6, 0.06);
  background: color-mix(in srgb, var(--oa-color-warning) 6%, var(--oa-bg-panel));
}

.stat-card.danger {
  border-color: rgba(220, 38, 38, 0.25);
  border-color: color-mix(in srgb, var(--oa-color-danger) 25%, var(--oa-border-color));
  background: rgba(220, 38, 38, 0.06);
  background: color-mix(in srgb, var(--oa-color-danger) 6%, var(--oa-bg-panel));
}

.probe-id {
  font-family: 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.85rem;
  background: var(--oa-bg-muted);
  border: 1px solid var(--oa-border-light);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  word-break: break-all;
}

.probe-card-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
}

.probe-card {
  border: 1px solid var(--oa-border-light);
  border-radius: 12px;
  padding: 16px;
  background: linear-gradient(180deg, var(--oa-bg-panel) 0%, var(--oa-bg-muted) 100%);
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--oa-shadow-sm);
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  height: 100%;
}

.probe-card:hover {
  border-color: var(--oa-color-primary-light);
  box-shadow: 0 8px 16px -8px rgba(37, 99, 235, 0.18), var(--oa-shadow-md);
  transform: translateY(-2px);
}

.probe-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.probe-card__name {
  font-size: 16px;
  margin: 0;
}

.probe-card__location {
  margin: 2px 0 0;
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.probe-card__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.probe-card__line {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  color: var(--oa-text-secondary);
}

.probe-card__line .label {
  color: var(--oa-text-muted);
}

.probe-card__line .value {
  text-align: right;
  color: var(--oa-text-primary);
}

.probe-card__line--id .value {
  display: flex;
  gap: 6px;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.probe-card__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--oa-border-light);
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.runtime-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.runtime-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.runtime-section h4 {
  margin: 0 0 0.5rem;
  font-weight: 600;
}

.section-headline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-tip {
  font-size: 0.85rem;
  color: var(--oa-text-muted);
}

.config-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.config-form {
  max-width: 480px;
}

.empty-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}

.divider {
  color: var(--oa-text-muted);
  margin: 0 6px;
}

@media (max-width: 768px) {
  .page-heading {
    flex-direction: column;
    align-items: flex-start;
  }
  .heading-actions {
    width: 100%;
    justify-content: flex-start;
  }
  .probe-card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
