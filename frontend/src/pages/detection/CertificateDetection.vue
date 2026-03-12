<template>
  <div class="oneoff-page">
    <DetectionPageBase
      title="证书检测"
      :error="submissionError"
      config-title="检测配置"
      refreshable
      :refreshing="headerRefreshing"
      refresh-text="刷新"
      @refresh="handleHeaderRefresh"
    >
    <template #header-left>
      <div class="single-combo">
        <el-input
          v-model="form.target"
          class="single-combo__input"
          size="large"
          :placeholder="targetPlaceholder"
          :disabled="submitting"
          clearable
          @keyup.enter="handleSubmit"
        />
      </div>
    </template>

    <template #config>
      <div class="detection-grid">
        <ProbeNodeSelector
          v-model="selectedNodeIds"
          :nodes="nodes"
          :loading="nodesLoading"
          embedded
          hint="支持多节点并发检测，本页仅保留本次批次结果。"
          @refresh="loadNodes"
        />

        <DetectionConfig title="高级配置" embedded>
          <template #config-items>
            <TimeoutSlider v-model="detectionConfig.timeout_seconds" :min="5" :max="60" />
          </template>
        </DetectionConfig>
      </div>
    </template>

    <template #config-footer>
      <div class="submit-row">
        <el-button
          type="primary"
          size="large"
          class="submit-row__action"
          :loading="submitting"
          :disabled="submitting"
          @click="handleSubmit"
        >
          立即检测
        </el-button>
      </div>
    </template>

    <template #content>
      <DetectionResults
        title="检测结果"
        :data="logs"
        :loading="submitting && !logs.length"
        @clear="clearLogs"
      >
        <template v-if="!logs.length && !submitting" #title-extra>
          仅支持 https:// 域名；建议多选不同网络类型节点，对比证书有效期与可达性差异
        </template>

        <template #columns>
          <el-table-column prop="executed_at" label="时间" min-width="160">
            <template #default="{ row }">{{ formatDate(row.executed_at) }}</template>
          </el-table-column>
          <el-table-column prop="target" label="域名" min-width="220" show-overflow-tooltip />
          <el-table-column prop="nodes" label="节点" min-width="160">
            <template #default="{ row }">
              <el-tag v-if="row.nodes.length" round size="small">{{ row.nodes[0] }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="剩余天数" width="140" align="center">
            <template #default="{ row }">
              <span :class="getCertificateDaysClass(row)">{{
                getCertificateDaysText(extractCertificateInfo(row))
              }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120" align="center">
            <template #default="{ row }">
              <el-tag
                :type="getStatusTagType(row.status)"
                effect="plain"
                size="small"
                class="status-tag"
              >
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button type="primary" text size="small" @click="openLogDetail(row)">
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </template>
      </DetectionResults>
    </template>
    </DetectionPageBase>

  <!-- 详情抽屉 -->
  <el-drawer
    v-model="detailVisible"
    title="证书检测详情"
    size="560px"
    destroy-on-close
    append-to-body
    class="detail-drawer"
  >
    <div v-if="activeLog" class="detail-content">
      <el-descriptions :column="1" size="small" border>
        <el-descriptions-item label="域名">{{ activeLog.target }}</el-descriptions-item>
        <el-descriptions-item label="节点">{{ activeLog.nodes[0] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{
          getStatusText(activeLog.status)
        }}</el-descriptions-item>
        <el-descriptions-item label="状态码">{{
          activeLog.status_code ?? '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{
          formatResponseTime(activeLog.response_time_ms)
        }}</el-descriptions-item>
        <el-descriptions-item label="执行时间">{{
          formatDate(activeLog.executed_at)
        }}</el-descriptions-item>
        <el-descriptions-item label="错误信息">{{
          activeLog.error_message || '-'
        }}</el-descriptions-item>
      </el-descriptions>

      <div class="detail-section">
        <h4>证书信息</h4>
        <el-empty v-if="!certificateDetail" description="无证书信息" :image-size="60" />
        <el-descriptions v-else :column="1" size="small" border>
          <el-descriptions-item label="状态">
            <el-tag :type="getCertificateStatusTag(certificateDetail.status)" size="small">
              {{ getStatusText(certificateDetail.status || 'unknown') }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="剩余有效期">
            <span :class="getCertificateDaysClass(activeLog)">
              {{ getCertificateDaysText(certificateDetail) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="颁发者">{{
            certificateDetail.issuer ?? '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="主题">{{
            certificateDetail.subject ?? '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="有效期">
            {{ formatDate(certificateDetail.valid_from || undefined) }} ~
            {{ formatDate(certificateDetail.valid_to || undefined) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="detail-section">
        <h4>检测配置</h4>
        <el-empty v-if="!detailConfigEntries.length" description="无配置数据" :image-size="60" />
        <el-descriptions v-else :column="1" size="small">
          <el-descriptions-item
            v-for="item in detailConfigEntries"
            :key="item.key"
            :label="item.label"
          >
            {{ item.value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </div>
  </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue';

import { fetchDetectionTask, requestOneOffDetection } from '@/services/detectionApi';
import ProbeNodeSelector from './components/ProbeNodeSelector.vue';
import DetectionPageBase from './components/DetectionPageBase.vue';
import DetectionConfig from './components/DetectionConfig.vue';
import DetectionResults from './components/DetectionResults.vue';
import TimeoutSlider from './components/TimeoutSlider.vue';
import { useDetectionBatchPolling } from './composables/useDetectionBatchPolling';
import { useProbeNodes } from './composables/useProbeNodes';
import {
  type DetectionResultViewModel,
  type DetectionLogItem,
  PROTOCOL_OPTIONS,
  getStatusTagType,
  getStatusText,
  formatDate,
  formatResponseTime,
  formatConfigEntries,
  validateTarget,
  extractCertificateInfo,
  getCertificateDaysText,
  getCertificateStatusTag,
  processBatchResults
} from './utils/detectionUtils';

const DEFAULT_WARNING_THRESHOLD_DAYS = 14;

type CertificateConfig = {
  timeout_seconds: number;
};

const form = reactive({
  target: ''
});

const detectionConfig = reactive<CertificateConfig>({
  timeout_seconds: 15
});

const submitting = ref(false);
const headerRefreshing = ref(false);
const submissionError = ref<string | null>(null);
const logs = ref<DetectionLogItem[]>([]);
const detailVisible = ref(false);
const activeLog = ref<DetectionLogItem | null>(null);

const targetPlaceholder = computed(() => {
  const option = PROTOCOL_OPTIONS.CERTIFICATE;
  return option?.placeholder ?? '请输入 https://your-domain.com';
});

const selectedNodeIds = ref<string[]>([]);
const { nodes, loading: nodesLoading, nodeMap, loadNodes } = useProbeNodes(selectedNodeIds);

const certificateDetail = computed(() => extractCertificateInfo(activeLog.value));

const detailConfigEntries = computed(() => {
  const config = (activeLog.value?.metadata?.config ?? null) as Record<string, unknown> | null;
  return formatConfigEntries(config);
});

const { resetRun, trackTask, startPolling, stopPolling } =
  useDetectionBatchPolling<DetectionResultViewModel>({
    fetchTask: fetchDetectionTask,
    onTerminal: (task, nodeId) => appendLog(task, nodeId)
  });

async function handleHeaderRefresh() {
  if (headerRefreshing.value) return;
  headerRefreshing.value = true;
  try {
    await nextTick();
    window.location.reload();
  } finally {
    headerRefreshing.value = false;
  }
}

// 获取证书天数的样式类
function getCertificateDaysClass(row: DetectionLogItem) {
  const info = extractCertificateInfo(row);
  if (!info || typeof info.days_until_expiry !== 'number') return '';

  const days = info.days_until_expiry;
  if (days < 0) return 'text-danger';
  if (days <= 7) return 'text-danger';
  if (days <= 30) return 'text-warning';
  return 'text-success';
}

function clearLogs() {
  logs.value = [];
  activeLog.value = null;
  detailVisible.value = false;
}

function openLogDetail(log: DetectionLogItem) {
  activeLog.value = log;
  detailVisible.value = true;
}

async function handleSubmit() {
  submissionError.value = null;
  submitting.value = true;

  try {
    const target = form.target.trim();
    const validationError = validateTarget(target, 'CERTIFICATE');
    if (validationError) {
      throw new Error(validationError);
    }

    if (!selectedNodeIds.value.length) {
      throw new Error('请选择检测节点');
    }

    logs.value = [];
    const runToken = resetRun();
    const nodeIds = [...selectedNodeIds.value];

    const submissions = await Promise.allSettled(
      nodeIds.map((nodeId) =>
        requestOneOffDetection({
          target,
          protocol: 'CERTIFICATE',
          timeout_seconds: detectionConfig.timeout_seconds,
          probe_id: nodeId,
          metadata: {
            selected_node: nodeId,
            config: {
              timeout_seconds: detectionConfig.timeout_seconds,
              warning_threshold_days: DEFAULT_WARNING_THRESHOLD_DAYS
            }
          }
        })
      )
    );

    const { successCount, failedCount } = processBatchResults(submissions);

    submissions.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        const detection = result.value;
        const nodeId = nodeIds[index];
        trackTask(detection.id, nodeId, runToken);
      } else {
        console.error('提交证书检测失败', result.reason);
      }
    });

    if (!successCount) {
      throw new Error('证书检测提交失败，请稍后重试。');
    }

    startPolling();
    if (failedCount) {
      ElMessage.warning(`部分节点提交失败，共 ${failedCount} 个。`);
    } else {
      ElMessage.success('证书检测请求已提交');
    }
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : '证书检测失败，请稍后再试。';
  } finally {
    submitting.value = false;
  }
}

function appendLog(task: DetectionResultViewModel, nodeId?: string) {
  const snapshot = nodeId ?? (task.metadata?.selected_node as string | undefined);
  const nodeName = snapshot ? (nodeMap.value.get(snapshot)?.name ?? snapshot) : null;
  logs.value = [
    ...logs.value,
    {
      id: task.id,
      target: task.target,
      protocol: task.protocol,
      nodes: nodeName ? [nodeName] : [],
      status: task.status,
      response_time_ms: task.response_time_ms ?? null,
      executed_at: new Date().toISOString(),
      status_code: task.status_code ?? null,
      error_message: task.error_message ?? null,
      metadata: task.metadata ?? null,
      result_payload: task.result_payload ?? null
    }
  ];
}

onBeforeUnmount(() => {
  stopPolling();
});

onMounted(() => {
  loadNodes();
});
</script>

<style scoped>
@import './styles/detection-common.scss';

.single-combo {
  display: flex;
  align-items: stretch;
  flex: 1;
  min-width: min(520px, 100%);
  border-radius: var(--oa-radius-md);
  background: var(--oa-bg-panel);
  box-shadow: 0 0 0 1px var(--oa-border-color) inset;
  transition: box-shadow 0.2s ease;
  overflow: hidden;
}

.single-combo:hover {
  box-shadow: 0 0 0 1px var(--oa-text-muted) inset;
}

.single-combo:focus-within {
  box-shadow: 0 0 0 2px var(--oa-color-primary-light) inset;
}

.single-combo__input {
  flex: 1;
  min-width: 0;
}

.single-combo :deep(.single-combo__input .el-input__wrapper),
.single-combo :deep(.single-combo__input .el-input__wrapper:hover),
.single-combo :deep(.single-combo__input .el-input__wrapper.is-focus) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: var(--oa-radius-md);
  min-height: 44px;
}

.submit-row {
  display: flex;
  justify-content: center;
  width: 100%;
}

.submit-row__action {
  min-height: 44px;
  min-width: 140px;
}

.text-success {
  color: var(--el-color-success);
  font-weight: 500;
}

.text-warning {
  color: var(--el-color-warning);
  font-weight: 500;
}

.text-danger {
  color: var(--el-color-danger);
  font-weight: 500;
}

@media (max-width: 768px) {
  .single-combo {
    min-width: auto;
    width: 100%;
  }
}
</style>
