<template>
  <div class="code-editor">
    <div class="code-editor__toolbar">
      <slot name="toolbar" />
      <div class="code-editor__actions">
        <el-tag
          size="small"
          effect="plain"
        >
          {{ languageLabel }}
        </el-tag>
        <el-button
          v-if="props.showFullscreenButton !== false"
          text
          size="small"
          @click="fullScreen = true"
        >
          放大
        </el-button>
      </div>
    </div>
    <div
      class="code-editor__pane"
      :style="paneStyle"
    >
      <pre
        ref="inlinePre"
        class="code-editor__highlight"
        aria-hidden="true"
      ><code v-html="highlighted" /><!-- eslint-disable-line vue/no-v-html --></pre>
      <textarea
        v-model="innerValue"
        class="code-editor__textarea"
        :placeholder="placeholder"
        :rows="rows"
        spellcheck="false"
        @scroll="syncScroll($event.target as HTMLTextAreaElement, inlinePre)"
      />
    </div>
    <el-dialog
      v-model="fullScreen"
      title="代码编辑"
      width="80%"
      top="5vh"
      append-to-body
      destroy-on-close
      class="code-editor__dialog"
    >
      <div class="code-editor__pane code-editor__pane--fullscreen">
        <pre
          ref="dialogPre"
          class="code-editor__highlight"
          aria-hidden="true"
        ><code v-html="highlighted" /><!-- eslint-disable-line vue/no-v-html --></pre>
        <textarea
          v-model="innerValue"
          class="code-editor__textarea"
          spellcheck="false"
          rows="20"
          @scroll="syncScroll($event.target as HTMLTextAreaElement, dialogPre)"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import bash from 'highlight.js/lib/languages/bash';
import powershell from 'highlight.js/lib/languages/powershell';
import go from 'highlight.js/lib/languages/go';
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import java from 'highlight.js/lib/languages/java';
import xml from 'highlight.js/lib/languages/xml';
import yamlLang from 'highlight.js/lib/languages/yaml';
import json from 'highlight.js/lib/languages/json';
import sql from 'highlight.js/lib/languages/sql';

hljs.registerLanguage('python', python);
hljs.registerLanguage('shell', bash);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('powershell', powershell);
hljs.registerLanguage('go', go);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('java', java);
hljs.registerLanguage('xml', xml);
hljs.registerLanguage('yaml', yamlLang);
hljs.registerLanguage('json', json);
hljs.registerLanguage('sql', sql);

const LANGUAGE_LABELS: Record<string, string> = {
  python: 'Python',
  shell: 'Shell',
  bash: 'Bash',
  powershell: 'PowerShell',
  go: 'Go',
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  java: 'Java',
  xml: 'XML',
  yaml: 'YAML',
  json: 'JSON',
  sql: 'SQL',
  other: 'Other'
};

const props = defineProps<{
  modelValue?: string;
  language?: string;
  placeholder?: string;
  rows?: number;
  height?: string | number;
  showFullscreenButton?: boolean;
}>();
const emit = defineEmits(['update:modelValue']);

const innerValue = ref(props.modelValue || '');
watch(
  () => props.modelValue,
  (val) => {
    if (val !== innerValue.value) innerValue.value = val || '';
  }
);
watch(innerValue, (val) => emit('update:modelValue', val));

const languageKey = computed(() => (props.language ? props.language.toLowerCase() : ''));
const highlighted = computed(() => {
  const code = innerValue.value || '';
  const lang = languageKey.value;
  if (lang && hljs.getLanguage(lang)) {
    return hljs.highlight(code, { language: lang }).value;
  }
  return hljs.highlightAuto(code).value;
});

const languageLabel = computed(() => LANGUAGE_LABELS[languageKey.value] || props.language || 'Code');
const placeholder = computed(() => props.placeholder || '输入脚本代码');
const rows = computed(() => props.rows || 8);
const fullScreen = ref(false);
const paneStyle = computed(() => {
  const style: Record<string, string> = {};
  if (props.height !== undefined) {
    const val = typeof props.height === 'number' ? `${props.height}px` : props.height;
    style.height = val;
    style.minHeight = val;
  }
  return style;
});

const inlinePre = ref<HTMLElement | null>(null);
const dialogPre = ref<HTMLElement | null>(null);

const syncScroll = (textarea: HTMLTextAreaElement, preRef: HTMLElement | null) => {
  if (!preRef) return;
  preRef.scrollTop = textarea.scrollTop;
  preRef.scrollLeft = textarea.scrollLeft;
};
</script>

<style scoped>
.code-editor {
  width: 100%;
}

.code-editor__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.35rem;
}

.code-editor__actions {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.code-editor__pane {
  position: relative;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 0;
  min-height: 180px;
  width: 100%;
  overflow: hidden;
}

.code-editor__pane--fullscreen {
  min-height: 60vh;
  height: calc(80vh - 120px);
}

.code-editor__textarea {
  position: relative;
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  padding: 12px;
  background: transparent;
  color: transparent;
  caret-color: #f8f8f2;
  font-family: 'Fira Code', 'SFMono-Regular', Consolas, monospace;
  font-size: 14px;
  line-height: 1.5;
  z-index: 2;
  height: 100%;
  box-sizing: border-box;
}

.code-editor__textarea:focus {
  outline: none;
  border: none;
  box-shadow: none;
}

.code-editor__textarea::selection {
  background: rgba(255, 255, 255, 0.2);
}

.code-editor__highlight {
  position: absolute;
  inset: 0;
  margin: 0;
  padding: 12px;
  overflow: auto;
  font-family: 'Fira Code', 'SFMono-Regular', Consolas, monospace;
  font-size: 14px;
  line-height: 1.5;
  pointer-events: none;
  color: #f8f8f2;
  white-space: pre-wrap;
  word-wrap: break-word;
  scrollbar-width: none;
}

.code-editor__highlight::-webkit-scrollbar {
  display: none;
}

.code-editor__highlight code {
  display: block;
}

.code-editor__dialog :deep(.el-dialog) {
  max-width: 1100px;
}

.code-editor__dialog :deep(.el-dialog__body) {
  padding: 0 0 12px;
  overflow: hidden;
}
</style>
