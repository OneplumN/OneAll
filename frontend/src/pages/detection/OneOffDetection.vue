<template>
  <div class="oneoff-page">
    <DetectionPageBase
      title="域名拨测"
      :error="submissionError"
      refreshable
      :refreshing="headerRefreshing"
      refresh-text="刷新"
      @refresh="handleHeaderRefresh"
    >
      <template #header-left>
        <div class="protocol-combo">
          <el-select
            v-model="form.protocol"
            class="protocol-combo__select"
            size="large"
            :disabled="submitting"
          >
            <el-option
              v-for="option in protocolOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-input
            v-model="form.target"
            class="protocol-combo__input"
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
            hint="可多选节点，将依次在各节点执行拨测。"
            @refresh="loadNodes"
          />

          <DetectionConfig title="高级配置" embedded>
            <template #config-items>
              <TimeoutSlider v-model="detectionConfig.timeout_seconds" :min="1" :max="60" />

              <div v-if="isHttpConfig" class="config-item config-item--row">
                <span class="config-item__label">允许重定向</span>
                <el-switch v-model="httpConfig.follow_redirects" />
              </div>
              <div v-else class="config-item config-item--row">
                <span class="config-item__label">端口</span>
                <el-input-number v-model="tcpConfig.port" :min="1" :max="65535" />
              </div>
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
            支持 HTTP(S) / WebSocket / Telnet；可多选节点并行执行，本页仅保留本次批次结果
          </template>

          <template #columns>
            <el-table-column prop="executed_at" label="时间" min-width="160">
              <template #default="{ row }">{{ formatDate(row.executed_at) }}</template>
            </el-table-column>
            <el-table-column prop="target" label="域名" min-width="220" show-overflow-tooltip />
            <el-table-column prop="protocol" label="类型" width="140">
              <template #default="{ row }">{{ getProtocolLabel(row.protocol) }}</template>
            </el-table-column>
            <el-table-column prop="nodes" label="节点" min-width="160">
              <template #default="{ row }">
                <el-tag v-if="row.nodes.length" round size="small">{{ row.nodes[0] }}</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="response_time_ms" label="耗时" width="120">
              <template #default="{ row }">
                {{ formatResponseTime(row.response_time_ms) }}
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
      title="拨测详情"
      size="560px"
      destroy-on-close
      append-to-body
      class="detail-drawer"
    >
      <div v-if="activeLog" class="detail-content">
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="域名">{{ activeLog.target }}</el-descriptions-item>
          <el-descriptions-item label="拨测类型">{{
            getProtocolLabel(activeLog.protocol)
          }}</el-descriptions-item>
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
          <h4>拨测配置</h4>
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
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';

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
  getProtocolLabel,
  formatDate,
  formatResponseTime,
  formatConfigEntries,
  validateTarget,
  cloneConfig,
  processBatchResults
} from './utils/detectionUtils';

type HttpDetectionConfig = {
  mode: 'http';
  timeout_seconds: number;
  follow_redirects: boolean;
};

type TcpDetectionConfig = {
  mode: 'tcp';
  timeout_seconds: number;
  port: number;
};

type DetectionConfigModel = HttpDetectionConfig | TcpDetectionConfig;

const form = reactive({
  target: '',
  protocol: 'HTTPS'
});

const protocolOptions = [
  { label: 'HTTP(S)', value: 'HTTPS' },
  { label: 'WebSocket', value: 'WSS' },
  { label: 'Telnet', value: 'Telnet' }
];

const configTemplates: Record<string, DetectionConfigModel> = {
  HTTPS: { mode: 'http', timeout_seconds: 10, follow_redirects: true },
  WSS: { mode: 'http', timeout_seconds: 10, follow_redirects: false },
  Telnet: { mode: 'tcp', timeout_seconds: 10, port: 80 }
};

const detectionConfig = reactive<DetectionConfigModel>(cloneConfig(configTemplates[form.protocol]));

const submitting = ref(false);
const headerRefreshing = ref(false);
const submissionError = ref<string | null>(null);
const logs = ref<DetectionLogItem[]>([]);
const detailVisible = ref(false);
const activeLog = ref<DetectionLogItem | null>(null);

const targetPlaceholder = computed(() => {
  const option = PROTOCOL_OPTIONS[form.protocol as keyof typeof PROTOCOL_OPTIONS];
  return option?.placeholder ?? '请输入目标地址';
});

const selectedNodeIds = ref<string[]>([]);
const { nodes, loading: nodesLoading, nodeMap, loadNodes } = useProbeNodes(selectedNodeIds);

const httpConfig = computed(() => detectionConfig as HttpDetectionConfig);
const tcpConfig = computed(() => detectionConfig as TcpDetectionConfig);
const isHttpConfig = computed(() => detectionConfig.mode === 'http');

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

watch(
  () => form.protocol,
  (next) => {
    Object.assign(detectionConfig, cloneConfig(configTemplates[next]));
  }
);

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
    const validationError = validateTarget(target, form.protocol);
    if (validationError) {
      throw new Error(validationError);
    }

    if (!selectedNodeIds.value.length) {
      throw new Error('请至少选择一个探针节点');
    }

    logs.value = [];
    const runToken = resetRun();
    const configSnapshot = cloneConfig(detectionConfig);
    const nodeIds = [...selectedNodeIds.value];

    const submissions = await Promise.allSettled(
      nodeIds.map((nodeId) =>
        requestOneOffDetection({
          target,
          protocol: form.protocol,
          timeout_seconds: detectionConfig.timeout_seconds,
          probe_id: nodeId,
          metadata: {
            selected_node: nodeId,
            config: configSnapshot
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
        console.error('提交拨测失败', result.reason);
      }
    });

    if (!successCount) {
      throw new Error('拨测提交失败，请稍后再试。');
    }

    startPolling();
    if (failedCount) {
      ElMessage.warning(`部分节点提交失败，共 ${failedCount} 个。`);
    } else {
      ElMessage.success('拨测请求已提交');
    }
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : '拨测提交失败，请稍后再试。';
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
      metadata: task.metadata ?? null
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

.protocol-combo {
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

.protocol-combo:hover {
  box-shadow: 0 0 0 1px var(--oa-text-muted) inset;
}

.protocol-combo:focus-within {
  box-shadow: 0 0 0 2px var(--oa-color-primary-light) inset;
}

.protocol-combo__select {
  width: 140px;
  flex: 0 0 auto;
}

.protocol-combo :deep(.protocol-combo__select .el-select__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: var(--oa-radius-md) 0 0 var(--oa-radius-md);
  border-right: 1px solid var(--oa-border-color);
  min-height: 44px;
}

.protocol-combo__input {
  flex: 1;
  min-width: 0;
}

.protocol-combo :deep(.protocol-combo__input .el-input__wrapper),
.protocol-combo :deep(.protocol-combo__input .el-input__wrapper:hover),
.protocol-combo :deep(.protocol-combo__input .el-input__wrapper.is-focus) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 var(--oa-radius-md) var(--oa-radius-md) 0;
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

@media (max-width: 768px) {
  .protocol-combo {
    min-width: auto;
    width: 100%;
  }
}
</style>
