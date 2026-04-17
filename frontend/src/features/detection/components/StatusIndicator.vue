<template>
  <div
    class="status-indicator"
    :class="statusClass"
  >
    <div class="status-dot" />
    <span class="status-text">{{ displayText }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { getStatusText, getStatusTagType } from '../mappers/detectionUtils';

interface Props {
  status: string;
  showDot?: boolean;
  size?: 'small' | 'medium' | 'large';
}

const props = withDefaults(defineProps<Props>(), {
  showDot: true,
  size: 'medium'
});

const displayText = computed(() => getStatusText(props.status));
const statusType = computed(() => getStatusTagType(props.status));

const statusClass = computed(() => [
  `status-indicator--${statusType.value}`,
  `status-indicator--${props.size}`,
  { 'status-indicator--no-dot': !props.showDot }
]);
</script>

<style scoped>
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  border-radius: 6px;
  padding: 4px 8px;
  transition: all 0.2s ease;
}

.status-indicator--small {
  font-size: 12px;
  padding: 2px 6px;
  gap: 4px;
}

.status-indicator--medium {
  font-size: 14px;
  padding: 4px 8px;
  gap: 6px;
}

.status-indicator--large {
  font-size: 16px;
  padding: 6px 12px;
  gap: 8px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-indicator--small .status-dot {
  width: 4px;
  height: 4px;
}

.status-indicator--large .status-dot {
  width: 8px;
  height: 8px;
}

.status-indicator--no-dot .status-dot {
  display: none;
}

/* Success状态 */
.status-indicator--success {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.2);
}

.status-indicator--success .status-dot {
  background: #67c23a;
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.2);
}

/* Warning状态 */
.status-indicator--warning {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
  border: 1px solid rgba(230, 162, 60, 0.2);
}

.status-indicator--warning .status-dot {
  background: #e6a23c;
  box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.2);
}

/* Danger状态 */
.status-indicator--danger {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.2);
}

.status-indicator--danger .status-dot {
  background: #f56c6c;
  box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.2);
}

/* Info状态 */
.status-indicator--info {
  background: rgba(144, 147, 153, 0.1);
  color: #909399;
  border: 1px solid rgba(144, 147, 153, 0.2);
}

.status-indicator--info .status-dot {
  background: #909399;
  box-shadow: 0 0 0 2px rgba(144, 147, 153, 0.2);
}

/* 动画效果 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.status-indicator--info .status-dot {
  animation: pulse 2s infinite;
}
</style>