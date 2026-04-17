<template>
  <div class="config-item config-item--column">
    <div class="config-item__header">
      <span class="config-item__label">{{ label }}</span>
      <span class="config-item__value">{{ modelValue }}{{ unit }}</span>
    </div>
    <div class="slider-control">
      <el-slider
        :model-value="modelValue"
        :min="min"
        :max="max"
        :step="step"
        :show-tooltip="false"
        @update:model-value="$emit('update:modelValue', $event)"
      />
      <el-input-number
        :model-value="modelValue"
        :min="min"
        :max="max"
        :step="step"
        class="timeout-input"
        @update:model-value="$emit('update:modelValue', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: number;
  label?: string;
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
}

interface Emits {
  'update:modelValue': [value: number];
}

withDefaults(defineProps<Props>(), {
  label: '超时时间',
  unit: 's',
  min: 1,
  max: 120,
  step: 1
});

defineEmits<Emits>();
</script>

<style scoped>
@import '../styles/detection-common.scss';

.timeout-input {
  width: 100px;
}
</style>