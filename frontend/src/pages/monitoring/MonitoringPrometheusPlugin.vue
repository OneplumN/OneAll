<template>
  <div class="prometheus-board page-card">
    <section class="hero-panel">
      <div class="hero-text">
        <h1>Prometheus 驾驶舱</h1>
        <p class="hero-subtitle">洞察采集目标、规则引擎与远程写入状态，保障拨测指标链路稳定。</p>
      </div>
      <div class="hero-actions">
        <el-button color="#34d399" plain :loading="testing" @click="handleTestApi">
          API 连通性
        </el-button>
        <el-button color="#f97316" plain :loading="reloading" @click="handleReloadRules">
          刷新规则
        </el-button>
        <el-tag effect="dark" type="info">配置入口：集成 → 监控插件</el-tag>
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
      <el-col :md="15" :xs="24">
        <div class="glass-card scrape-panel">
          <div class="panel-header">
            <div>
              <h3>抓取目标健康度</h3>
              <p class="muted">监控 domain / certificate / cmdb 任务的抓取延迟与离线率。</p>
            </div>
            <el-tag effect="dark" :type="scrapeSummary.tag">{{ scrapeSummary.label }}</el-tag>
          </div>
          <el-table :data="scrapeTargets" height="280" class="dark-table" stripe>
            <el-table-column prop="job" label="Job" width="150" />
            <el-table-column prop="total" label="目标数" width="100" />
            <el-table-column prop="healthy" label="健康" width="90">
              <template #default="{ row }">
                <el-tag type="success" effect="dark">{{ row.healthy }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="unhealthy" label="异常" width="90">
              <template #default="{ row }">
                <el-tag type="danger" effect="dark">{{ row.unhealthy }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="latency" label="P95 延迟" width="120" />
            <el-table-column prop="lastScrape" label="最近抓取" min-width="140" />
          </el-table>
        </div>
      </el-col>
      <el-col :md="9" :xs="24">
        <div class="glass-card rule-panel">
          <div class="panel-header">
            <div>
              <h3>告警规则触发</h3>
              <p class="muted">Prometheus Alertmanager 最近 24h 触发记录。</p>
            </div>
            <el-tag effect="dark" type="warning">{{ firingRules.length }} 条活跃</el-tag>
          </div>
          <ul class="rule-list">
            <li v-for="rule in firingRules" :key="rule.id">
              <div class="rule-title">
                <span>{{ rule.name }}</span>
                <el-tag :type="rule.severity === 'critical' ? 'danger' : 'warning'" size="small" effect="dark">
                  {{ rule.severity === 'critical' ? '高' : '中' }}
                </el-tag>
              </div>
              <p class="rule-desc">{{ rule.summary }}</p>
              <div class="rule-meta">
                <span>最近触发：{{ rule.lastFiring }}</span>
                <span>{{ rule.duration }}</span>
              </div>
            </li>
          </ul>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :md="10" :xs="24">
        <div class="glass-card storage-panel">
          <div class="panel-header">
            <div>
              <h3>时序存储</h3>
              <p class="muted">容量与基数控制情况</p>
            </div>
          </div>
          <div class="storage-body">
            <div class="storage-progress">
              <span>使用率 {{ storageUsage.usedPercent }}%</span>
              <el-progress
                :percentage="storageUsage.usedPercent"
                :stroke-width="12"
                :color="storageUsage.usedPercent > 80 ? '#f87171' : '#10b981'"
                striped
                striped-flow
              />
            </div>
            <ul class="storage-meta">
              <li>
                <label>保留策略</label>
                <span>{{ storageUsage.retention }}</span>
              </li>
              <li>
                <label>活跃时序</label>
                <span>{{ storageUsage.cardinality }}</span>
              </li>
              <li>
                <label>压缩状态</label>
                <span>{{ storageUsage.compaction }}</span>
              </li>
            </ul>
          </div>
        </div>
      </el-col>
      <el-col :md="14" :xs="24">
        <div class="glass-card remote-panel">
          <div class="panel-header">
            <div>
              <h3>远程写入链路</h3>
              <p class="muted">Timescale / Kafka 等下游同步状况</p>
            </div>
            <el-tag effect="dark" type="success">{{ remoteStreams.length }} 条连接</el-tag>
          </div>
          <el-table :data="remoteStreams" class="dark-table" height="220" stripe>
            <el-table-column prop="target" label="目标" width="170" />
            <el-table-column prop="status" label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : row.status === 'lagging' ? 'warning' : 'danger'" effect="dark">
                  {{ statusCopy(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="throughput" label="写入速率" width="140" />
            <el-table-column prop="lag" label="延迟" width="120" />
            <el-table-column prop="lastSync" label="最近同步" min-width="150" />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <section class="glass-card query-panel">
      <div class="panel-header">
        <div>
          <h3>查询体验</h3>
          <p class="muted">Grafana / API 查询耗时概览</p>
        </div>
        <el-button text type="primary" @click="handleTestApi">刷新样本</el-button>
      </div>
      <div class="query-grid">
        <div v-for="card in queryHealth" :key="card.label" class="query-card">
          <span class="query-label">{{ card.label }}</span>
          <div class="query-value">{{ card.value }}</div>
          <small>{{ card.subtitle }}</small>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';

const testing = ref(false);
const reloading = ref(false);

const handleTestApi = async () => {
  testing.value = true;
  await new Promise((resolve) => setTimeout(resolve, 800));
  testing.value = false;
  ElMessage.success('Prometheus API 连通性正常');
};

const handleReloadRules = async () => {
  reloading.value = true;
  await new Promise((resolve) => setTimeout(resolve, 1200));
  reloading.value = false;
  ElMessage.success('已触发规则热加载');
};

const overviewCards = [
  { label: '抓取目标', value: '128', subtitle: '在线 120 · 异常 8' },
  { label: '查询延迟 P95', value: '420 ms', subtitle: '较昨日 -12%' },
  { label: '样本写入速率', value: '1.8M / s', subtitle: '平均 32 MB/min' },
  { label: '存储使用率', value: '68%', subtitle: '保留 15 天' }
];

const scrapeTargets = [
  { job: 'domain_probe', total: 32, healthy: 30, unhealthy: 2, latency: '145 ms', lastScrape: '12 秒前' },
  { job: 'certificate_probe', total: 24, healthy: 22, unhealthy: 2, latency: '186 ms', lastScrape: '18 秒前' },
  { job: 'cmdb_probe', total: 18, healthy: 17, unhealthy: 1, latency: '210 ms', lastScrape: '22 秒前' },
  { job: 'probe_scheduler', total: 12, healthy: 12, unhealthy: 0, latency: '95 ms', lastScrape: '8 秒前' }
];

const scrapeSummary = computed(() => {
  const unhealthy = scrapeTargets.reduce((sum, job) => sum + job.unhealthy, 0);
  if (unhealthy > 6) return { label: '异常率偏高', tag: 'danger' as const };
  if (unhealthy > 0) return { label: '存在异常目标', tag: 'warning' as const };
  return { label: '全部健康', tag: 'success' as const };
});

const firingRules = [
  { id: 'rule-1', name: 'DomainProbeLatency', severity: 'warning', summary: '域名拨测延迟 > 3s', lastFiring: '09:21', duration: '持续 12 分钟' },
  { id: 'rule-2', name: 'CertificateExpiry', severity: 'warning', summary: '证书剩余 < 7 天', lastFiring: '08:44', duration: '持续 43 分钟' },
  { id: 'rule-3', name: 'ProbeNodeOffline', severity: 'critical', summary: '探针节点离线 > 5 个', lastFiring: '昨晚 23:02', duration: '持续 2 小时' }
];

const storageUsage = {
  usedPercent: 68,
  retention: '15 天',
  cardinality: '42 M 系列',
  compaction: '正常 · 12m/批'
};

const remoteStreams = [
  { target: 'Timescale-Prod', status: 'active', throughput: '2.3 MB/s', lag: '4 s', lastSync: '刚刚' },
  { target: 'Kafka-Bus', status: 'lagging', throughput: '1.1 MB/s', lag: '28 s', lastSync: '32 秒前' },
  { target: 'S3-Archive', status: 'paused', throughput: '—', lag: '—', lastSync: '02:13' }
];

const statusCopy = (status: 'active' | 'lagging' | 'paused') => {
  if (status === 'active') return '活跃';
  if (status === 'lagging') return '延迟';
  return '暂停';
};

const queryHealth = [
  { label: '查询 QPS', value: '420', subtitle: '慢查询 3 条' },
  { label: 'P99 延迟', value: '620 ms', subtitle: 'Grafana 平均值' },
  { label: '内存占用', value: '38 GB', subtitle: 'TSDB + Query' },
  { label: '规则评估', value: '2.4k ops/s', subtitle: 'Alert Rules' }
];
</script>

<style scoped>
.prometheus-board {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  background: radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.12), transparent 45%),
    linear-gradient(135deg, #020617, #030a1f 60%, #01030a);
  border-radius: 26px;
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: #dde7ff;
}

.prometheus-board :deep(.el-empty__description) {
  color: rgba(221, 231, 255, 0.9);
}

.hero-panel {
  padding: 1.5rem;
  border-radius: 18px;
  background: linear-gradient(135deg, #091526, #0d1f3f);
  border: 1px solid rgba(77, 167, 255, 0.18);
  box-shadow: 0 25px 45px rgba(3, 6, 18, 0.65);
  color: #d6e4ff;
}

.hero-text h1 {
  margin: 0;
}

.hero-subtitle {
  color: #9cb8ff;
  margin-top: 0.35rem;
}

.hero-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-top: 0.75rem;
  flex-wrap: wrap;
}

.hero-metrics {
  margin-top: 1.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
}

.glass-card {
  background: rgba(9, 14, 26, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 18px;
  backdrop-filter: blur(12px);
  box-shadow: 0 20px 40px rgba(5, 5, 5, 0.4);
}

.metric-card {
  padding: 1rem;
}

.metric-label {
  color: #a8beff;
}

.metric-value {
  font-size: 2rem;
  font-weight: 700;
  color: #60fdff;
}

.metric-subtitle {
  color: #8fa4dc;
  font-size: 0.9rem;
}

.scrape-panel,
.rule-panel,
.storage-panel,
.remote-panel,
.query-panel {
  padding: 1.25rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.muted {
  color: #92a7d7;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.dark-table :deep(.el-table) {
  background: transparent;
  color: #dce4ff;
}

.dark-table :deep(.el-table th),
.dark-table :deep(.el-table tr) {
  background: transparent;
  color: #b5c2e9;
}

.dark-table :deep(.el-table__row:hover > td) {
  background: rgba(255, 255, 255, 0.04);
}

.rule-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.rule-list li {
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 14px;
  padding: 0.85rem;
  background: rgba(255, 255, 255, 0.01);
}

.rule-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #e6ecff;
  font-weight: 600;
}

.rule-desc {
  color: #8ea3d7;
  margin: 0.35rem 0;
  font-size: 0.92rem;
}

.rule-meta {
  display: flex;
  justify-content: space-between;
  color: #6074a7;
  font-size: 0.85rem;
}

.storage-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.storage-progress span {
  display: inline-block;
  margin-bottom: 0.35rem;
  color: #c7d5ff;
}

.storage-meta {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.5rem;
}

.storage-meta li {
  padding: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.01);
}

.storage-meta label {
  display: block;
  font-size: 0.8rem;
  color: #8ea3d7;
  margin-bottom: 0.2rem;
}

.storage-meta span {
  color: #e4ebff;
  font-weight: 600;
}

.query-panel {
  padding-bottom: 1.5rem;
}

.query-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.query-card {
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 14px;
  padding: 0.85rem;
  background: rgba(8, 14, 27, 0.6);
}

.query-label {
  color: #8ea3d7;
  font-size: 0.85rem;
}

.query-value {
  font-size: 1.85rem;
  font-weight: 600;
  color: #5df2ff;
  margin: 0.35rem 0;
}

.query-card small {
  color: #7f91c5;
}
</style>
