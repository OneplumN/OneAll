<template>
  <el-card shadow="never" class="panel-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <div>
          <h3>异常节点</h3>
        </div>
      </div>
    </template>
    <div class="nodes-grid">
      <div class="node-stat">
        <h4>心跳延迟TOP</h4>
        <ul>
          <li v-for="node in latencyNodes" :key="node.id">
            <strong>{{ node.name }}</strong>
            <span>{{ formatDelay(node.heartbeat_delay_seconds) }}</span>
          </li>
          <li v-if="!latencyNodes.length" class="text-muted">暂无</li>
        </ul>
      </div>
      <div class="node-stat">
        <h4>执行失败TOP</h4>
        <ul>
          <li v-for="item in failureNodes" :key="item.id">
            <strong>{{ item.name }}</strong>
            <span>{{ item.failed }} 次失败</span>
          </li>
          <li v-if="!failureNodes.length" class="text-muted">暂无</li>
        </ul>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">

interface LatencyNode {
  id: string;
  name: string;
  heartbeat_delay_seconds: number | null;
}
interface FailureNode {
  id: string;
  name: string;
  failed: number;
}

const props = defineProps<{ loading: boolean; latencyNodes: LatencyNode[]; failureNodes: FailureNode[] }>();
const formatDelay = (seconds: number | null) => {
  if (!seconds || seconds < 0) return '—';
  if (seconds < 60) return `${seconds.toFixed(0)} 秒`;
  const minutes = seconds / 60;
  if (minutes < 60) return `${minutes.toFixed(1)} 分钟`;
  const hours = minutes / 60;
  return `${hours.toFixed(1)} 小时`;
};
</script>

<style scoped>
.nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}
.node-stat {
  border-radius: 10px;
  border: 1px solid var(--oa-border-color);
  background: var(--oa-bg-muted);
  padding: 0.75rem 1rem;
}
.node-stat h4 {
  margin: 0 0 0.5rem;
  color: var(--oa-text-primary);
  font-size: 13px;
}
.node-stat ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.node-stat li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--oa-text-secondary);
}
.node-stat li strong {
  color: var(--oa-text-primary);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.node-stat li span {
  color: var(--oa-text-secondary);
  white-space: nowrap;
}
.text-muted {
  color: var(--oa-text-muted);
  font-style: italic;
}
</style>
