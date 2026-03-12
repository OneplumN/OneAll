<template>
  <div class="zabbix-board page-card" v-loading="loading">
    <section class="hero-panel">
      <div class="hero-grid">
        <div class="hero-content">
          <div class="hero-text">
            <p class="hero-kicker">SYNTH • WATCH</p>
            <h1>Zabbix 监控驾驶舱</h1>
            <p class="hero-subtitle">聚合 Zabbix 告警、主机健康与同步态势，统一在 OneAll 可视宇宙。</p>
          </div>
          <div class="hero-actions">
            <el-button color="#22d3ee" plain :loading="testing" @click="handleTestConnection">测试连接</el-button>
            <el-button color="#f472b6" plain :loading="syncing" @click="handleSyncNow">立即同步</el-button>
            <el-button text type="primary" @click="refreshDashboard(true)">刷新数据</el-button>
            <el-select
              v-if="canManageSystemSettings"
              class="refresh-select"
              size="small"
              :model-value="zabbixRefreshSeconds"
              :loading="refreshSettingsLoading"
              :disabled="refreshSettingsSaving"
              @update:model-value="handleUpdateRefreshSeconds"
            >
              <el-option label="30 秒刷新" :value="30" />
              <el-option label="1 分钟刷新" :value="60" />
              <el-option label="5 分钟刷新" :value="300" />
              <el-option label="15 分钟刷新" :value="900" />
              <el-option label="30 分钟刷新" :value="1800" />
              <el-option label="1 小时刷新" :value="3600" />
            </el-select>
            <el-tag effect="dark" type="success">插件配置入口在集成 → 监控插件</el-tag>
          </div>
          <ul class="hero-chips">
            <li
              v-for="chip in heroChips"
              :key="chip.label"
              :class="['hero-chip', chip.status]"
            >
              <span>{{ chip.label }}</span>
              <strong>{{ chip.value }}</strong>
              <small>{{ chip.subtitle }}</small>
            </li>
          </ul>
          <el-alert
            v-if="error"
            type="error"
            :closable="false"
            show-icon
            class="hero-alert"
          >
            {{ error }}
          </el-alert>
        </div>
        <div class="hero-visual">
          <div class="holo-radar">
            <span class="radar-ring ring-1" />
            <span class="radar-ring ring-2" />
            <span class="radar-pulse" />
            <div class="radar-core">
              <span class="radar-label">{{ radarStat.label }}</span>
              <span class="radar-value">{{ radarStat.value }}</span>
              <small>{{ radarStat.subtitle }}</small>
            </div>
          </div>
          <div class="hero-secondary">
            <div
              v-for="card in heroSecondaryCards"
              :key="card.label"
              class="secondary-card"
            >
              <span>{{ card.label }}</span>
              <strong>{{ card.value }}</strong>
              <small>{{ card.subtitle }}</small>
            </div>
          </div>
        </div>
      </div>
      <div class="hero-metrics">
        <div v-for="card in overviewCards" :key="card.label" class="metric-card glass-card">
          <span class="metric-label">{{ card.label }}</span>
          <span class="metric-value">{{ card.value }}</span>
          <span class="metric-subtitle">{{ card.subtitle }}</span>
        </div>
      </div>
    </section>

    <el-row :gutter="20">
      <el-col :md="12" :xs="24">
        <section class="glass-card trigger-panel">
          <div class="panel-header">
            <div>
              <h3>触发器问题概览</h3>
              <p class="muted">聚焦当前处于问题状态的触发器</p>
            </div>
            <el-tag effect="dark" type="danger">
              {{ triggerStats.problem }} 条问题
            </el-tag>
          </div>
          <div class="trigger-metric">
            <span class="metric-hint">问题触发器</span>
            <strong>{{ triggerStats.problem }}</strong>
            <small>触发器总数 {{ triggerStats.total }}</small>
          </div>
        </section>
      </el-col>
      <el-col :md="12" :xs="24">
        <section class="glass-card system-panel">
          <div class="panel-header">
            <div>
              <h3>系统信息</h3>
              <p class="muted">Zabbix 服务运行状态与统计</p>
            </div>
          </div>
          <dl class="system-list">
            <div class="system-row">
              <dt>Zabbix 服务器端运行中</dt>
              <dd>
                <strong>{{ systemInfo.is_running ? '是' : '否' }}</strong>
                <small>{{ systemInfo.server_address }}</small>
              </dd>
            </div>
            <div class="system-row">
              <dt>Zabbix 服务端版本</dt>
              <dd>
                <strong>{{ systemInfo.server_version }}</strong>
                <small v-if="systemInfo.latest_release">最新 {{ systemInfo.latest_release }}</small>
              </dd>
            </div>
            <div class="system-row">
              <dt>Zabbix 前端版本</dt>
              <dd>
                <strong>{{ systemInfo.frontend_version }}</strong>
                <small>Matching server build</small>
              </dd>
            </div>
            <div class="system-row">
              <dt>Software update last checked</dt>
              <dd>
                <strong>{{ formatTimestamp(systemInfo.update_checked_at) }}</strong>
              </dd>
            </div>
            <div class="system-row">
              <dt>Latest release</dt>
              <dd>
                <strong>{{ systemInfo.latest_release || '—' }}</strong>
                <small v-if="systemInfo.latest_release_notes">
                  <a :href="systemInfo.latest_release_notes" target="_blank" rel="noopener">Release notes</a>
                </small>
              </dd>
            </div>
            <div
              v-for="row in systemStatRows"
              :key="row.label"
              class="system-row"
            >
              <dt>{{ row.label }}</dt>
              <dd>
                <strong>{{ row.value }}</strong>
                <small>{{ row.detail }}</small>
              </dd>
            </div>
          </dl>
        </section>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :md="15" :xs="24">
        <div class="glass-card alerts-panel" v-loading="sectionLoading">
          <div class="panel-header">
            <div>
              <h3>实时问题告警</h3>
              <p class="muted">从 Zabbix 拉取的高优先级问题会自动聚合于此。</p>
            </div>
            <el-tag effect="dark" :type="alertProblems.length ? 'danger' : 'success'">
              {{ alertProblems.length }} 条严重告警
            </el-tag>
          </div>
          <el-empty
            v-if="!alertProblems.length && !sectionLoading"
            description="暂无告警"
            class="dark-empty"
          />
          <div v-else class="dark-table-shell">
            <el-table
              :data="alertProblems"
              height="280"
              class="dark-table"
              stripe
            >
              <el-table-column prop="severity" label="级别" width="120">
                <template #default="{ row }">
                  <el-tag :type="row.severity === 'Disaster' ? 'danger' : 'warning'" effect="dark">
                    {{ row.severity }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="host" label="主机" width="180" />
              <el-table-column prop="message" label="告警信息" min-width="220" />
              <el-table-column prop="duration" label="持续时长" width="140" />
            </el-table>
          </div>
        </div>
      </el-col>
      <el-col :md="9" :xs="24">
        <div class="glass-card signal-panel" v-loading="sectionLoading">
          <div class="panel-header">
            <div>
              <h3>告警等级分布</h3>
              <p class="muted">聚焦当前开放 Problem 的严重度结构</p>
            </div>
          </div>
          <ul class="severity-list">
            <li v-for="item in severityList" :key="item.label">
              <div class="severity-info">
                <strong>{{ item.label }}</strong>
                <small>{{ item.hint }}</small>
              </div>
              <div class="severity-bar">
                <span
                  class="severity-fill"
                  :class="item.tone"
                  :style="{ width: item.percent + '%' }"
                />
              </div>
              <span class="severity-value">{{ item.value }}</span>
            </li>
          </ul>
        </div>
      </el-col>
    </el-row>

    <section class="glass-card history-panel" v-loading="sectionLoading">
      <div class="panel-header">
        <div>
          <h3>同步任务记录</h3>
          <p class="muted">追踪最近一次同步耗时与结果，辅助定位故障。</p>
        </div>
      </div>
      <el-empty
        v-if="!syncHistory.length && !sectionLoading"
        description="暂无记录"
        class="dark-empty"
      />
      <div v-else class="dark-table-shell">
        <el-table
          :data="syncHistory"
          class="dark-table"
          height="220"
          stripe
        >
          <el-table-column prop="time" label="同步时间" width="180" />
          <el-table-column prop="scope" label="范围" width="180" />
          <el-table-column prop="duration" label="耗时" width="140" />
          <el-table-column prop="result" label="结果" width="140">
            <template #default="{ row }">
              <el-tag :type="row.result === '成功' ? 'success' : 'warning'" effect="dark">
                {{ row.result }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="备注" min-width="220" />
        </el-table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { isAxiosError } from 'axios';

import apiClient from '@/services/apiClient';
import { useSessionStore } from '@/stores/session';
import {
  fetchZabbixDashboard,
  testZabbixConnection,
  triggerZabbixSync,
  type ZabbixDashboardMetrics,
  type ZabbixDashboardResponse,
  type ZabbixProxyStats,
  type ZabbixSeverityBreakdown,
  type ZabbixSystemInfo
} from '@/services/zabbixApi';

type SystemSettingsPayload = Record<string, any> & {
  zabbix_dashboard_refresh_seconds?: number;
};

const session = useSessionStore();
const canManageSystemSettings = computed(() => session.hasPermission('settings.system.manage'));

const refreshSettingsLoading = ref(false);
const refreshSettingsSaving = ref(false);
const systemSettingsSnapshot = ref<SystemSettingsPayload | null>(null);
const zabbixRefreshSeconds = ref<number>(60);


const loading = ref(false);
const sectionLoading = ref(false);
const testing = ref(false);
const syncing = ref(false);
const error = ref<string | null>(null);
const dashboard = ref<ZabbixDashboardResponse | null>(null);

const fallbackMetrics: ZabbixDashboardMetrics = {
  total_hosts: 0,
  problem_hosts: 0,
  open_problems: 0,
  avg_problem_age_seconds: 0,
  available_hosts: 0,
  unavailable_hosts: 0,
  maintenance_hosts: 0
};

const fallbackProxyStats: ZabbixProxyStats = {
  total: 0,
  online: 0,
  offline: 0
};

const fallbackSystemInfo: ZabbixSystemInfo = {
  is_running: false,
  server_address: '—',
  server_version: '—',
  frontend_version: '—',
  update_checked_at: '—',
  latest_release: '—',
  latest_release_notes: '',
  hosts_enabled: 0,
  hosts_disabled: 0,
  triggers_total: 0,
  triggers_problem: 0,
  users_total: 0,
  users_online: 0,
  ha_status: 'disabled'
};

const fallbackSeverityBreakdown: ZabbixSeverityBreakdown = {
  disaster: 0,
  high: 0,
  average: 0,
  warning: 0,
  information: 0
};

const severityConfig: Array<{
  key: keyof ZabbixSeverityBreakdown;
  label: string;
  hint: string;
  tone: 'danger' | 'warn' | 'pulse' | 'info' | 'muted';
}> = [
  { key: 'disaster', label: '灾难', hint: '生产中断', tone: 'danger' },
  { key: 'high', label: '高', hint: '核心服务故障', tone: 'warn' },
  { key: 'average', label: '中', hint: '主要模块', tone: 'pulse' },
  { key: 'warning', label: '警告', hint: '关注观察', tone: 'info' },
  { key: 'information', label: '信息', hint: 'FYI', tone: 'muted' }
];

const formatSeconds = (value: number) => {
  if (!value) return '—';
  const seconds = Math.max(Math.round(value), 0);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remain = seconds % 60;
  if (minutes < 60) return `${minutes}m ${remain.toString().padStart(2, '0')}s`;
  const hours = Math.floor(minutes / 60);
  const minuteRemain = minutes % 60;
  return `${hours}h ${minuteRemain.toString().padStart(2, '0')}m`;
};

const metricSnapshot = computed(() => dashboard.value?.metrics ?? fallbackMetrics);
const proxyStats = computed(() => dashboard.value?.proxy_stats ?? fallbackProxyStats);
const systemInfo = computed(() => dashboard.value?.system_info ?? fallbackSystemInfo);
const severityBreakdown = computed(() => dashboard.value?.severity_breakdown ?? fallbackSeverityBreakdown);

const overviewCards = computed(() => {
  const metrics = metricSnapshot.value;
  const proxies = proxyStats.value;
  const total = metrics.total_hosts ?? 0;
  const available = metrics.available_hosts ?? 0;
  const availableRate = total ? Math.round((available / total) * 100) : 0;
  return [
    { label: '主机总数', value: total.toLocaleString(), subtitle: `可用率 ${availableRate}%` },
    { label: '开放告警', value: (metrics.open_problems ?? 0).toLocaleString(), subtitle: '实时 Problem' },
    { label: '平均告警持续', value: formatSeconds(metrics.avg_problem_age_seconds ?? 0), subtitle: '按开放问题计算' },
    {
      label: '代理在线率',
      value: proxies.total ? `${Math.round((proxies.online / proxies.total) * 100)}%` : '—',
      subtitle: `${proxies.online}/${proxies.total} Proxy`
    }
  ];
});

const heroChips = computed(() => {
  const metrics = metricSnapshot.value;
  const proxies = proxyStats.value;
  return [
    { label: '可用主机', value: (metrics.available_hosts ?? 0).toLocaleString(), subtitle: 'Agent 在线', status: 'ok' },
    { label: '不可用主机', value: (metrics.unavailable_hosts ?? 0).toLocaleString(), subtitle: '失联或故障', status: 'danger' },
    { label: '在线代理', value: `${proxies.online}/${proxies.total}`, subtitle: 'Proxy 心跳', status: 'pulse' }
  ];
});

const radarStat = computed(() => {
  const metrics = metricSnapshot.value;
  return {
    label: '开放告警',
    value: (metrics.open_problems ?? 0).toLocaleString(),
    subtitle: `平均持续 ${formatSeconds(metrics.avg_problem_age_seconds ?? 0)}`
  };
});

const heroSecondaryCards = computed(() => {
  const info = systemInfo.value;
  return [
    {
      label: '用户数量',
      value: (info.users_total ?? 0).toLocaleString(),
      subtitle: 'Zabbix 用户总数'
    },
    {
      label: 'HA 状态',
      value: info.ha_status === 'active' ? 'Active' : info.ha_status,
      subtitle: info.is_running ? 'Zabbix server 运行中' : 'Zabbix server离线'
    },
    {
      label: '最新版本',
      value: info.latest_release || '—',
      subtitle: 'Official release'
    }
  ];
});

const severityList = computed(() => {
  const stats = severityBreakdown.value;
  const total = Math.max(
    Object.values(stats).reduce((sum, value) => sum + value, 0),
    1
  );
  return severityConfig.map((item) => {
    const value = stats[item.key] ?? 0;
    return {
      ...item,
      value,
      percent: Math.round((value / total) * 100)
    };
  });
});

const alertProblems = computed(() => dashboard.value?.alerts ?? []);
const syncHistory = computed(() => dashboard.value?.sync_history ?? []);
const systemStatRows = computed(() => {
  const info = systemInfo.value;
  return [
    {
      label: '主机数量 (启用/禁用)',
      value: info.hosts_enabled + info.hosts_disabled,
      detail: `${info.hosts_enabled} / ${info.hosts_disabled}`
    },
    {
      label: '触发器问题数量',
      value: info.triggers_problem,
      detail: `触发器总数 ${info.triggers_total}`
    },
    {
      label: '用户数量',
      value: info.users_total,
      detail: 'Zabbix 用户总数'
    },
    {
      label: '高可用集群',
      value: info.ha_status === 'disabled' ? '停用' : info.ha_status,
      detail: info.is_running ? 'HA 模块反馈' : '服务器未运行'
    }
  ];
});

const formatTimestamp = (value: string) => {
  if (!value || value === '—') return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
};

const triggerStats = computed(() => ({
  total: systemInfo.value.triggers_total ?? 0,
  problem: systemInfo.value.triggers_problem ?? 0
}));

const resolveErrorMessage = (err: unknown) => {
  if (isAxiosError(err)) {
    return (err.response?.data?.detail as string) || err.message || '请求失败';
  }
  if (err instanceof Error) {
    return err.message;
  }
  return '未知错误';
};

const loadSystemSettingsSnapshot = async () => {
  if (!canManageSystemSettings.value) return;
  refreshSettingsLoading.value = true;
  try {
    const { data } = await apiClient.get<SystemSettingsPayload>('/settings/system');
    systemSettingsSnapshot.value = data;
    zabbixRefreshSeconds.value = Number(data.zabbix_dashboard_refresh_seconds ?? 60);
  } catch {
    // 没有权限或接口异常时，不影响 Zabbix 主页面使用
  } finally {
    refreshSettingsLoading.value = false;
  }
};

const handleUpdateRefreshSeconds = async (value: number | string) => {
  if (!canManageSystemSettings.value) return;
  const nextValue = Number(value);
  if (!Number.isFinite(nextValue)) return;

  const previous = zabbixRefreshSeconds.value;
  zabbixRefreshSeconds.value = nextValue;
  refreshSettingsSaving.value = true;
  try {
    if (!systemSettingsSnapshot.value) {
      await loadSystemSettingsSnapshot();
    }
    if (!systemSettingsSnapshot.value) {
      throw new Error('missing snapshot');
    }
    const payload: SystemSettingsPayload = { ...systemSettingsSnapshot.value, zabbix_dashboard_refresh_seconds: nextValue };
    const { data } = await apiClient.put<SystemSettingsPayload>('/settings/system', payload);
    systemSettingsSnapshot.value = data;
    zabbixRefreshSeconds.value = Number(data.zabbix_dashboard_refresh_seconds ?? nextValue);
    ElMessage.success('刷新频率已更新');
  } catch {
    zabbixRefreshSeconds.value = previous;
    ElMessage.error('刷新频率更新失败（可能需要管理员权限）');
  } finally {
    refreshSettingsSaving.value = false;
  }
};

const refreshDashboard = async (force = false) => {
  loading.value = true;
  sectionLoading.value = true;
  error.value = null;
  try {
    dashboard.value = await fetchZabbixDashboard(force);
  } catch (err) {
    error.value = resolveErrorMessage(err);
  } finally {
    loading.value = false;
    sectionLoading.value = false;
  }
};

const handleTestConnection = async () => {
  testing.value = true;
  try {
    const result = await testZabbixConnection();
    ElMessage.success(result.detail || 'Zabbix 连接测试通过');
  } catch (err) {
    ElMessage.error(resolveErrorMessage(err));
  } finally {
    testing.value = false;
  }
};

const handleSyncNow = async () => {
  syncing.value = true;
  try {
    await triggerZabbixSync();
    ElMessage.success('已触发主机同步任务，结果将显示在同步记录');
    await refreshDashboard(true);
  } catch (err) {
    ElMessage.error(resolveErrorMessage(err));
  } finally {
    syncing.value = false;
  }
};

onMounted(() => {
  refreshDashboard();
  loadSystemSettingsSnapshot();
});
</script>

<style scoped>
.zabbix-board {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
  padding: 2rem;
  background: radial-gradient(circle at 10% 20%, rgba(244, 114, 182, 0.22), transparent 55%),
    radial-gradient(circle at 80% 0%, rgba(34, 211, 238, 0.18), transparent 60%),
    linear-gradient(145deg, #04060f, #050317 60%, #010106 90%);
  border-radius: 30px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  color: #e0e9ff;
  overflow: hidden;
}

.zabbix-board::before,
.zabbix-board::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.zabbix-board::before {
  background: linear-gradient(0deg, rgba(255, 255, 255, 0.08), transparent 65%);
  mix-blend-mode: screen;
  opacity: 0.6;
}

.zabbix-board::after {
  background-image: linear-gradient(rgba(94, 234, 212, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(94, 234, 212, 0.08) 1px, transparent 1px);
  background-size: 140px 140px;
  transform: skewY(-6deg);
  opacity: 0.35;
  filter: drop-shadow(0 0 6px rgba(94, 234, 212, 0.25));
}

.zabbix-board :deep(.el-empty__description) {
  color: rgba(224, 233, 255, 0.9);
}

.zabbix-board :deep(.el-table),
.zabbix-board :deep(.el-table th),
.zabbix-board :deep(.el-table tr) {
  color: inherit;
}

.hero-panel {
  position: relative;
  padding: 1.75rem;
  border-radius: 22px;
  background: linear-gradient(125deg, rgba(10, 15, 37, 0.92), rgba(4, 6, 18, 0.9));
  border: 1px solid rgba(120, 168, 255, 0.2);
  box-shadow: 0 30px 60px rgba(4, 5, 18, 0.75);
  color: #dae3ff;
  overflow: hidden;
}

.hero-panel::before {
  content: '';
  position: absolute;
  inset: -20% 0 auto 0;
  height: 120%;
  background: radial-gradient(circle at 20% 20%, rgba(34, 211, 238, 0.18), transparent 55%);
  filter: blur(35px);
  opacity: 0.8;
}

.hero-grid {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 1fr);
  gap: 1.25rem;
}

.hero-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.hero-text h1 {
  margin: 0;
  font-size: clamp(1.8rem, 2.4vw, 2.8rem);
}

.hero-kicker {
  font-size: 0.85rem;
  letter-spacing: 0.45rem;
  color: rgba(94, 234, 212, 0.9);
  margin-bottom: 0.2rem;
}

.hero-subtitle {
  color: #9fb2ff;
  margin-top: 0.35rem;
}

.hero-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.refresh-select {
  width: 140px;
}

.refresh-select :deep(.el-select__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.25);
}

.refresh-select :deep(.el-select__selected-item) {
  color: rgba(224, 233, 255, 0.9);
}

.refresh-select :deep(.el-select__caret) {
  color: rgba(224, 233, 255, 0.75);
}

.hero-actions :deep(.el-button[color='#f472b6']) {
  box-shadow: 0 0 18px rgba(244, 114, 182, 0.5);
}

.hero-chips {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  list-style: none;
  margin: 0;
  padding: 0;
}

.hero-chip {
  padding: 0.9rem 1rem;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(6, 10, 22, 0.75);
  box-shadow: inset 0 0 12px rgba(34, 211, 238, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  text-transform: uppercase;
  font-size: 0.85rem;
  letter-spacing: 0.04em;
}

.hero-chip strong {
  font-size: 1.5rem;
  color: #fdf4ff;
}

.hero-chip small {
  color: rgba(203, 213, 225, 0.8);
  font-size: 0.75rem;
  text-transform: none;
  letter-spacing: 0.02em;
}

.hero-chip.ok {
  border-color: rgba(34, 211, 238, 0.4);
  text-shadow: 0 0 10px rgba(34, 211, 238, 0.6);
}

.hero-chip.danger {
  border-color: rgba(248, 113, 113, 0.4);
  text-shadow: 0 0 12px rgba(248, 113, 113, 0.6);
}

.hero-chip.warn {
  border-color: rgba(244, 114, 182, 0.4);
  text-shadow: 0 0 10px rgba(244, 114, 182, 0.6);
}

.hero-chip.pulse {
  border-color: rgba(190, 24, 93, 0.4);
  text-shadow: 0 0 10px rgba(190, 24, 93, 0.6);
}

.hero-metrics {
  margin-top: 1.25rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.9rem;
}

.hero-alert {
  margin-top: 0.5rem;
}

.glass-card {
  background: linear-gradient(140deg, rgba(4, 8, 20, 0.9), rgba(21, 8, 37, 0.85));
  border: 1px solid rgba(93, 140, 255, 0.2);
  border-radius: 20px;
  backdrop-filter: blur(16px);
  box-shadow: 0 25px 45px rgba(5, 9, 25, 0.65), inset 0 0 25px rgba(66, 153, 225, 0.1);
  position: relative;
  overflow: hidden;
}

.glass-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top right, rgba(255, 255, 255, 0.14), transparent 45%);
  opacity: 0.5;
  pointer-events: none;
}

.metric-card {
  padding: 1rem;
  min-height: 140px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.45rem;
}

.metric-label {
  color: rgba(166, 183, 255, 0.9);
  letter-spacing: 0.08em;
  font-size: 0.8rem;
}

.metric-value {
  font-size: 2.2rem;
  font-weight: 700;
  color: #5df2ff;
  text-shadow: 0 0 12px rgba(93, 242, 255, 0.8);
}

.metric-subtitle {
  color: #c4cffc;
  font-size: 0.85rem;
}

.alerts-panel,
.signal-panel,
.history-panel {
  padding: 1.25rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 0.8rem;
}

.muted {
  color: #96a5d8;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.hero-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}

.holo-radar {
  position: relative;
  width: min(260px, 70vw);
  aspect-ratio: 1 / 1;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.08), transparent 70%);
  border: 1px solid rgba(34, 211, 238, 0.4);
  box-shadow: 0 0 30px rgba(14, 165, 233, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.radar-core {
  text-align: center;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.radar-label {
  letter-spacing: 0.25em;
  font-size: 0.85rem;
  color: rgba(209, 213, 219, 0.9);
}

.radar-value {
  font-size: 2.8rem;
  font-weight: 700;
  color: #22d3ee;
  text-shadow: 0 0 30px rgba(34, 211, 238, 0.8);
}

.radar-ring {
  position: absolute;
  border: 1px solid rgba(34, 211, 238, 0.35);
  border-radius: 50%;
  inset: 10%;
  animation: spinRing 12s linear infinite;
}

.ring-2 {
  inset: 0;
  animation-direction: reverse;
  animation-duration: 16s;
}

.radar-pulse {
  position: absolute;
  width: 40%;
  height: 40%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(244, 114, 182, 0.25), transparent 70%);
  animation: radarPulse 4s ease-in-out infinite;
}

.hero-secondary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
  width: 100%;
}

.secondary-card {
  padding: 0.9rem 1rem;
  border-radius: 16px;
  border: 1px solid rgba(244, 114, 182, 0.3);
  background: rgba(43, 7, 35, 0.55);
  box-shadow: inset 0 0 18px rgba(244, 114, 182, 0.2);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.secondary-card span {
  font-size: 0.85rem;
  letter-spacing: 0.1em;
  color: #f9a8d4;
}

.secondary-card strong {
  font-size: 1.8rem;
  font-weight: 700;
  color: #fdf2f8;
}

.secondary-card small {
  color: rgba(249, 168, 212, 0.8);
}

.signal-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.severity-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.severity-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.severity-info small {
  color: rgba(148, 163, 184, 0.9);
}

.severity-list li {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) 1fr auto;
  gap: 0.75rem;
  align-items: center;
}

.severity-bar {
  position: relative;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.7);
  overflow: hidden;
}

.severity-fill {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  transition: width 0.3s ease;
  background: linear-gradient(90deg, rgba(34, 211, 238, 0.5), rgba(59, 130, 246, 0.8));
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.4);
}

.severity-fill.warn {
  background: linear-gradient(90deg, rgba(251, 191, 36, 0.45), rgba(249, 115, 22, 0.8));
  box-shadow: 0 0 12px rgba(251, 191, 36, 0.35);
}

.severity-fill.pulse {
  background: linear-gradient(90deg, rgba(244, 114, 182, 0.45), rgba(147, 51, 234, 0.85));
  box-shadow: 0 0 12px rgba(244, 114, 182, 0.35);
}

.severity-fill.danger {
  background: linear-gradient(90deg, rgba(248, 113, 113, 0.5), rgba(190, 24, 93, 0.85));
  box-shadow: 0 0 12px rgba(248, 113, 113, 0.45);
}

.severity-fill.info {
  background: linear-gradient(90deg, rgba(96, 165, 250, 0.45), rgba(14, 165, 233, 0.85));
}

.severity-fill.muted {
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.35), rgba(148, 163, 184, 0.6));
}

.severity-value {
  font-weight: 600;
  color: #f8fafc;
  font-size: 1.1rem;
}

.trigger-panel {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.trigger-metric {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 1rem;
  background: rgba(10, 16, 34, 0.6);
  text-align: center;
}

.trigger-metric strong {
  font-size: 2.8rem;
  color: #f87171;
  letter-spacing: 0.08em;
}

.metric-hint {
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: rgba(203, 213, 225, 0.9);
  font-size: 0.8rem;
}

.trigger-metric small {
  color: rgba(203, 213, 225, 0.8);
}

.system-panel {
  padding: 1.25rem 1.5rem;
}

.system-list {
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.system-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  padding-bottom: 0.65rem;
}

.system-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.system-row dt {
  margin: 0;
  color: #c9d8ff;
  font-size: 0.95rem;
}

.system-row dd {
  margin: 0;
  text-align: right;
}

.system-row strong {
  display: block;
  font-size: 1.15rem;
  color: #f8fafc;
}

.system-row small,
.system-row a {
  color: rgba(148, 163, 184, 0.9);
  font-size: 0.8rem;
}

.system-row a {
  text-decoration: underline;
}

.dark-table {
  position: relative;
  isolation: isolate;
}

.dark-table::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top, rgba(64, 158, 255, 0.08), transparent 60%);
  pointer-events: none;
  z-index: 0;
}

.dark-table :deep(.el-table),
.dark-table :deep(.el-table__inner-wrapper),
.dark-table :deep(.el-table__header-wrapper),
.dark-table :deep(.el-table__body-wrapper),
.dark-table :deep(.el-table__footer-wrapper) {
  background: rgba(5, 7, 16, 0.85) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}

.dark-table :deep(.el-table__body),
.dark-table :deep(.el-table__body tr),
.dark-table :deep(.el-table__body td) {
  background: transparent !important;
}

.dark-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: rgba(14, 20, 40, 0.6) !important;
}

.dark-table :deep(.el-table__inner-wrapper::before),
.dark-table :deep(.el-table__inner-wrapper::after),
.dark-table :deep(.el-table::before),
.dark-table :deep(.el-table__border-left-patch) {
  display: none !important;
}

.dark-table :deep(th),
.dark-table :deep(td) {
  background-color: transparent !important;
  color: #d6deff;
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.dark-table :deep(.el-table__header th) {
  background-color: rgba(11, 19, 38, 0.85) !important;
  color: #9fb2e4;
}

.dark-table :deep(.el-table__row:hover > td) {
  background: rgba(80, 143, 255, 0.09) !important;
}

.dark-table-shell {
  background: linear-gradient(160deg, rgba(6, 12, 28, 0.9), rgba(10, 18, 36, 0.82));
  border: 1px solid rgba(72, 114, 255, 0.18);
  border-radius: 16px;
  padding: 0.35rem;
  box-shadow: inset 0 0 35px rgba(7, 12, 31, 0.55);
}

.dark-empty {
  width: 100%;
  margin-top: 0.5rem;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(6, 12, 28, 0.92), rgba(10, 18, 36, 0.85));
  border: 1px dashed rgba(121, 150, 255, 0.35);
  color: #aab7ff;
  padding: 1.5rem 0;
}

.dark-empty :deep(.el-empty__description) {
  color: #9fb2ff;
}

@keyframes spinRing {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes radarPulse {
  0% {
    transform: scale(0.8);
    opacity: 0.8;
  }
  70% {
    transform: scale(1.2);
    opacity: 0.2;
  }
  100% {
    transform: scale(0.8);
    opacity: 0.8;
  }
}

@media (max-width: 768px) {
  .zabbix-board {
    padding: 1.25rem;
  }

  .hero-grid {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-chip {
    text-align: center;
  }

  .hero-visual {
    margin-top: 0.5rem;
  }
}
</style>
