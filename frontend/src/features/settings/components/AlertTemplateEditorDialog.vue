<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    width="920px"
    append-to-body
    destroy-on-close
    class="template-dialog"
  >
    <div class="template-dialog__body">
      <section class="template-dialog__section">
        <div class="template-dialog__heading">
          <div class="template-dialog__title">
            基本信息
          </div>
          <div class="template-dialog__subtitle">
            选择通知通道并定义模板的名称、说明与主题。
          </div>
        </div>
        <el-form
          label-position="top"
          class="template-dialog__form"
        >
          <div class="template-dialog__grid">
            <el-form-item label="通知通道">
              <el-select v-model="formModel.channel_type">
                <el-option
                  v-for="option in channelTypeOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="模板名称">
              <el-input
                v-model="formModel.name"
                placeholder="例如：默认模板"
              />
            </el-form-item>
            <el-form-item
              label="模板说明"
              class="template-dialog__grid-span"
            >
              <el-input
                v-model="formModel.description"
                placeholder="可选"
              />
            </el-form-item>
            <el-form-item
              label="通知主题"
              class="template-dialog__grid-span"
            >
              <el-input
                v-model="formModel.subject"
                placeholder="仅对邮件等支持主题的通道生效"
              />
            </el-form-item>
            <el-form-item label="设为默认">
              <el-switch v-model="formModel.is_default" />
            </el-form-item>
          </div>
        </el-form>
      </section>

      <section class="template-dialog__section">
        <div class="template-dialog__heading">
          <div class="template-dialog__title">
            模板内容
          </div>
          <div class="template-dialog__subtitle">
            左侧变量可直接插入到正文中，右侧维护最终通知内容。
          </div>
        </div>

        <div class="template-editor">
          <section class="variable-panel">
            <div class="variable-panel__header">
              <strong>可用变量</strong>
              <p>点击变量即可插入到当前光标位置。</p>
            </div>
            <el-scrollbar
              class="variable-panel__list"
              height="300px"
            >
              <div
                v-for="(desc, key) in variables"
                :key="key"
                class="variable-panel__item"
                @click="insertVariable(key)"
              >
                <code>{ {{ key }} }</code>
                <span>{{ desc }}</span>
              </div>
            </el-scrollbar>
          </section>

          <div class="editor-panel">
            <div class="editor-panel__header">
              <span class="editor-panel__title">正文编辑器</span>
              <span class="editor-panel__hint">支持变量占位，如 {title}、{severity}</span>
            </div>
            <el-input
              v-model="formModel.body"
              type="textarea"
              :rows="12"
              placeholder="请输入通知模板内容"
              class="template-body-textarea"
            />
          </div>
        </div>
      </section>
    </div>

    <template #footer>
      <div class="template-dialog__footer">
        <el-button @click="visibleModel = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="emit('submit')"
        >
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>

  <el-button
    v-if="visibleModel"
    class="variable-fab"
    type="primary"
    circle
    title="查看通知变量"
    @click="variablePanelVisible = true"
  >
    <el-icon><Collection /></el-icon>
  </el-button>

  <el-drawer
    v-model="variablePanelVisible"
    direction="rtl"
    size="320px"
    title="通知变量"
  >
    <p class="drawer-hint">
      点击变量即可插入到当前模板内容。
    </p>
    <el-descriptions
      :column="1"
      border
    >
      <el-descriptions-item
        v-for="(desc, key) in variables"
        :key="key"
        :label="`{${key}}`"
      >
        <span
          class="variable-item"
          @click="insertVariable(key)"
        >{{ desc }}</span>
      </el-descriptions-item>
    </el-descriptions>
  </el-drawer>
</template>

<script setup lang="ts">
import { Collection } from '@element-plus/icons-vue';
import { nextTick, ref, watch } from 'vue';

type ChannelTypeOption = {
  value: string;
  label: string;
};

type TemplateForm = {
  channel_type: string;
  name: string;
  description: string;
  subject: string;
  body: string;
  is_default: boolean;
};

const visibleModel = defineModel<boolean>('visible', { required: true });
const formModel = defineModel<TemplateForm>('form', { required: true });

defineProps<{
  title: string;
  loading: boolean;
  variables: Record<string, string>;
  channelTypeOptions: ChannelTypeOption[];
}>();

const emit = defineEmits<{
  (event: 'submit'): void;
}>();

const variablePanelVisible = ref(false);

function insertVariable(key: string) {
  const textarea = document.querySelector<HTMLTextAreaElement>('.template-body-textarea textarea');
  if (!textarea) {
    formModel.value.body += ` {${key}}`;
    return;
  }
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const value = formModel.value.body;
  formModel.value.body = `${value.slice(0, start)}{${key}}${value.slice(end)}`;
  nextTick(() => {
    textarea.focus();
    const cursor = start + key.length + 2;
    textarea.setSelectionRange(cursor, cursor);
  });
}

watch(visibleModel, (visible) => {
  if (!visible) variablePanelVisible.value = false;
});
</script>

<style scoped>
.template-dialog__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.template-dialog__section {
  border: 1px solid var(--oa-border-light);
  border-radius: 12px;
  background: var(--oa-bg-panel);
  padding: 18px;
}

.template-dialog__heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.template-dialog__title {
  font-size: var(--oa-font-section-title);
  font-weight: 600;
  color: var(--oa-text-primary);
}

.template-dialog__subtitle {
  font-size: var(--oa-font-subtitle);
  color: var(--oa-text-secondary);
}

.template-dialog__form :deep(.el-form-item) {
  margin-bottom: 0;
}

.template-dialog__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.template-dialog__grid-span {
  grid-column: 1 / -1;
}

.template-editor {
  display: flex;
  gap: 16px;
  width: 100%;
}

.variable-panel {
  width: 250px;
  border: 1px solid var(--oa-border-light);
  border-radius: 12px;
  padding: 16px;
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.04), rgba(37, 99, 235, 0.01));
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.variable-panel__header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.variable-panel__header p {
  margin: 0;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.variable-panel__list {
  flex: 1;
}

.variable-panel__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border-radius: 8px;
  border: 1px dashed transparent;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.variable-panel__item:hover {
  border-color: var(--el-color-primary);
  background: rgba(64, 158, 255, 0.08);
}

.variable-panel__item code {
  font-family: 'JetBrains Mono', SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: var(--oa-font-meta);
  color: var(--el-color-primary);
}

.variable-panel__item span {
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.editor-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  background: var(--oa-bg-muted);
}

.editor-panel__title {
  font-size: var(--oa-font-subtitle);
  font-weight: 600;
  color: var(--oa-text-primary);
}

.editor-panel__hint {
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.editor-panel :deep(.el-textarea__inner) {
  min-height: 320px;
  border-radius: 12px;
  line-height: 1.6;
}

.template-dialog__footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.variable-fab {
  position: fixed;
  right: 32px;
  bottom: 48px;
  z-index: 20;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.2);
}

.drawer-hint {
  margin-bottom: 12px;
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-subtitle);
}

.variable-item {
  cursor: pointer;
}

.variable-item:hover {
  color: var(--el-color-primary);
}

.template-dialog :deep(.el-dialog) {
  margin-top: 8vh;
  max-height: calc(100vh - 16vh);
  display: flex;
  flex-direction: column;
}

.template-dialog :deep(.el-dialog__body) {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

@media (max-width: 960px) {
  .template-dialog__grid {
    grid-template-columns: 1fr;
  }

  .template-dialog__grid-span {
    grid-column: auto;
  }

  .template-editor {
    flex-direction: column;
  }

  .variable-panel {
    width: 100%;
  }

  .editor-panel__header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
