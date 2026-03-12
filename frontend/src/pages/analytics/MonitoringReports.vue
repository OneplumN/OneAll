<template>
  <RepositoryPageShell root-title="统计分析" section-title="拨测报表">
    <template #actions>
      <el-select v-model="days" class="toolbar-select" :disabled="loading" style="width: 140px" @change="loadReport">
        <el-option :value="7" label="近 7 天" />
        <el-option :value="30" label="近 30 天" />
        <el-option :value="90" label="近 90 天" />
      </el-select>
      <el-button class="toolbar-button" type="primary" :loading="loading" @click="loadReport">刷新</el-button>
    </template>

    <div class="content">
      <el-alert
        type="info"
        show-icon
        :closable="false"
        title="综合拨测报表：以拨测任务结果为准，提供成功率、延迟分位数、失败类型与 Top 榜，并支持查看失败明细。"
      />

      <el-row :gutter="12">
        <el-col :span="6">
          <div class="kpi">
            <div class="kpi-label">任务数</div>
            <div class="kpi-value">{{ report.summary.total }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="kpi">
            <div class="kpi-label">成功率</div>
            <div class="kpi-value">{{ formatPercent(report.summary.success_rate) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="kpi">
            <div class="kpi-label">失败（含超时）</div>
            <div class="kpi-value danger">{{ report.summary.failed + report.summary.timeout }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="kpi">
            <div class="kpi-label">P95 延迟</div>
            <div class="kpi-value">{{ formatMs(report.summary.p95_ms) }}</div>
          </div>
        </el-col>
      </el-row>

      <el-card shadow="never">
        <template #header><span>趋势（成功率 / P95 延迟）</span></template>
        <BaseChart :option="trendOption" :height="300" />
        <el-empty v-if="!report.trend.length" description="暂无趋势数据" />
      </el-card>

      <el-row :gutter="12">
        <el-col :span="10">
          <el-card shadow="never">
            <template #header><span>失败类型分布</span></template>
            <BaseChart :option="failureTypeOption" :height="280" />
            <el-empty v-if="!report.failure_types.length" description="暂无失败类型数据" />
          </el-card>
        </el-col>
        <el-col :span="14">
          <el-card shadow="never">
            <template #header><span>Top 榜</span></template>
            <el-tabs v-model="topTab">
              <el-tab-pane label="失败目标 Top" name="targets">
                <el-table :data="report.top_targets" height="260" style="width: 100%">
                  <el-table-column prop="target" label="目标" min-width="260" show-overflow-tooltip />
                  <el-table-column prop="total" label="总数" width="90" />
                  <el-table-column label="失败/超时" width="120">
                    <template #default="{ row }">{{ (row.failed || 0) + (row.timeout || 0) }}</template>
                  </el-table-column>
                  <el-table-column label="失败率" width="110">
                    <template #default="{ row }">{{ formatPercent(row.fail_rate) }}</template>
                  </el-table-column>
                  <el-table-column prop="p95_ms" label="P95(ms)" width="110">
                    <template #default="{ row }">{{ formatMs(row.p95_ms) }}</template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="!report.top_targets.length" description="暂无 Top 目标数据" />
              </el-tab-pane>
              <el-tab-pane label="失败探针 Top" name="probes">
                <el-table :data="report.top_probes" height="260" style="width: 100%">
                  <el-table-column prop="probe_name" label="探针" min-width="220" show-overflow-tooltip />
                  <el-table-column prop="total" label="总数" width="90" />
                  <el-table-column label="失败/超时" width="120">
                    <template #default="{ row }">{{ (row.failed || 0) + (row.timeout || 0) }}</template>
                  </el-table-column>
                  <el-table-column label="成功率" width="110">
                    <template #default="{ row }">{{ formatPercent(row.success_rate) }}</template>
                  </el-table-column>
                  <el-table-column prop="p95_ms" label="P95(ms)" width="110">
                    <template #default="{ row }">{{ formatMs(row.p95_ms) }}</template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="!report.top_probes.length" description="暂无 Top 探针数据" />
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never">
        <template #header><span>最近失败明细</span></template>
        <el-table :data="report.recent_failures" height="420" style="width: 100%">
          <el-table-column prop="created_at" label="时间" width="180" show-overflow-tooltip />
          <el-table-column prop="target" label="目标" min-width="240" show-overflow-tooltip />
          <el-table-column prop="protocol" label="协议" width="120" />
          <el-table-column label="探针" width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ row.probe?.name || '-' }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="110" />
          <el-table-column prop="status_code" label="状态码" width="110" />
          <el-table-column prop="error_message" label="错误" min-width="280" show-overflow-tooltip />
        </el-table>
        <el-empty v-if="!report.recent_failures.length" description="暂无失败明细" />
      </el-card>
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import type { EChartsOption } from 'echarts';

import BaseChart from '@/components/BaseChart.vue';
import RepositoryPageShell from '@/components/RepositoryPageShell.vue';
import { fetchDetectionReport } from '@/services/reportApi';

interface DetectionReportData {
  generated_at: string;
  range: { start: string; end: string; days: number };
  summary: {
    total: number;
    succeeded: number;
    failed: number;
    timeout: number;
    success_rate: number;
    p50_ms?: number | null;
    p95_ms?: number | null;
  };
  trend: Array<{ day: string; total: number; success_rate: number; p95_ms?: number | null }>;
  failure_types: Array<{ type: string; count: number }>;
  top_targets: Array<{
    target: string;
    total: number;
    succeeded: number;
    failed: number;
    timeout: number;
    fail_rate: number;
    p95_ms?: number | null;
  }>;
  top_probes: Array<{
    probe_id: string;
    probe_name: string;
    total: number;
    succeeded: number;
    failed: number;
    timeout: number;
    success_rate: number;
    p95_ms?: number | null;
  }>;
  recent_failures: Array<{
    id: string;
    target: string;
    protocol: string;
    status: string;
    response_time_ms?: number | null;
    status_code?: string;
    error_message?: string;
    created_at: string;
    probe?: { id?: string | null; name?: string | null };
  }>;
}

const days = ref(30);
const topTab = ref<'targets' | 'probes'>('targets');
const loading = ref(false);

const report = reactive<DetectionReportData>({
  generated_at: '',
  range: { start: '', end: '', days: 30 },
  summary: {
    total: 0,
    succeeded: 0,
    failed: 0,
    timeout: 0,
    success_rate: 0,
    p50_ms: null,
    p95_ms: null
  },
  trend: [],
  failure_types: [],
  top_targets: [],
  top_probes: [],
  recent_failures: []
});

async function loadReport() {
  loading.value = true;
  try {
    const data = await fetchDetectionReport(days.value);
    Object.assign(report, data || {});
  } catch (err) {
    ElMessage.error('报表加载失败');
  } finally {
    loading.value = false;
  }
}

function formatPercent(value: number) {
  if (typeof value !== 'number') return '-';
  return `${(value * 100).toFixed(2)}%`;
}

function formatMs(value?: number | null) {
  if (typeof value !== 'number') return '-';
  return `${value}`;
}

const trendOption = computed<EChartsOption | null>(() => {
  if (!report.trend.length) return null;
  const x = report.trend.map((p) => p.day);
  const rate = report.trend.map((p) => Number((p.success_rate * 100).toFixed(2)));
  const p95 = report.trend.map((p) => (typeof p.p95_ms === 'number' ? p.p95_ms : null));
  return {
    tooltip: { trigger: 'axis', appendToBody: true, extraCssText: 'z-index: 3000;' },
    legend: { top: 0, left: 'center' },
    grid: { left: 40, right: 40, top: 40, bottom: 30, containLabel: true },
    xAxis: { type: 'category', data: x },
    yAxis: [
      { type: 'value', name: '成功率(%)', min: 0, max: 100 },
      { type: 'value', name: 'P95(ms)', min: 0 }
    ],
    series: [
      { name: '成功率', type: 'line', smooth: true, data: rate, yAxisIndex: 0 },
      { name: 'P95 延迟', type: 'line', smooth: true, data: p95, yAxisIndex: 1 }
    ],
    color: ['#409EFF', '#E6A23C']
  };
});

const failureTypeOption = computed<EChartsOption | null>(() => {
  if (!report.failure_types.length) return null;
  const total = report.failure_types.reduce((sum, item) => sum + (item.count || 0), 0);
  return {
    tooltip: { trigger: 'item', appendToBody: true, extraCssText: 'z-index: 3000;' },
    legend: { bottom: 0, left: 'center', type: 'scroll' },
    graphic: {
      type: 'text',
      left: 'center',
      top: '42%',
      style: {
        text: `失败类型\\n总计 ${total}`,
        align: 'center',
        fill: '#303133',
        fontSize: 13,
        fontWeight: 600,
        lineHeight: 18
      }
    },
    series: [
      {
        type: 'pie',
        center: ['50%', '42%'],
        radius: ['55%', '78%'],
        label: { show: false },
        labelLine: { show: false },
        data: report.failure_types.map((item) => ({ name: item.type, value: item.count }))
      }
    ]
  };
});

loadReport();
</script>

<style scoped>
.content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kpi {
  border: 1px solid var(--oa-border-light);
  border-radius: 8px;
  padding: 12px;
  background: var(--oa-bg-panel);
}

.kpi-label {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.kpi-value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 600;
  color: var(--oa-text-primary);
}

.kpi-value.danger {
  color: var(--el-color-danger);
}
</style>
