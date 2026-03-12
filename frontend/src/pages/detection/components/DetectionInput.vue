<template>
  <div
    class="detection-input-wrapper"
    :class="{ 'detection-input-wrapper--combo': showProtocolSelector }"
  >
    <el-input
      :model-value="modelValue"
      :placeholder="currentPlaceholder"
      :loading="loading"
      :disabled="disabled"
      clearable
      class="detection-input"
      @update:model-value="$emit('update:modelValue', $event)"
      @keyup.enter="$emit('submit')"
      @clear="$emit('clear')"
    >
      <template v-if="showProtocolSelector" #prepend>
        <el-select
          :model-value="protocol"
          class="protocol-select"
          @update:model-value="$emit('update:protocol', $event)"
        >
          <el-option
            v-for="option in protocolOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </template>
    </el-input>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { PROTOCOL_OPTIONS } from '../utils/detectionUtils';

interface Props {
  modelValue: string;
  placeholder?: string;
  protocol?: string;
  loading?: boolean;
  disabled?: boolean;
  showProtocolSelector?: boolean;
  protocolOptions?: Array<{ label: string; value: string }>;
}

interface Emits {
  'update:modelValue': [value: string];
  'update:protocol': [protocol: string];
  submit: [];
  clear: [];
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
  protocol: 'HTTPS',
  loading: false,
  disabled: false,
  showProtocolSelector: false,
  protocolOptions: () => [
    { label: 'HTTP(S)', value: 'HTTPS' },
    { label: 'WebSocket', value: 'WSS' },
    { label: 'Telnet', value: 'Telnet' }
  ]
});

defineEmits<Emits>();

const currentPlaceholder = computed(() => {
  if (props.placeholder) return props.placeholder;
  if (props.protocol && PROTOCOL_OPTIONS[props.protocol as keyof typeof PROTOCOL_OPTIONS]) {
    return PROTOCOL_OPTIONS[props.protocol as keyof typeof PROTOCOL_OPTIONS].placeholder;
  }
  return '请输入目标地址';
});
</script>

<style scoped>
@import '../styles/detection-common.scss';

.detection-input-wrapper {
  flex: 1;
  min-width: 320px;
}

.detection-input-wrapper--combo {
  :deep(.el-input-group__prepend) {
    padding: 0;
    border: none;
    background: transparent;
  }

  /* 组合输入：对齐平台 pill-input（统一底色 + 统一边框 + focus-within 高亮） */
  :deep(.el-input-group) {
    border-radius: var(--oa-radius-full);
    background: var(--oa-bg-muted);
    box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
    transition: box-shadow 0.2s ease;
  }

  :deep(.el-input-group:hover) {
    box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.4);
  }

  :deep(.el-input-group:focus-within) {
    box-shadow: inset 0 0 0 2px var(--el-color-primary);
  }

  :deep(.el-input-group__prepend) {
    box-shadow: none;
  }

  :deep(.protocol-select .el-select__wrapper) {
    border-radius: var(--oa-radius-full) 0 0 var(--oa-radius-full);
    background: transparent;
    box-shadow: none;
    border-right: 1px solid rgba(148, 163, 184, 0.25);
  }

  :deep(.detection-input .el-input__wrapper) {
    border-radius: 0 var(--oa-radius-full) var(--oa-radius-full) 0;
    background: transparent;
    box-shadow: none;
  }

  :deep(.detection-input .el-input__wrapper:hover),
  :deep(.detection-input .el-input__wrapper.is-focus) {
    box-shadow: none;
  }
}

.protocol-select {
  width: 140px;

  :deep(.el-select__wrapper) {
    border-radius: var(--oa-radius-full) 0 0 var(--oa-radius-full);
    background: transparent;
    box-shadow: none;
  }
}

@media (max-width: 768px) {
  .detection-input-wrapper {
    min-width: auto;
    width: 100%;
  }
}
</style>
