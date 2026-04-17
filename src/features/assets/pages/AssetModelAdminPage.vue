<template>
  <RepositoryPageShell
    root-title="资产中心"
    section-title="模型管理"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <el-button
        type="primary"
        class="toolbar-button"
        @click="openCreateModelDialog"
      >
        新建模型
      </el-button>
      <el-button
        class="toolbar-button"
        plain
        :loading="loading"
        @click="loadAssetModels"
      >
        刷新
      </el-button>
    </template>

    <div class="oa-list-page">
      <div class="page-toolbar page-toolbar--panel">
        <div class="page-toolbar__left">
          <div class="asset-page-intro__text">
            <h3>资产模型管理</h3>
            <p>为不同来源的资产定义结构与同步脚本，实现统一纳管。</p>
          </div>
        </div>
      </div>

      <div class="oa-table-panel">
        <div class="oa-table-panel__card asset-table__card">
          <el-table
            v-loading="loading"
            :data="assetModels"
            border
            class="oa-table"
            height="100%"
          >
            <el-table-column
              prop="label"
              label="模型名称"
              min-width="160"
            />
            <el-table-column
              prop="key"
              label="标识"
              min-width="160"
            />
            <el-table-column
              prop="category"
              label="分类"
              min-width="120"
            />
            <el-table-column
              label="字段数"
              width="90"
            >
              <template #default="{ row }">
                {{ row.fields?.length ?? 0 }}
              </template>
            </el-table-column>
            <el-table-column
              label="唯一键"
              min-width="200"
            >
              <template #default="{ row }">
                {{ (row.unique_key || []).join(' / ') || '未配置' }}
              </template>
            </el-table-column>
            <el-table-column
              label="脚本"
              min-width="140"
            >
              <template #default="{ row }">
                <el-tag
                  v-if="row.script_id"
                  size="small"
                  type="success"
                  effect="light"
                >
                  已绑定
                </el-tag>
                <el-tag
                  v-else
                  size="small"
                  type="info"
                  effect="plain"
                >
                  未绑定
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              min-width="260"
            >
              <template #default="{ row }">
                <el-button
                  class="oa-table-action oa-table-action--primary"
                  size="small"
                  text
                  type="primary"
                  @click="openEditModelDialog(row)"
                >
                  编辑模型
                </el-button>
                <el-button
                  class="oa-table-action oa-table-action--primary"
                  size="small"
                  text
                  type="primary"
                  :disabled="!row.script_id"
                  @click="() => triggerModelSync(row)"
                >
                  同步资产
                </el-button>
                <el-dropdown
                  trigger="click"
                  @command="(command: string) => handleScriptCommand(command, row)"
                >
                  <el-button
                    class="oa-table-action oa-table-action--primary"
                    size="small"
                    text
                    type="primary"
                  >
                    脚本
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        command="download-current"
                        :disabled="!row.script_id"
                      >
                        下载当前脚本
                      </el-dropdown-item>
                      <el-dropdown-item command="download-template">
                        下载模板
                      </el-dropdown-item>
                      <el-dropdown-item command="upload">
                        上传脚本
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- 隐藏的脚本上传输入 -->
    <input
      ref="scriptFileInputRef"
      class="hidden-file-input"
      type="file"
      accept=".py"
      @change="handleScriptFileChange"
    >

    <!-- 模型编辑对话框 -->
    <el-dialog
      v-model="modelDialogVisible"
      class="asset-model-dialog"
      :title="modelDialogMode === 'create' ? '新建资产模型' : `编辑资产模型 · ${modelForm.label || modelForm.key}`"
      width="780px"
    >
      <el-form
        label-width="100px"
        class="asset-model-form"
      >
        <el-form-item label="标识">
          <el-input
            v-model="modelForm.key"
            :disabled="Boolean(modelForm.id)"
            placeholder="例如 aliyun-account"
          />
        </el-form-item>
        <el-form-item label="名称">
          <el-input
            v-model="modelForm.label"
            placeholder="例如 阿里云账号"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-input
            v-model="modelForm.category"
            placeholder="例如 cmdb、monitoring、workorder"
          />
        </el-form-item>

        <el-divider content-position="left">
          字段定义
        </el-divider>
        <div class="asset-model-fields">
          <el-table
            :data="modelFieldDrafts"
            border
            class="oa-table asset-model-fields-table"
          >
            <el-table-column
              label="字段 Key"
              min-width="150"
            >
              <template #default="{ row }">
                <el-input
                  v-model="row.key"
                  size="small"
                  placeholder="例如 account_id"
                />
              </template>
            </el-table-column>
            <el-table-column
              label="名称"
              min-width="150"
            >
              <template #default="{ row }">
                <el-input
                  v-model="row.label"
                  size="small"
                  placeholder="例如 账号ID"
                />
              </template>
            </el-table-column>
            <el-table-column
              label="类型"
              width="120"
            >
              <template #default="{ row }">
                <el-select
                  v-model="row.type"
                  size="small"
                  placeholder="类型"
                >
                  <el-option
                    label="文本"
                    value="string"
                  />
                  <el-option
                    label="数字"
                    value="number"
                  />
                  <el-option
                    label="布尔"
                    value="boolean"
                  />
                  <el-option
                    label="枚举"
                    value="enum"
                  />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="90"
            >
              <template #default="{ $index }">
                <el-button
                  size="small"
                  text
                  type="danger"
                  @click="removeModelField($index)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="asset-model-fields-actions">
            <el-button
              size="small"
              type="primary"
              plain
              @click="addModelField"
            >
              新增字段
            </el-button>
          </div>
        </div>

        <el-form-item label="唯一键字段">
          <el-select
            v-model="modelForm.unique_key"
            multiple
            filterable
            collapse-tags
            placeholder="从上方字段中选择组成业务唯一键的字段"
          >
            <el-option
              v-for="field in modelFieldDrafts"
              :key="field.key || field.label"
              :label="field.label || field.key"
              :value="field.key"
              :disabled="!field.key"
            />
          </el-select>
        </el-form-item>
        <p class="asset-model-hint">
          唯一键需引用字段列表中的 Key，用于避免资产重复导入。
        </p>
      </el-form>

      <template #footer>
        <el-button @click="modelDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="saveAssetModel"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';

import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import type { AssetModel } from '@/features/assets/api/assetsApi';
import {
  fetchAssetModels,
  createAssetModel,
  updateAssetModel,
  uploadAssetModelScript,
  downloadAssetModelScriptTemplate,
  downloadAssetModelScript,
  syncAssetModel
} from '@/features/assets/api/assetsApi';

const loading = ref(false);
const assetModels = ref<AssetModel[]>([]);

const modelDialogVisible = ref(false);
const modelDialogMode = ref<'create' | 'edit'>('create');
const modelForm = ref<{
  id?: string;
  key: string;
  label: string;
  category: string;
  unique_key: string[];
}>({
  key: '',
  label: '',
  category: '',
  unique_key: []
});

const modelFieldDrafts = ref<Array<{ key: string; label: string; type?: string }>>([]);

const scriptFileInputRef = ref<HTMLInputElement | null>(null);
const scriptTargetModelId = ref<string | null>(null);

const loadAssetModels = async () => {
  loading.value = true;
  try {
    const data = await fetchAssetModels();
    assetModels.value = data || [];
  } catch (err) {
    ElMessage.error('加载资产模型失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

const openCreateModelDialog = () => {
  modelDialogMode.value = 'create';
  modelForm.value = reactive({
    key: '',
    label: '',
    category: '',
    unique_key: [] as string[]
  });
  modelFieldDrafts.value = [];
  modelDialogVisible.value = true;
};

const openEditModelDialog = (model: AssetModel) => {
  modelDialogMode.value = 'edit';
  modelForm.value = reactive({
    id: model.id,
    key: model.key,
    label: model.label,
    category: model.category || '',
    unique_key: [...(model.unique_key || [])]
  });
  modelFieldDrafts.value = (model.fields || []).map((field) => ({
    key: field.key,
    label: field.label || field.key,
    type: field.type || 'string'
  }));
  modelDialogVisible.value = true;
};

const addModelField = () => {
  modelFieldDrafts.value.push({
    key: '',
    label: '',
    type: 'string'
  });
};

const removeModelField = (index: number) => {
  modelFieldDrafts.value.splice(index, 1);
  const currentKeys = new Set(modelFieldDrafts.value.map((f) => f.key).filter(Boolean));
  modelForm.value.unique_key = (modelForm.value.unique_key || []).filter((key) => currentKeys.has(key));
};

const saveAssetModel = async () => {
  const fields = modelFieldDrafts.value
    .filter((f) => f.key && f.label)
    .map((f) => ({
      key: String(f.key).trim(),
      label: String(f.label).trim(),
      type: f.type || 'string'
    }));

  const uniqueKeys = (modelForm.value.unique_key || []).map((key) => String(key).trim()).filter(Boolean);

  if (!modelForm.value.key.trim()) {
    ElMessage.warning('请填写模型标识');
    return;
  }
  if (!modelForm.value.label.trim()) {
    ElMessage.warning('请填写模型名称');
    return;
  }

  try {
    const payload = {
      key: modelForm.value.key.trim(),
      label: modelForm.value.label.trim(),
      category: (modelForm.value.category || '').trim(),
      fields,
      unique_key: uniqueKeys,
      is_active: true
    };

    let updated: AssetModel;
    if (modelDialogMode.value === 'create') {
      updated = await createAssetModel(payload);
      assetModels.value = [...assetModels.value, updated];
      ElMessage.success('模型已创建');
    } else if (modelForm.value.id) {
      updated = await updateAssetModel(modelForm.value.id, payload);
      assetModels.value = assetModels.value.map((m) => (m.id === updated.id ? updated : m));
      ElMessage.success('模型已更新');
    } else {
      return;
    }
    modelDialogVisible.value = false;
  } catch (err: any) {
    const message =
      err?.response?.data?.detail ||
      err?.response?.data?.non_field_errors?.[0] ||
      '模型保存失败，请稍后重试';
    ElMessage.error(message);
  }
};

const triggerScriptUpload = (modelId: string) => {
  scriptTargetModelId.value = modelId;
  scriptFileInputRef.value?.click();
};

const handleScriptCommand = (command: string, model: AssetModel) => {
  if (!model.id) return;
  switch (command) {
    case 'download-current':
      if (model.script_id) {
        downloadCurrentScript(model);
      }
      break;
    case 'download-template':
      downloadScriptTemplate(model);
      break;
    case 'upload':
      triggerScriptUpload(model.id);
      break;
    default:
      break;
  }
};

const handleScriptFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement | null;
  const file = input?.files?.[0] || null;
  if (input) {
    input.value = '';
  }
  if (!file || !scriptTargetModelId.value) return;

  try {
    const updated = await uploadAssetModelScript(scriptTargetModelId.value, file);
    assetModels.value = assetModels.value.map((m) => (m.id === updated.id ? updated : m));
    ElMessage.success('脚本已上传并绑定');
  } catch (err: any) {
    const message = err?.response?.data?.detail || '脚本上传失败，请检查文件内容';
    ElMessage.error(message);
  } finally {
    scriptTargetModelId.value = null;
  }
};

const downloadScriptTemplate = async (model: AssetModel) => {
  try {
    const blob = await downloadAssetModelScriptTemplate(model.id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const filename = `asset_sync_${model.key}_template.py`;
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err: any) {
    const message = err?.response?.data?.detail || '模板脚本下载失败，请稍后重试';
    ElMessage.error(message);
  }
};

const downloadCurrentScript = async (model: AssetModel) => {
  try {
    const blob = await downloadAssetModelScript(model.id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const filename = `asset_sync_${model.key}.py`;
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err: any) {
    const message = err?.response?.data?.detail || '当前脚本下载失败，请稍后重试';
    ElMessage.error(message);
  }
};

const triggerModelSync = async (model: AssetModel) => {
  if (!model.id) return;
  try {
    const result = await syncAssetModel(model.id);
    const totals = result.summary?.totals || {};
    const created = totals.created ?? 0;
    const updated = totals.updated ?? 0;
    const removed = totals.removed ?? 0;
    ElMessage.success(
      `资产同步完成：新增 ${created} 条，更新 ${updated} 条${removed ? `，移除 ${removed} 条` : ''}`
    );
  } catch (err: any) {
    const message = resolveSyncErrorMessage(err);
    ElMessage.error(message);
  }
};

function resolveSyncErrorMessage(err: any) {
  const detail = String(err?.response?.data?.detail || '').trim();
  if (!detail) return '资产同步失败，请稍后重试';
  if (detail.includes('尚未配置真实数据源')) {
    return '当前模型尚未配置真实数据源，暂不可同步';
  }
  if (detail.includes('模板示例')) {
    return '当前脚本仍是模板示例，请先完善真实同步逻辑后再执行同步';
  }
  return detail;
}

onMounted(() => {
  loadAssetModels();
});
</script>

<style scoped>
.asset-page-intro__text h3 {
  margin: 0;
  font-size: var(--oa-font-section-title);
  font-weight: 600;
  line-height: 1.4;
  color: var(--oa-text-primary);
}

.asset-page-intro__text p {
  margin: 0.25rem 0 0;
  font-size: var(--oa-font-subtitle);
  line-height: 1.6;
  color: var(--oa-text-secondary);
}

.asset-model-dialog :deep(.el-dialog__title) {
  font-size: var(--oa-font-heading);
  font-weight: 600;
  color: var(--oa-text-primary);
}

.asset-model-dialog :deep(.el-form-item__label) {
  font-size: var(--oa-font-subtitle);
  color: var(--oa-text-secondary);
}

.asset-model-dialog :deep(.el-input__inner),
.asset-model-dialog :deep(.el-textarea__inner),
.asset-model-dialog :deep(.el-select__wrapper),
.asset-model-dialog :deep(.el-input-number__input) {
  font-size: var(--oa-font-base);
}

.asset-table__card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.asset-model-dialog :deep(.el-divider__text) {
  font-size: var(--oa-font-subtitle);
  font-weight: 600;
  color: var(--oa-text-primary);
}

.asset-model-dialog :deep(.el-table .cell) {
  font-size: var(--oa-font-base);
}

.asset-model-dialog :deep(.el-button--small) {
  font-size: var(--oa-font-base);
}

.asset-model-dialog :deep(.el-select__placeholder),
.asset-model-dialog :deep(.el-input__placeholder),
.asset-model-dialog :deep(.el-textarea__inner::placeholder) {
  font-size: var(--oa-font-base);
}

.asset-model-fields {
  margin-bottom: 12px;
}

.asset-model-fields-actions {
  margin-top: 8px;
}

.asset-model-hint {
  margin: 6px 0 0;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-muted);
}

.hidden-file-input {
  display: none;
}
</style>
