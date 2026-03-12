<template>
  <el-row :gutter="16" class="probe-summary-grid">
    <el-col v-for="card in cards" :key="card.label" :lg="6" :md="12" :sm="12" :xs="24">
      <div class="summary-card">
        <p>{{ card.label }}</p>
        <h3>{{ card.value }}</h3>
        <small>{{ card.description }}</small>
      </div>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
interface SummaryCard {
  label: string;
  value: string | number;
  description: string;
}

const props = defineProps<{ cards: SummaryCard[] }>();
</script>

<style scoped>
.probe-summary-grid {
  margin-bottom: 8px;
}

.summary-card {
  background: var(--oa-bg-panel);
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid var(--oa-border-color);
  box-shadow: var(--oa-shadow-sm);
  min-height: 104px;
}
.summary-card p {
  margin: 0;
  color: var(--oa-text-secondary);
  font-size: 12px;
}
.summary-card h3 {
  margin: 6px 0 2px;
  font-size: 20px;
  font-weight: 600;
  color: var(--oa-text-primary);
}
.summary-card small {
  color: var(--oa-text-muted);
  font-size: 12px;
}
</style>
