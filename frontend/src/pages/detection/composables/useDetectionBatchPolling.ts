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
  isTerminalStatus?: (status: string) => boolean;
  onTerminal: (task: TTask, nodeId?: string) => void;
}) {
  const intervalMs = options.intervalMs ?? 2000;
  const isTerminalStatus =
    options.isTerminalStatus ??
    ((status: string) => ['succeeded', 'failed', 'timeout'].includes(status));

  const active = ref<Map<string, ActiveMeta>>(new Map());
  const currentRunToken = ref(0);
  const activeCount = computed(() => active.value.size);
  const running = computed(() => active.value.size > 0);

  let pollTimer: ReturnType<typeof window.setInterval> | null = null;

  function stopPolling() {
    if (!pollTimer) return;
    window.clearInterval(pollTimer);
    pollTimer = null;
  }

  function clearActive() {
    stopPolling();
    active.value.clear();
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
    const ids = Array.from(active.value.keys());
    if (!ids.length) {
      stopPolling();
      return;
    }

    await Promise.all(
      ids.map(async (id) => {
        try {
          const task = await options.fetchTask(id);
          if (!isTerminalStatus(task.status)) return;

          const meta = active.value.get(id);
          if (meta && meta.runToken === currentRunToken.value) {
            options.onTerminal(task, resolveNodeId(task, meta));
          }
          active.value.delete(id);
        } catch (error) {
          console.error('Polling detection task failed', error);
        }
      })
    );

    if (!active.value.size) {
      stopPolling();
    }
  }

  function startPolling() {
    if (!active.value.size) return;
    stopPolling();
    pollOnce().catch((error) => {
      console.error('Polling detection task failed', error);
    });
    pollTimer = window.setInterval(() => {
      pollOnce().catch((error) => {
        console.error('Polling detection task failed', error);
      });
    }, intervalMs);
  }

  return {
    activeCount,
    running,
    resetRun,
    trackTask,
    startPolling,
    stopPolling,
    clearActive
  };
}

