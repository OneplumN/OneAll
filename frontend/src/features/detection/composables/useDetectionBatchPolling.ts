import { computed, ref } from 'vue';

type MinimalTask = {
  id: string;
  status: string;
  metadata?: Record<string, unknown> | null;
};

type ActiveMeta = {
  nodeId: string;
  runToken: number;
};

export function useDetectionBatchPolling<TTask extends MinimalTask>(options: {
  fetchTask: (id: string) => Promise<TTask>;
  intervalMs?: number;
  maxFailures?: number;
  isTerminalStatus?: (status: string) => boolean;
  onUpdate?: (task: TTask, nodeId?: string) => void;
  onTerminal: (task: TTask, nodeId?: string) => void;
}) {
  const intervalMs = options.intervalMs ?? 2000;
  const maxFailures = options.maxFailures ?? 3;
  const isTerminalStatus =
    options.isTerminalStatus ??
    ((status: string) => ['succeeded', 'failed', 'timeout'].includes(status));

  const active = ref<Map<string, ActiveMeta>>(new Map());
  const currentRunToken = ref(0);
  const activeCount = computed(() => active.value.size);
  const running = computed(() => active.value.size > 0);
  const failureCount = ref(0);
  const pollingError = ref<string | null>(null);
  const stoppedDueToError = ref(false);

  let pollTimer: ReturnType<typeof window.setInterval> | null = null;
  let pollInFlight = false;

  function resetPollingState() {
    failureCount.value = 0;
    pollingError.value = null;
    stoppedDueToError.value = false;
  }

  function stopPolling() {
    if (!pollTimer) return;
    window.clearInterval(pollTimer);
    pollTimer = null;
  }

  function clearActive() {
    stopPolling();
    active.value.clear();
    resetPollingState();
  }

  function resetRun(): number {
    clearActive();
    currentRunToken.value += 1;
    return currentRunToken.value;
  }

  function trackTask(taskId: string, nodeId: string, runToken: number) {
    active.value.set(taskId, { nodeId, runToken });
  }

  function resolveNodeId(task: TTask, meta?: ActiveMeta): string | undefined {
    const fromMeta = meta?.nodeId;
    if (fromMeta) return fromMeta;
    const fromTaskMeta = task.metadata?.selected_node;
    return typeof fromTaskMeta === 'string' ? fromTaskMeta : undefined;
  }

  async function pollOnce() {
    if (pollInFlight) return;

    const ids = Array.from(active.value.keys());
    if (!ids.length) {
      stopPolling();
      return;
    }

    pollInFlight = true;
    let hasSuccessfulFetch = false;
    let hadFailures = false;

    try {
      await Promise.all(
        ids.map(async (id) => {
          try {
            const task = await options.fetchTask(id);
            hasSuccessfulFetch = true;
            const meta = active.value.get(id);
            if (meta && meta.runToken === currentRunToken.value) {
              options.onUpdate?.(task, resolveNodeId(task, meta));
            }
            if (!isTerminalStatus(task.status)) return;

            if (meta && meta.runToken === currentRunToken.value) {
              options.onTerminal(task, resolveNodeId(task, meta));
            }
            active.value.delete(id);
          } catch {
            hadFailures = true;
          }
        })
      );
    } finally {
      pollInFlight = false;
    }

    if (hasSuccessfulFetch) {
      resetPollingState();
    } else if (hadFailures) {
      failureCount.value += 1;
      stoppedDueToError.value = failureCount.value >= maxFailures;
      pollingError.value = stoppedDueToError.value
        ? '任务状态同步已中断，结果可能延迟显示，请手动刷新后重试。'
        : `任务状态同步暂时失败，正在自动重试（${failureCount.value}/${maxFailures}）。`;

      if (stoppedDueToError.value) {
        stopPolling();
      }
    }

    if (!active.value.size) {
      stopPolling();
    }
  }

  function startPolling() {
    if (!active.value.size) return;
    resetPollingState();
    stopPolling();
    pollOnce().catch(() => undefined);
    pollTimer = window.setInterval(() => {
      pollOnce().catch(() => undefined);
    }, intervalMs);
  }

  return {
    activeCount,
    running,
    failureCount,
    pollingError,
    stoppedDueToError,
    resetRun,
    trackTask,
    pollOnce,
    startPolling,
    stopPolling,
    clearActive,
    resetPollingState
  };
}
