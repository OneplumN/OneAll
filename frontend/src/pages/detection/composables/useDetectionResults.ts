/**
 * 检测结果管理通用逻辑
 */
import { computed, ref, shallowRef } from 'vue';
import type { BaseDetectionLog } from '../utils/detectionUtils';

export function useDetectionResults<T extends BaseDetectionLog>() {
  // 结果数据
  const logs = shallowRef<T[]>([]);
  const detailVisible = ref(false);
  const activeLog = ref<T | null>(null);

  // 计算属性
  const hasLogs = computed(() => logs.value.length > 0);
  const latestLog = computed(() => logs.value[0] || null);

  // 添加日志
  const addLog = (log: T) => {
    logs.value = [log, ...logs.value];
  };

  // 批量添加日志
  const addLogs = (newLogs: T[]) => {
    logs.value = [...newLogs, ...logs.value];
  };

  // 更新日志
  const updateLog = (id: string, updates: Partial<T>) => {
    const index = logs.value.findIndex(log => log.id === id);
    if (index !== -1) {
      logs.value[index] = { ...logs.value[index], ...updates };
    }
  };

  // 清空日志
  const clearLogs = () => {
    logs.value = [];
    activeLog.value = null;
    detailVisible.value = false;
  };

  // 打开详情
  const openDetail = (log: T) => {
    activeLog.value = log;
    detailVisible.value = true;
  };

  // 关闭详情
  const closeDetail = () => {
    detailVisible.value = false;
    // 延迟清空activeLog，避免关闭动画时数据消失
    setTimeout(() => {
      if (!detailVisible.value) {
        activeLog.value = null;
      }
    }, 300);
  };

  // 根据状态筛选日志
  const getLogsByStatus = (status: string) => {
    return logs.value.filter(log => log.status === status);
  };

  // 获取成功的日志
  const successLogs = computed(() => getLogsByStatus('succeeded'));
  const failedLogs = computed(() => getLogsByStatus('failed'));
  const timeoutLogs = computed(() => getLogsByStatus('timeout'));

  // 统计信息
  const stats = computed(() => ({
    total: logs.value.length,
    success: successLogs.value.length,
    failed: failedLogs.value.length,
    timeout: timeoutLogs.value.length,
    successRate: logs.value.length > 0 ? (successLogs.value.length / logs.value.length * 100).toFixed(1) : '0'
  }));

  return {
    logs,
    detailVisible,
    activeLog,
    hasLogs,
    latestLog,
    stats,
    addLog,
    addLogs,
    updateLog,
    clearLogs,
    openDetail,
    closeDetail,
    getLogsByStatus,
    successLogs,
    failedLogs,
    timeoutLogs
  };
}
