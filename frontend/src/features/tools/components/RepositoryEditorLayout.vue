<template>
  <div class="repository-detail-page">
    <div class="detail-layout">
      <div class="detail-left">
        <div class="detail-card__header detail-left__header">
          <h4 class="section-title">
            {{ codeTitle }}
          </h4>
        </div>
        <div class="detail-code-wrapper">
          <CodeEditor
            :model-value="modelValue"
            :language="language"
            :placeholder="placeholder"
            height="100%"
            :show-fullscreen-button="false"
            @update:model-value="emit('update:modelValue', $event)"
          />
        </div>
      </div>
      <div class="detail-right">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CodeEditor from '@/features/tools/components/CodeEditor.vue';

withDefaults(
  defineProps<{
    modelValue: string;
    language?: string;
    placeholder?: string;
    codeTitle?: string;
  }>(),
  {
    language: '',
    placeholder: '暂无代码',
    codeTitle: '脚本代码',
  }
);

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void;
}>();
</script>

<style scoped>
.repository-detail-page {
  margin: 16px 24px 32px;
  padding: 0;
}

.detail-layout {
  display: grid;
  grid-template-columns: 1.6fr 0.8fr;
  gap: 20px;
  align-items: stretch;
}

.detail-left {
  background: var(--oa-bg-panel);
  border: 1px solid var(--oa-border-color);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-left__header {
  justify-content: space-between;
  align-items: center;
}

.detail-right {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-code-wrapper {
  flex: 1;
  height: calc(100vh - 220px);
  min-height: calc(100vh - 220px);
}

.detail-code-wrapper :deep(.code-editor),
.detail-code-wrapper :deep(.monaco-editor),
.detail-code-wrapper :deep(.cm-editor),
.detail-code-wrapper :deep(.CodeMirror) {
  height: 100% !important;
}
</style>
