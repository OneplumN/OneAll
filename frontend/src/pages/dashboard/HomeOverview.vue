<template>
  <div class="dashboard-overview">
    <div class="header">
      <div>
        <h1>实时监控驾驶舱</h1>
        <p class="subtitle">掌握探针运行状态与关键拨测指标</p>
      </div>
      <div class="actions">
        <el-button type="primary" :loading="loading" @click="refreshDashboard">刷新数据</el-button>
        <span v-if="metrics" class="timestamp">最近更新：{{ formattedUpdatedAt }}</span>
      </div>
    </div>

    <el-alert v-if="error" type="error" show-icon :closable="false" class="mb-3">
      {{ error }}
    </el-alert>

    <el-row :gutter="16" class="metric-row">
      <el-col v-for="item in probeCards" :key="item.label" :xs="24" :sm="12" :lg="6">
        <el-card class="glass-card metric-card" shadow="never" data-test="overview-metric-card">
          <span class="metric-label">{{ item.label }}</span>
          <span class="metric-value">{{ item.value }}</span>
        </el-card>
      </el-col>
    </el-row>

    <div class="glass-card charts-panel" v-if="metrics">
      <OverviewCharts
        :detection="metrics.detection"
        :incidents="metrics.incidents"
      />
    </div>

    <section class="honeycomb-section">
      <div class="honeycomb-header">
        <div>
          <h2>域名拨测蜂窝图</h2>
          <p class="muted">根据一次性拨测任务实时展示各域名的预期状态。</p>
        </div>
        <span class="honeycomb-meta">
          共 {{ detectionGrid.length }} 条任务
        </span>
      </div>
      <DetectionHoneycomb :cells="honeycombCells" @select="handleCellSelect" />
      <el-alert
        v-if="detectionGridError"
        type="warning"
        :closable="false"
        show-icon
        class="honeycomb-alert"
      >
        {{ detectionGridError }}
      </el-alert>
    </section>

    <section class="probe-alerts glass-card">
      <RecentAlertsPanel
        :alerts="probeAlerts"
        :loading="probeAlertsLoading"
        @refresh="fetchProbeAlerts"
        @view-logs="goToProbeLogs"
      />
      <el-alert
        v-if="probeAlertsError"
        type="warning"
        :closable="false"
        show-icon
        class="probe-alerts__error"
      >
        {{ probeAlertsError }}
      </el-alert>
    </section>

    <section class="certificate-section glass-card">
      <div class="certificate-header">
        <div>
          <h3>证书有效期监测</h3>
          <p class="muted">跟踪临近过期的证书并提前规划续签。</p>
        </div>
          <el-tag size="large" effect="dark" type="warning">
            {{ certificateAlerts.length }} 个待关注
          </el-tag>
        </div>
        <div class="certificate-grid">
          <div
            v-for="cert in certificateAlerts"
            :key="cert.id"
            class="certificate-item"
          >
            <div class="certificate-domain">
              <span>{{ cert.domain }}</span>
              <small>{{ cert.issuer || '—' }}</small>
            </div>
            <div class="certificate-days" :class="certificateLevel(cert.days_remaining)">
              <span>{{ cert.days_remaining ?? '—' }}</span>
              <small>天剩余</small>
            </div>
          </div>
        </div>
        <el-alert
          v-if="certificateError"
          type="warning"
          :closable="false"
          show-icon
          class="certificate-alert"
        >
          {{ certificateError }}
        </el-alert>
      </section>

    <el-row :gutter="16" class="summary-row">
      <el-col :xs="24" :md="12">
        <div class="glass-card summary-panel">
          <AlertSummary :summary="alerts" :loading="alertsLoading" :error="alertsError" />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="glass-card summary-panel">
          <TodoList :summary="todos" :loading="todosLoading" :error="todosError" />
        </div>
      </el-col>
    </el-row>

    <el-dialog
      v-model="detailDialogVisible"
      :title="detailLabel + ' 拨测详情'"
      width="520px"
    >
      <el-descriptions v-if="detailRecord" :column="1" border>
        <el-descriptions-item label="业务系统">
          {{ detailRecord.system_name || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="域名">
          {{ detailRecord.domain }}
        </el-descriptions-item>
        <el-descriptions-item label="预期状态码">
          <span>{{ formatExpected(detailRecord.expected_status) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="实际状态码">
          <span :class="['status-chip', `status-chip--${deriveStatus(detailRecord.actual_status ?? undefined, detailRecord.expected_status)}`]">
            {{ detailRecord.actual_status ?? '—' }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="响应时间">
          {{ detailRecord.response_ms != null ? detailRecord.response_ms + ' ms' : '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="探针/节点">
          {{ detailRecord.probe || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="拨测时间">
          {{ detailRecord.checked_at ? new Date(detailRecord.checked_at).toLocaleString() : '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="说明">
          {{ detailRecord.status_message || '—' }}
        </el-descriptions-item>
      </el-descriptions>
      <el-empty v-else description="暂无详情" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
	import { computed, onMounted, ref } from 'vue';
	import { useRouter } from 'vue-router';

	import { fetchDashboardAlerts, fetchDashboardOverview, fetchDashboardTodos, fetchCertificateAlerts, fetchDetectionGrid } from '@/services/dashboardApi';
	import type {
	  DashboardAlertSummary,
	  DashboardOverviewMetrics,
	  DashboardTodoSummary,
	  CertificateAlertSummary,
	  DetectionTaskStatus
	} from '@/types/dashboard';
	import { fetchRecentProbeAlerts, type ProbeAlertRecord } from '@/services/probeAlertApi';

import OverviewCharts from './components/OverviewCharts.vue';
import AlertSummary from './components/AlertSummary.vue';
import TodoList from './components/TodoList.vue';
import DetectionHoneycomb, { type HoneycombCell } from './components/DetectionHoneycomb.vue';
import RecentAlertsPanel from '@/pages/probes/components/RecentAlertsPanel.vue';

const loading = ref(false);
const error = ref<string | null>(null);
const metrics = ref<DashboardOverviewMetrics | null>(null);
const router = useRouter();

const alerts = ref<DashboardAlertSummary | null>(null);
const alertsLoading = ref(false);
const alertsError = ref<string | null>(null);

const todos = ref<DashboardTodoSummary | null>(null);
const todosLoading = ref(false);
const todosError = ref<string | null>(null);

	const detectionGrid = ref<DetectionTaskStatus[]>([]);
	const detectionGridError = ref<string | null>(null);
const detailDialogVisible = ref(false);
const detailRecord = ref<DetectionTaskStatus | null>(null);
const detailLabel = ref('');
const probeAlerts = ref<ProbeAlertRecord[]>([]);
const probeAlertsLoading = ref(false);
const probeAlertsError = ref<string | null>(null);

	const certificateSummary = ref<CertificateAlertSummary | null>(null);
	const certificateError = ref<string | null>(null);
	const certificateAlerts = computed(() => certificateSummary.value?.items || []);

const formattedUpdatedAt = computed(() => {
  if (!metrics.value) return '';
  const date = new Date(metrics.value.generated_at);
  return date.toLocaleString();
});

const probeCards = computed(() => {
  if (!metrics.value) {
    return [
      { label: '在线探针', value: '-' },
      { label: '离线探针', value: '-' },
      { label: '待处理告警', value: '-' },
      { label: '近 24h 拨测', value: '-' }
    ];
  }

  return [
    { label: '在线探针', value: metrics.value.probes.active },
    { label: '离线探针', value: metrics.value.probes.offline },
    { label: '待处理告警', value: metrics.value.incidents.open },
    { label: '近 24h 拨测', value: metrics.value.detection.last_24h_runs }
  ];
});

type HoneycombStatus = 'success' | 'warning' | 'danger' | 'idle';

const honeycombCells = computed<HoneycombCell[]>(() => {
  if (!detectionGrid.value.length) {
    return [
      { id: 'idle-1', label: '任务 #1', value: '--', status: 'idle' },
      { id: 'idle-2', label: '任务 #2', value: '--', status: 'idle' },
      { id: 'idle-3', label: '任务 #3', value: '--', status: 'idle' },
      { id: 'idle-4', label: '任务 #4', value: '--', status: 'idle' }
    ];
  }

  const prefixCounter: Record<string, number> = {};
  return detectionGrid.value.map((task) => {
    const prefix = extractDomainPrefix(task.domain);
    prefixCounter[prefix] = (prefixCounter[prefix] ?? 0) + 1;
    const label = `${prefix} #${prefixCounter[prefix]}`;
    const actual = task.actual_status ?? undefined;
    const expected = task.expected_status;
    const status = deriveStatus(actual, expected);
    const value = actual ? actual.toString() : '--';
    return {
      id: task.id,
      label,
      value,
      status,
      payload: task
    };
  });
});

	async function refreshDashboard() {
	  loading.value = true;
	  alertsLoading.value = true;
	  todosLoading.value = true;
	  probeAlertsLoading.value = true;
	  error.value = null;
	  alertsError.value = null;
	  todosError.value = null;
	  probeAlertsError.value = null;
	  certificateError.value = null;

	  const results = await Promise.allSettled([
	    fetchDashboardOverview(),
	    fetchDashboardAlerts(),
	    fetchDashboardTodos(),
	    fetchDetectionGrid(),
	    fetchCertificateAlerts(),
	    fetchRecentProbeAlerts(8)
	  ]);

	  const [overviewResult, alertResult, todoResult, detectionResult, certificateResult, probeAlertResult] = results;

  if (overviewResult.status === 'fulfilled') {
    metrics.value = overviewResult.value;
  } else {
    error.value = '无法获取驾驶舱数据，请稍后重试。';
  }

  if (alertResult.status === 'fulfilled') {
    alerts.value = alertResult.value;
  } else {
    alertsError.value = '无法加载告警摘要。';
  }

  if (todoResult.status === 'fulfilled') {
    todos.value = todoResult.value;
  } else {
    todosError.value = '无法加载待办事项。';
  }

	  if (detectionResult.status === 'fulfilled') {
	    detectionGrid.value = detectionResult.value;
	    detectionGridError.value = null;
	  } else {
	    detectionGridError.value = '无法加载域名拨测任务';
	    detectionGrid.value = [];
	  }

	  if (certificateResult.status === 'fulfilled') {
	    certificateSummary.value = certificateResult.value;
	    certificateError.value = null;
	  } else {
	    certificateError.value = '无法加载证书提醒数据';
	    certificateSummary.value = { generated_at: '', thresholds: { critical: 15, warning: 30, notice: 45 }, items: [] };
	  }

	  if (probeAlertResult.status === 'fulfilled') {
	    probeAlerts.value = probeAlertResult.value;
	    probeAlertsError.value = null;
	  } else {
	    probeAlerts.value = [];
	    probeAlertsError.value = '无法加载探针告警';
	  }

	  loading.value = false;
	  alertsLoading.value = false;
	  todosLoading.value = false;
	  probeAlertsLoading.value = false;
	}

onMounted(() => {
  refreshDashboard();
});

function extractDomainPrefix(domain: string): string {
  if (!domain) return '任务';
  let host = domain.trim();
  if (host.startsWith('http://') || host.startsWith('https://')) {
    try {
      host = new URL(host).host;
    } catch {
      host = host.replace(/^https?:\/\//, '').split('/')[0];
    }
  } else {
    host = host.split('/')[0];
  }
  const prefix = host.split('.')[0];
  return prefix || host;
}

function deriveStatus(actual?: number, expected?: number | number[] | null): HoneycombStatus {
  if (actual == null) return 'warning';
  if (matchesExpected(actual, expected)) return 'success';
  if (actual >= 400 && actual < 500) return 'warning';
  return 'danger';
}

function matchesExpected(actual: number, expected?: number | number[] | null): boolean {
  if (expected == null) {
    return actual >= 200 && actual < 300;
  }
  if (Array.isArray(expected)) {
    return expected.includes(actual);
  }
  return actual === expected;
}

function formatExpected(expected?: number | number[] | null): string {
  if (expected == null) return '—';
  if (Array.isArray(expected)) {
    return expected.join(', ');
  }
  return expected.toString();
}

async function fetchProbeAlerts() {
  probeAlertsLoading.value = true;
  probeAlertsError.value = null;
  try {
    probeAlerts.value = await fetchRecentProbeAlerts(8);
  } catch (error) {
    console.error(error);
    probeAlertsError.value = '无法加载探针告警';
  } finally {
    probeAlertsLoading.value = false;
  }
}

function goToProbeLogs() {
  router.push('/probes/logs');
}

	function certificateLevel(days: number | null | undefined) {
	  if (days == null) return 'warning';
	  const thresholds = certificateSummary.value?.thresholds;
	  const critical = thresholds?.critical ?? 15;
	  const warning = thresholds?.warning ?? 30;
	  const notice = thresholds?.notice ?? 45;
	  if (days < 0) return 'danger';
	  if (days <= critical) return 'danger';
	  if (days <= warning) return 'warning';
	  if (days <= notice) return 'info';
	  return 'success';
	}

const handleCellSelect = (cell: HoneycombCell) => {
  const record = (cell as HoneycombCell & { payload?: DetectionTaskStatus }).payload ?? null;
  detailRecord.value = record;
  detailLabel.value = cell.label;
  if (record) {
    detailDialogVisible.value = true;
  }
};
</script>

<style scoped>
.dashboard-overview {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  background: radial-gradient(circle at top, rgba(55, 110, 255, 0.18), transparent),
    linear-gradient(135deg, #050816 0%, #0b1124 45%, #050812 100%);
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: 0 35px 60px rgba(2, 6, 23, 0.65);
  position: relative;
  overflow: hidden;
}

.dashboard-overview::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.08), transparent 35%),
    radial-gradient(circle at 80% -10%, rgba(84, 178, 255, 0.12), transparent 45%);
  pointer-events: none;
  opacity: 0.7;
}

.dashboard-overview > * {
  position: relative;
  z-index: 1;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.subtitle {
  color: #c5d2ff;
  margin-top: 0.25rem;
}

.actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.timestamp {
  color: #94a3c9;
  font-size: 0.875rem;
}

.metric-row {
  margin-bottom: 1rem;
}

.glass-card {
  background: rgba(18, 27, 55, 0.55);
  border: 1px solid rgba(117, 182, 255, 0.15);
  border-radius: 20px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(18px);
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-height: 130px;
  justify-content: center;
  padding: 1rem;
}

.metric-label {
  color: #c7d3ff;
  letter-spacing: 0.03em;
}

.metric-value {
  font-size: 2.3rem;
  font-weight: 700;
  color: #66f0ff;
  text-shadow: 0 0 14px rgba(102, 240, 255, 0.5);
}

.mb-3 {
  margin-bottom: 1rem;
}

.charts-panel {
  padding: 0.75rem 1rem;
}

.summary-row {
  margin-top: 0.5rem;
}

.summary-panel {
  padding: 1rem;
}

.summary-panel :deep(.el-card),
.summary-panel :deep(.el-alert) {
  background: transparent;
  border: none;
}

.summary-panel :deep(.el-table) {
  background: transparent;
  color: #dce4ff;
}

.summary-panel :deep(.el-table th),
.summary-panel :deep(.el-table tr) {
  background: transparent;
  color: #aeb8da;
}

.summary-panel :deep(.el-table__row:hover > td) {
  background: rgba(255, 255, 255, 0.03);
}

.summary-panel :deep(.el-table__body tr:nth-child(odd) > td) {
  background: rgba(255, 255, 255, 0.01);
}

.probe-alerts {
  margin: 1.5rem 0;
}

.probe-alerts__error {
  margin-top: 0.5rem;
}

.honeycomb-section {
  background: linear-gradient(135deg, #0f172a, #111827);
  border-radius: 16px;
  padding: 1.5rem;
  color: #f8fafc;
}

.honeycomb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.honeycomb-header h2 {
  margin: 0;
  font-size: 20px;
}

.muted {
  margin: 0.25rem 0 0;
  color: #cbd5f5;
  font-size: 13px;
}

.honeycomb-meta {
  font-size: 13px;
  color: #94a3b8;
}

.honeycomb-alert {
  margin-top: 1rem;
}

.certificate-section {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.certificate-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.certificate-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
}

.certificate-alert {
  margin-top: 1rem;
}

.certificate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1rem;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.certificate-item:hover {
  transform: translateY(-4px);
  border-color: rgba(102, 240, 255, 0.3);
}

.certificate-domain {
  display: flex;
  flex-direction: column;
  color: #d7e2ff;
}

.certificate-domain small {
  color: #99a8d7;
  margin-top: 0.15rem;
}

.certificate-days {
  text-align: right;
}

.certificate-days span {
  font-size: 1.5rem;
  font-weight: 700;
  display: block;
}

.certificate-days small {
  color: #bfc9ed;
  font-size: 0.85rem;
}

.certificate-days.success span {
  color: #67c23a;
}

	.certificate-days.warning span {
	  color: #f7c948;
	}

	.certificate-days.info span {
	  color: #409eff;
	}

	.certificate-days.danger span {
	  color: #ff6b6b;
	}

.status-chip {
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  height: 24px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.status-chip--success {
  background: #27ae60;
}

.status-chip--warning {
  background: #e6a23c;
}

.status-chip--danger {
  background: #f56c6c;
}

.status-chip--idle {
  background: #909399;
}
</style>
