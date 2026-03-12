<template>
  <div class="alert-templates-view">
    <SettingsPageShell section-title="告警" breadcrumb="通知模板" body-padding="0" :panel-bordered="false">
    <template #actions>
      <el-button class="toolbar-button" @click="goBack">返回</el-button>
      <div class="refresh-card" @click="loadTemplates">
        <el-icon class="refresh-icon" :class="{ spinning: loading }"><Refresh /></el-icon>
        <span>刷新</span>
      </div>
    </template>

    <el-alert v-if="error" type="error" :closable="false" class="mb-2" show-icon>{{ error }}</el-alert>

    <div class="list-page">
      <div class="repository-filters">
        <div class="filters-left">
          <el-button class="toolbar-button toolbar-button--primary" type="primary" @click="openTemplateDialog()">
            新增模板
          </el-button>
        </div>
        <div class="filters-right">
          <el-select v-model="channelTypeFilter" class="pill-input narrow-select" placeholder="通道" clearable>
            <el-option v-for="option in channelTypeOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
          <el-input v-model="keyword" placeholder="搜索模板名称" clearable class="search-input pill-input search-input--compact" />
        </div>
      </div>

      <div class="repository-table">
        <div class="repository-table__card">
          <el-table
            v-loading="loading"
            :data="pagedTemplates"
            height="100%"
            stripe
            empty-text="暂无模板"
            :header-cell-style="tableHeaderStyle"
            :cell-style="tableCellStyle"
          >
            <el-table-column prop="name" label="模板名称" min-width="240" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="template-name">
                  <strong class="cell-title">{{ row.name }}</strong>
                  <el-tag v-if="row.is_default" size="small" type="success" effect="plain">默认</el-tag>
                </div>
                <p class="template-desc">{{ row.description || '—' }}</p>
              </template>
            </el-table-column>
            <el-table-column prop="channel_type" label="通道" width="180">
              <template #default="{ row }">
                {{ channelTypeMap[row.channel_type] || row.channel_type }}
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" width="200">
              <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <div class="row-actions">
                  <el-button text size="small" @click="openTemplateDialog(row)">编辑</el-button>
                  <el-button text size="small" type="primary" :disabled="row.is_default" @click="setTemplateDefault(row)">
                    设为默认
                  </el-button>
                  <el-button text type="danger" size="small" @click="handleTemplateDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="repository-table__footer">
        <div class="footer-left">
          <div class="repository-stats">共 {{ filteredTemplates.length }} 条</div>
          <el-pagination
            :total="filteredTemplates.length"
            :current-page="currentPage"
            :page-size="pageSize"
            :page-sizes="pageSizeOptions"
            layout="sizes"
            background
            class="repository-pagination__sizes"
            :disabled="loading"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
        <div class="footer-right">
          <el-pagination
            class="repository-pagination__pager"
            :total="filteredTemplates.length"
            :current-page="currentPage"
            :page-size="pageSize"
            layout="prev, pager, next"
            background
            :disabled="loading"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>
    </SettingsPageShell>

  <el-dialog
    v-model="templateDialog.visible"
    :title="templateDialog.record ? '编辑模板' : '新增模板'"
    width="720px"
    append-to-body
    destroy-on-close
    class="template-dialog"
  >
    <el-form label-width="100px">
      <el-form-item label="通道">
        <el-select v-model="templateDialog.form.channel_type">
          <el-option v-for="option in channelTypeOptions" :key="option.value" :label="option.label" :value="option.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="名称">
        <el-input v-model="templateDialog.form.name" placeholder="例如：默认模板" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="templateDialog.form.description" placeholder="可选" />
      </el-form-item>
      <el-form-item label="主题">
        <el-input v-model="templateDialog.form.subject" placeholder="仅对邮件等支持主题的通道生效" />
      </el-form-item>
      <el-form-item label="内容" class="template-content-item">
        <div class="template-editor">
          <section class="variable-panel">
            <div class="variable-panel__header">
              <strong>模板变量</strong>
              <p>点击变量插入对应占位符</p>
            </div>
            <el-scrollbar class="variable-panel__list" height="240px">
              <div v-for="(desc, key) in templateDialog.variables" :key="key" class="variable-panel__item" @click="insertVariable(key)">
                <code>{ {{ key }} }</code>
                <span>{{ desc }}</span>
              </div>
            </el-scrollbar>
          </section>
          <div class="editor-panel">
            <el-input
              type="textarea"
              :rows="8"
              v-model="templateDialog.form.body"
              placeholder="支持变量，如 {title}、{severity}"
              class="template-body-textarea"
            />
          </div>
        </div>
      </el-form-item>
      <el-form-item label="设为默认">
        <el-switch v-model="templateDialog.form.is_default" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="templateDialog.visible = false">取消</el-button>
      <el-button type="primary" :loading="templateDialog.loading" @click="submitTemplate">保存</el-button>
    </template>
  </el-dialog>

  <el-button
    v-if="templateDialog.visible"
    class="variable-fab"
    type="primary"
    circle
    @click="variablePanelVisible = true"
    title="查看通知变量"
  >
    <el-icon><Collection /></el-icon>
  </el-button>

  <el-drawer v-model="variablePanelVisible" direction="rtl" size="320px" title="通知变量">
    <p class="drawer-hint">点击变量即可插入到当前模板内容。</p>
    <el-descriptions :column="1" border>
      <el-descriptions-item v-for="(desc, key) in templateDialog.variables" :key="key" :label="`{${key}}`">
        <span class="variable-item" @click="insertVariable(key)">{{ desc }}</span>
      </el-descriptions-item>
    </el-descriptions>
  </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { Collection, Refresh } from '@element-plus/icons-vue';
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router';

import type { AlertTemplateRecord } from '@/services/settingsApi';
import { createAlertTemplate, deleteAlertTemplate, fetchAlertTemplates, updateAlertTemplate } from '@/services/settingsApi';
import SettingsPageShell from './components/SettingsPageShell.vue';

const router = useRouter();
const route = useRoute();

const channelTypeOptions = [
  { value: 'email', label: '邮件' },
  { value: 'wecom', label: '企业微信机器人' },
  { value: 'dingtalk', label: '钉钉机器人' },
  { value: 'lark', label: '飞书机器人' },
  { value: 'http', label: 'HTTP 回调' },
  { value: 'script', label: '脚本执行' },
];

const channelTypeMap = channelTypeOptions.reduce<Record<string, string>>((map, item) => {
  map[item.value] = item.label;
  return map;
}, {});

const AVAILABLE_VARIABLES: Record<string, string> = {
  title: '告警标题',
  severity: '告警级别，例如 critical/warning',
  status: '告警状态，如 triggered/resolved',
  timestamp: '触发时间 (ISO 格式)',
  task_name: '任务名称或目标',
  probe_name: '探针或执行节点名称',
  message: '详细描述或错误信息',
  result_url: '控制台查看详情链接',
};

const templates = ref<AlertTemplateRecord[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const keyword = ref('');
const channelTypeFilter = ref<string>('');

const pageSizeOptions = [10, 20, 50];
const currentPage = ref(1);
const pageSize = ref(20);

const templateDialog = reactive({
  visible: false,
  loading: false,
  record: null as AlertTemplateRecord | null,
  form: {
    channel_type: 'email',
    name: '',
    description: '',
    subject: '',
    body: '',
    is_default: false,
  },
  variables: AVAILABLE_VARIABLES as Record<string, string>,
});

const variablePanelVisible = ref(false);

const goBack = () => {
  router.push({ name: 'settings-alerts' });
};

const loadTemplates = async () => {
  loading.value = true;
  error.value = null;
  try {
    templates.value = await fetchAlertTemplates();
  } catch {
    error.value = '无法加载告警模板，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

const filteredTemplates = computed(() => {
  const k = keyword.value.trim().toLowerCase();
  return templates.value.filter((tpl) => {
    if (channelTypeFilter.value && tpl.channel_type !== channelTypeFilter.value) return false;
    if (!k) return true;
    return `${tpl.name} ${tpl.description || ''}`.toLowerCase().includes(k);
  });
});

const pagedTemplates = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredTemplates.value.slice(start, start + pageSize.value);
});

const handlePageSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
};

const formatDate = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

const openTemplateDialog = (record?: AlertTemplateRecord) => {
  templateDialog.visible = true;
  templateDialog.record = record || null;
  templateDialog.form = {
    channel_type: record?.channel_type || (channelTypeFilter.value || 'email'),
    name: record?.name || '',
    description: record?.description || '',
    subject: record?.subject || '',
    body: record?.body || '',
    is_default: record?.is_default || false,
  };
  templateDialog.variables = record?.variables || AVAILABLE_VARIABLES;
};

const submitTemplate = async () => {
  templateDialog.loading = true;
  try {
    if (templateDialog.record) {
      await updateAlertTemplate(templateDialog.record.id, templateDialog.form);
    } else {
      await createAlertTemplate(templateDialog.form);
    }
    templateDialog.visible = false;
    await loadTemplates();
    ElMessage.success('模板已保存');
  } catch (error: any) {
    const detail = error?.response?.data?.detail || '保存模板失败';
    ElMessage.error(detail);
  } finally {
    templateDialog.loading = false;
  }
};

const handleTemplateDelete = async (record: AlertTemplateRecord) => {
  try {
    await deleteAlertTemplate(record.id);
    await loadTemplates();
    ElMessage.success('模板已删除');
  } catch (error) {
    ElMessage.error('删除模板失败');
  }
};

const setTemplateDefault = async (record: AlertTemplateRecord) => {
  if (record.is_default) return;
  try {
    await updateAlertTemplate(record.id, { is_default: true });
    await loadTemplates();
    ElMessage.success('已设为默认模板');
  } catch {
    ElMessage.error('设置默认模板失败');
  }
};

const insertVariable = (key: string) => {
  const textarea = document.querySelector<HTMLTextAreaElement>('.template-body-textarea textarea');
  if (!textarea) {
    templateDialog.form.body += ` {${key}}`;
    return;
  }
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const value = templateDialog.form.body;
  templateDialog.form.body = `${value.slice(0, start)}{${key}}${value.slice(end)}`;
  nextTick(() => {
    textarea.focus();
    const cursor = start + key.length + 2;
    textarea.setSelectionRange(cursor, cursor);
  });
};

const tableHeaderStyle = () => ({
  background: 'var(--oa-bg-muted)',
  color: 'var(--oa-text-secondary)',
  fontWeight: 600,
  height: '44px',
});

const tableCellStyle = () => ({
  height: '44px',
  padding: '6px 8px',
});

watch(
  () => [keyword.value, channelTypeFilter.value] as const,
  () => {
    currentPage.value = 1;
  }
);

watch(
  () => [filteredTemplates.value.length, pageSize.value] as const,
  () => {
    const maxPage = Math.max(1, Math.ceil(filteredTemplates.value.length / pageSize.value));
    if (currentPage.value > maxPage) currentPage.value = maxPage;
  }
);

watch(
  () => templateDialog.visible,
  (visible) => {
    if (!visible) variablePanelVisible.value = false;
  }
);

onMounted(async () => {
  const preset = route.query.channel_type;
  if (typeof preset === 'string' && preset) channelTypeFilter.value = preset;
  await loadTemplates();
});

onBeforeRouteLeave(async () => {
  templateDialog.visible = false;
  variablePanelVisible.value = false;
  await nextTick();
});
</script>

<style scoped>
.alert-templates-view {
  height: 100%;
  min-height: 0;
}

.mb-2 {
  margin-bottom: 1rem;
}

.list-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.repository-filters {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.filters-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 220px;
}

.search-input--compact {
  max-width: 360px;
}

.narrow-select {
  width: 200px;
}

.pill-input :deep(.el-input__wrapper),
.pill-input :deep(.el-select__wrapper) {
  border-radius: 999px;
  padding-left: 0.85rem;
  background: var(--oa-filter-control-bg);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}

.repository-table {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--oa-bg-panel);
  padding: 0 16px 12px;
}

.repository-table__card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: none;
}

.repository-table__card :deep(.el-table) {
  flex: 1;
  overflow-x: hidden;
}

.repository-table__card :deep(.el-table__inner-wrapper) {
  border: none !important;
}

.repository-table__card :deep(.el-table__cell) {
  padding: 8px 10px;
}

.repository-table__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 0px 16px 12px;
  color: var(--oa-text-secondary);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-right {
  margin-left: auto;
}

.repository-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.cell-title {
  font-weight: 600;
}

.template-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-desc {
  margin: 2px 0 0;
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.row-actions {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
}

.row-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.template-content-item :deep(.el-form-item__content) {
  align-items: stretch;
}

.template-editor {
  display: flex;
  gap: 1rem;
  width: 100%;
}

.variable-panel {
  width: 220px;
  border: 1px solid var(--oa-border-light);
  border-radius: 12px;
  padding: 1rem;
  background: #fafcff;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.variable-panel__header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.variable-panel__header p {
  margin: 0;
  font-size: 12px;
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
  font-size: 12px;
  color: var(--el-color-primary);
}

.variable-panel__item span {
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.editor-panel {
  flex: 1;
}

.editor-panel :deep(.el-textarea__inner) {
  min-height: 260px;
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
  font-size: 13px;
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

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.08);
  cursor: pointer;
  user-select: none;
}

.refresh-card:hover {
  background: rgba(15, 23, 42, 0.06);
}

.refresh-icon {
  transition: transform 0.35s ease;
}

.refresh-icon.spinning {
  animation: spinning 0.9s linear infinite;
}

@keyframes spinning {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
