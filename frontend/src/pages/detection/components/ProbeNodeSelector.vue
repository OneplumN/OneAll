<template>
  <component
    :is="embedded ? 'section' : 'el-card'"
    v-bind="embedded ? {} : { shadow: 'never' }"
    :class="['node-card', { 'node-card--embedded': embedded }]"
  >
    <div class="node-header">
      <div class="node-header__info">
        <h2 class="node-title">
          <el-icon><Histogram /></el-icon>
          <span>探针节点选择</span>
        </h2>
        <p v-if="hint" class="node-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>{{ hint }}</span>
        </p>
      </div>
      <div class="node-header__meta">
        <span class="selection-count">已选 {{ modelValue.length }} / {{ nodes.length }}</span>
        <el-button
          text
          size="small"
          :disabled="!modelValue.length || loading"
          @click="clearSelection"
        >
          清空
        </el-button>
        <el-button
          type="primary"
          text
          size="small"
          :icon="Refresh"
          :loading="loading"
          @click="$emit('refresh')"
        >
          刷新
        </el-button>
      </div>
    </div>

    <div class="node-groups">
      <section class="node-group">
        <div class="node-group__header">
          <span class="node-group__title">内网</span>
          <span class="node-group__count">({{ internalNodes.length }})</span>
        </div>
        <div v-if="internalNodes.length" class="chip-group">
          <button
            v-for="node in internalNodes"
            :key="node.id"
            type="button"
            class="chip"
            :class="{ active: isSelected(node.id), disabled: loading }"
            :disabled="loading"
            :aria-pressed="isSelected(node.id)"
            @click="toggle(node.id)"
          >
            {{ node.name }}
          </button>
        </div>
        <div v-else class="empty-hint">暂无内网节点</div>
      </section>

      <section class="node-group">
        <div class="node-group__header">
          <span class="node-group__title">互联网</span>
          <span class="node-group__count">({{ externalNodes.length }})</span>
        </div>
        <div v-if="externalNodes.length" class="chip-group">
          <button
            v-for="node in externalNodes"
            :key="node.id"
            type="button"
            class="chip"
            :class="{ active: isSelected(node.id), disabled: loading }"
            :disabled="loading"
            :aria-pressed="isSelected(node.id)"
            @click="toggle(node.id)"
          >
            {{ node.name }}
          </button>
        </div>
        <div v-else class="empty-hint">暂无互联网节点</div>
      </section>

      <section v-if="otherNodes.length" class="node-group">
        <div class="node-group__header">
          <span class="node-group__title">其他</span>
          <span class="node-group__count">({{ otherNodes.length }})</span>
        </div>
        <div class="chip-group">
          <button
            v-for="node in otherNodes"
            :key="node.id"
            type="button"
            class="chip"
            :class="{ active: isSelected(node.id), disabled: loading }"
            :disabled="loading"
            :aria-pressed="isSelected(node.id)"
            @click="toggle(node.id)"
          >
            {{ node.name }}
          </button>
        </div>
      </section>
    </div>
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Histogram, InfoFilled, Refresh } from '@element-plus/icons-vue';

type ProbeNode = {
  id: string;
  name: string;
  network_type: 'internal' | 'external' | string;
};

const props = withDefaults(defineProps<{
  nodes: ProbeNode[];
  modelValue: string[];
  loading?: boolean;
  hint?: string;
  embedded?: boolean;
}>(), {
  loading: false,
  hint: '',
  embedded: false
});

const emit = defineEmits<{
  (event: 'update:modelValue', value: string[]): void;
  (event: 'refresh'): void;
}>();

const internalNodes = computed(() => props.nodes.filter((node) => node.network_type === 'internal'));
const externalNodes = computed(() => props.nodes.filter((node) => node.network_type === 'external'));
const otherNodes = computed(() =>
  props.nodes.filter((node) => node.network_type !== 'internal' && node.network_type !== 'external')
);

function isSelected(id: string) {
  return props.modelValue.includes(id);
}

function toggle(id: string) {
  if (props.loading) return;
  if (isSelected(id)) {
    emit(
      'update:modelValue',
      props.modelValue.filter((item) => item !== id)
    );
    return;
  }
  emit('update:modelValue', [...props.modelValue, id]);
}

function clearSelection() {
  emit('update:modelValue', []);
}
</script>

<style scoped>
.node-card {
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  background: var(--oa-bg-panel);
}

.node-card :deep(.el-card__body) {
  padding: 16px;
}

.node-card--embedded {
  border: none;
  background: transparent;
  padding: 0;
  box-sizing: border-box;
}

.node-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.node-header__info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.node-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--oa-text-primary);
}

.node-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 13px;
  color: var(--oa-text-secondary);
}

.node-hint :deep(.el-icon) {
  color: var(--oa-color-primary);
}

.node-header__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.selection-count {
  font-size: 13px;
  color: var(--oa-text-secondary);
}

.node-groups {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.node-group__header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
}

.node-group__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--oa-text-primary);
}

.node-group__count {
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  border: 1px solid var(--oa-border-color);
  border-radius: var(--oa-radius-full);
  padding: 6px 12px;
  background: var(--oa-bg-muted);
  font-size: 13px;
  color: var(--oa-text-secondary);
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.chip:hover {
  border-color: var(--oa-color-primary-light);
  color: var(--oa-text-primary);
}

.chip.active {
  background: var(--oa-color-primary);
  border-color: var(--oa-color-primary);
  color: var(--oa-text-on-primary);
}

.chip.disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.empty-hint {
  font-size: 12px;
  color: var(--oa-text-secondary);
  padding: 4px 0;
}
</style>
