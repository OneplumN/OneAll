<template>
  <div class="quick-actions">
    <div class="quick-actions__header">
      <h4>快捷操作</h4>
    </div>
    <div class="quick-actions__content">
      <el-button
        v-for="action in actions"
        :key="action.key"
        :type="action.type || 'default'"
        :size="action.size || 'small'"
        :icon="action.icon"
        :loading="action.loading"
        :disabled="action.disabled"
        class="action-button"
        @click="$emit('action', action.key)"
      >
        {{ action.label }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface QuickAction {
  key: string;
  label: string;
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default';
  size?: 'large' | 'default' | 'small';
  icon?: any;
  loading?: boolean;
  disabled?: boolean;
}

interface Props {
  actions: QuickAction[];
}

interface Emits {
  action: [key: string];
}

defineProps<Props>();
defineEmits<Emits>();
</script>

<style scoped>
.quick-actions {
  background: var(--oa-bg-panel);
  border: 1px solid var(--oa-border-light);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.quick-actions__header {
  margin-bottom: 12px;
}

.quick-actions__header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--oa-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.quick-actions__header h4::before {
  content: '';
  width: 3px;
  height: 14px;
  background: var(--el-color-primary);
  border-radius: 2px;
}

.quick-actions__content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-button {
  justify-content: flex-start;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.action-button:hover {
  transform: translateX(2px);
}

@media (max-width: 768px) {
  .quick-actions__content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .action-button {
    justify-content: center;
  }
}
</style>