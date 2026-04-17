import { ElMessage } from 'element-plus';
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue';

import { fetchDetectionTask, requestOneOffDetection } from '@/features/detection/api/detectionApi';
import { useDetectionBatchPolling } from '@/features/detection/composables/useDetectionBatchPolling';
import { useProbeNodes } from '@/features/detection/composables/useProbeNodes';
import {
  type DetectionResultViewModel,
  type DetectionLogItem,
  PROTOCOL_OPTIONS,
  extractCertificateInfo,
  formatConfigEntries,
  formatDate,
  formatResponseTime,
  getCertificateDaysText,
  getCertificateStatusTag,
  getStatusTagType,
  getStatusText,
  processBatchResults,
  validateTarget,
} from '@/features/detection/mappers/detectionUtils';

const DEFAULT_WARNING_THRESHOLD_DAYS = 14;

type CertificateConfig = {
  timeout_seconds: number;
};

type PendingTaskState = {
  id: string;
  nodeId?: string;
  nodeName: string;
  status: string;
};

export function useCertificateDetectionPage() {
  const form = reactive({
    target: '',
  });

  const detectionConfig = reactive<CertificateConfig>({
    timeout_seconds: 15,
  });

  const submitting = ref(false);
  const headerRefreshing = ref(false);
  const submissionError = ref<string | null>(null);
  const logs = ref<DetectionLogItem[]>([]);
  const detailVisible = ref(false);
  const activeLog = ref<DetectionLogItem | null>(null);
  const pendingTaskMap = ref<Map<string, PendingTaskState>>(new Map());

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

  const pendingTaskList = computed(() =>
    Array.from(pendingTaskMap.value.values()).sort((left, right) =>
      left.nodeName.localeCompare(right.nodeName, 'zh-CN')
    )
  );

  const {
    activeCount,
    pollingError,
    stoppedDueToError,
    resetRun,
    trackTask,
    startPolling,
    stopPolling,
    clearActive,
  } = useDetectionBatchPolling<DetectionResultViewModel>({
    fetchTask: fetchDetectionTask,
    onUpdate: (task, nodeId) => upsertPendingTask(task, nodeId),
    onTerminal: (task, nodeId) => appendLog(task, nodeId),
  });

  const visiblePendingTaskList = computed(() =>
    pendingTaskList.value.map((item) => ({
      ...item,
      status: stoppedDueToError.value ? 'unknown' : item.status,
    }))
  );

  const pendingSummaryText = computed(() => {
    const total = visiblePendingTaskList.value.length;
    if (!total) return '';

    const counts = visiblePendingTaskList.value.reduce<Record<string, number>>((acc, item) => {
      acc[item.status] = (acc[item.status] ?? 0) + 1;
      return acc;
    }, {});

    const parts = [
      counts.scheduled ? `${counts.scheduled} 个已提交` : '',
      counts.running ? `${counts.running} 个检测中` : '',
      counts.unknown ? `${counts.unknown} 个状态未知` : '',
    ].filter(Boolean);

    return `共 ${total} 个节点${parts.length ? `，${parts.join('，')}` : ''}`;
  });

  const batchProgressTitle = computed(() =>
    stoppedDueToError.value ? '本批次状态同步已暂停' : '本批次执行中'
  );

  function clearPendingTasks() {
    pendingTaskMap.value = new Map();
  }

  function resolveNodeName(nodeId?: string) {
    if (!nodeId) return '节点待确认';
    return nodeMap.value.get(nodeId)?.name ?? nodeId;
  }

  function upsertPendingTask(task: Pick<DetectionResultViewModel, 'id' | 'status'>, nodeId?: string) {
    const next = new Map(pendingTaskMap.value);
    const current = next.get(task.id);
    const resolvedNodeId = nodeId ?? current?.nodeId;
    next.set(task.id, {
      id: task.id,
      nodeId: resolvedNodeId,
      nodeName: resolveNodeName(resolvedNodeId),
      status: task.status || current?.status || 'scheduled',
    });
    pendingTaskMap.value = next;
  }

  function removePendingTask(taskId: string) {
    if (!pendingTaskMap.value.has(taskId)) return;
    const next = new Map(pendingTaskMap.value);
    next.delete(taskId);
    pendingTaskMap.value = next;
  }

  async function handleHeaderRefresh() {
    if (headerRefreshing.value) return;
    headerRefreshing.value = true;
    try {
      submissionError.value = null;
      await nextTick();
      await loadNodes();
      if (activeCount.value) {
        startPolling();
      }
      ElMessage.success('页面状态已刷新');
    } finally {
      headerRefreshing.value = false;
    }
  }

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
    clearActive();
    logs.value = [];
    activeLog.value = null;
    detailVisible.value = false;
    clearPendingTasks();
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
                warning_threshold_days: DEFAULT_WARNING_THRESHOLD_DAYS,
              },
            },
          })
        )
      );

      const { successCount, failedCount } = processBatchResults(submissions);

      if (!successCount) {
        throw new Error('证书检测提交失败，请稍后重试。');
      }

      logs.value = [];
      clearPendingTasks();
      const runToken = resetRun();

      submissions.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          const detection = result.value;
          const nodeId = nodeIds[index];
          trackTask(detection.id, nodeId, runToken);
          upsertPendingTask(
            {
              id: detection.id,
              status: detection.status ?? 'scheduled',
            },
            nodeId
          );
        }
      });

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
    removePendingTask(task.id);
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
        executed_at: task.executed_at ?? task.created_at ?? new Date().toISOString(),
        status_code: task.status_code ?? null,
        error_message: task.error_message ?? null,
        metadata: task.metadata ?? null,
        result_payload: task.result_payload ?? null,
      },
    ];
  }

  onBeforeUnmount(() => {
    stopPolling();
  });

  onMounted(() => {
    void loadNodes();
  });

  return {
    form,
    detectionConfig,
    submitting,
    headerRefreshing,
    submissionError,
    logs,
    detailVisible,
    activeLog,
    targetPlaceholder,
    selectedNodeIds,
    nodes,
    nodesLoading,
    loadNodes,
    certificateDetail,
    detailConfigEntries,
    pendingTaskList,
    visiblePendingTaskList,
    pollingError,
    stoppedDueToError,
    pendingSummaryText,
    batchProgressTitle,
    clearLogs,
    openLogDetail,
    handleSubmit,
    handleHeaderRefresh,
    getCertificateDaysClass,
    getCertificateDaysText,
    getCertificateStatusTag,
    getStatusTagType,
    getStatusText,
    formatDate,
    formatResponseTime,
    extractCertificateInfo,
  };
}
