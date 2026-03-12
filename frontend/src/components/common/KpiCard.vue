<template>
  <div class="kpi-card" :class="`is-${status}`">
    <div class="kpi-header">
      <span class="kpi-title">{{ title }}</span>
      <slot name="icon"></slot>
    </div>
    <div class="kpi-value">{{ displayValue }}</div>
    <div v-if="subtitle" class="kpi-subtitle">{{ subtitle }}</div>
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    title: string;
    value: string | number | null | undefined;
    subtitle?: string;
    formatter?: (value: string | number | null | undefined) => string;
    status?: 'default' | 'success' | 'warning' | 'danger';
  }>(),
  {
    status: 'default',
    formatter: undefined,
    subtitle: undefined
  }
);

const displayValue = computed(() => {
  if (props.formatter) {
    return props.formatter(props.value);
  }
  if (props.value === null || props.value === undefined || props.value === '') {
    return '--';
  }
  return typeof props.value === 'number' ? props.value.toLocaleString() : props.value;
});
</script>

<style scoped>
.kpi-card {
  background-color: var(--oneall-card-bg);
  border: 1px solid var(--oneall-card-border);
  border-radius: 12px;
  padding: 16px 20px;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.kpi-card:hover {
  box-shadow: var(--oneall-card-shadow);
  transform: translateY(-2px);
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
  color: var(--oneall-text-secondary);
}

.kpi-title {
  font-weight: 600;
}

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--oneall-text-primary);
}

.kpi-subtitle {
  font-size: 0.85rem;
  color: var(--oneall-text-secondary);
}

.kpi-card.is-success {
  border-color: var(--oneall-success);
}

.kpi-card.is-info {
  border-color: var(--oneall-info);
}

.kpi-card.is-warning {
  border-color: var(--oneall-warning);
}

.kpi-card.is-danger {
  border-color: var(--oneall-danger);
}
</style>
