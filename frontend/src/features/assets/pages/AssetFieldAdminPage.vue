<template>
  <RepositoryPageShell
    root-title="资产中心"
    section-title="字段管理"
    body-padding="0"
    :panel-bordered="false"
  >
    <div class="oa-list-page">
      <div class="page-toolbar page-toolbar--panel">
        <div class="page-toolbar__left">
          <div class="asset-page-intro__text">
            <h3>资产字段配置</h3>
            <p>为不同资产类型配置业务唯一键与管理字段，用于去重、聚合与第三方对接。</p>
          </div>
        </div>
      </div>

      <div
        v-if="assetTypesLoading"
        class="asset-settings-loading"
      >
        <el-skeleton
          :rows="2"
          animated
        />
      </div>
      <div
        v-else
        class="asset-settings-content"
      >
        <el-alert
          v-if="!assetTypes.length"
          type="info"
          show-icon
          :closable="false"
          class="asset-settings-alert"
        >
          暂无资产类型定义，当前将按后端默认规则生成唯一键。
        </el-alert>

        <div
          v-else
          class="oa-table-panel"
        >
          <div class="oa-table-panel__card asset-table__card">
            <el-table
              :data="assetTypeRows"
              border
              class="oa-table asset-types-el-table"
            >
              <el-table-column
                prop="label"
                label="资产类型"
                min-width="160"
              />
              <el-table-column
                prop="key"
                label="标识"
                min-width="160"
              />
              <el-table-column
                label="业务唯一字段"
                min-width="260"
              >
                <template #default="{ row }">
                  <el-select
                    class="asset-unique-select"
                    :model-value="row.uniqueFields"
                    multiple
                    filterable
                    placeholder="例如 domain、ip、app_code"
                    @update:model-value="(value: string[]) => handleAssetUniqueFieldsChange(row.key, value)"
                  >
                    <el-option
                      v-for="field in fieldOptionsForType(row.key)"
                      :key="field"
                      :label="field"
                      :value="field"
                    />
                  </el-select>
                  <div
                    v-if="row.defaultUniqueFields?.length"
                    class="asset-unique-hint"
                  >
                    默认：{{ row.defaultUniqueFields.join(' / ') }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column
                label="管理字段"
                min-width="220"
              >
                <template #default="{ row }">
                  <el-button
                    class="oa-table-action oa-table-action--primary"
                    size="small"
                    text
                    type="primary"
                    @click="openExtraFieldDialog(row.key, row.label, row.extraFields)"
                  >
                    编辑
                  </el-button>
                  <span
                    v-if="row.extraFields?.length"
                    class="asset-extra-hint"
                  >
                    {{ row.extraFields.length }} 个
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <el-dialog
          v-model="extraFieldDialogVisible"
          class="asset-field-dialog"
          :title="`字段管理 · ${currentExtraTypeLabel || currentExtraTypeKey}`"
          width="760px"
        >
          <el-alert
            type="info"
            show-icon
            :closable="false"
            class="asset-extra-alert"
          >
            左侧为内置字段，仅展示；右侧为可自定义的管理字段，写入资产 metadata，用于补充环境、业务线等信息。
          </el-alert>
          <div class="asset-field-layout">
            <div class="asset-field-layout__builtin">
              <h4 class="asset-field-title">
                内置字段（只读）
              </h4>
              <el-table
                :data="builtinFieldRows"
                border
                class="oa-table asset-builtin-table"
              >
                <el-table-column
                  prop="key"
                  label="字段 Key"
                  min-width="160"
                />
                <el-table-column
                  prop="description"
                  label="说明"
                  min-width="200"
                />
              </el-table>
            </div>
            <div class="asset-field-layout__extra">
              <h4 class="asset-field-title">
                管理字段
              </h4>
              <el-table
                :data="extraFieldDrafts"
                border
                class="oa-table asset-extra-table"
              >
                <el-table-column
                  label="字段 Key"
                  min-width="140"
                >
                  <template #default="{ row }">
                    <el-input
                      v-model="row.key"
                      size="small"
                      placeholder="例如 env、biz_line"
                    />
                  </template>
                </el-table-column>
                <el-table-column
                  label="显示名称"
                  min-width="140"
                >
                  <template #default="{ row }">
                    <el-input
                      v-model="row.label"
                      size="small"
                      placeholder="例如 环境、业务线"
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
                  label="枚举选项"
                  min-width="200"
                >
                  <template #default="{ row }">
                    <el-input
                      v-model="row.optionsText"
                      size="small"
                      :disabled="row.type !== 'enum'"
                      placeholder="仅枚举：用逗号分隔，例如 prod,pre,test"
                    />
                  </template>
                </el-table-column>
                <el-table-column
                  label="必填"
                  width="80"
                  align="center"
                >
                  <template #default="{ row }">
                    <el-switch
                      v-model="row.required"
                      size="small"
                    />
                  </template>
                </el-table-column>
                <el-table-column
                  label="列表展示"
                  width="100"
                  align="center"
                >
                  <template #default="{ row }">
                    <el-switch
                      v-model="row.list_visible"
                      size="small"
                    />
                  </template>
                </el-table-column>
                <el-table-column
                  label="操作"
                  width="80"
                >
                  <template #default="{ $index }">
                    <el-button
                      class="oa-table-action oa-table-action--danger"
                      text
                      type="danger"
                      size="small"
                      @click="removeExtraField($index)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <div class="asset-extra-actions">
                <el-button
                  size="small"
                  type="primary"
                  plain
                  @click="addExtraField"
                >
                  新增字段
                </el-button>
              </div>
            </div>
          </div>

          <template #footer>
            <el-button @click="extraFieldDialogVisible = false">
              取消
            </el-button>
            <el-button
              type="primary"
              @click="saveExtraFields"
            >
              保存
            </el-button>
          </template>
        </el-dialog>
      </div>
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';

import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import type { AssetTypeSummary } from '@/features/assets/api/assetsApi';
import { fetchAssetTypes, updateAssetTypeSettings } from '@/features/assets/api/assetsApi';

type AssetExtraField = {
  key: string;
  label: string;
  type?: string;
  options?: string[];
  required?: boolean;
  list_visible?: boolean;
};

const assetTypes = ref<AssetTypeSummary[]>([]);
const assetTypesLoading = ref(false);

const extraFieldDialogVisible = ref(false);
const currentExtraTypeKey = ref('');
const currentExtraTypeLabel = ref('');
const extraFieldDrafts = ref<
  Array<{
    key: string;
    label: string;
    type: string;
    optionsText?: string;
    required?: boolean;
    list_visible?: boolean;
  }>
>([]);

const builtinFieldRows = computed(() => {
  if (!extraFieldDialogVisible.value || !currentExtraTypeKey.value) return [];
  const def = assetTypes.value.find((t) => t.key === currentExtraTypeKey.value);
  if (!def) return [];
  const fields = def.fields && def.fields.length ? def.fields : [];
  return fields.map((key) => ({
    key,
    description: ''
  }));
});

const assetTypeRows = computed(() => {
  return assetTypes.value.map((def) => ({
    key: def.key,
    label: def.label || def.key,
    uniqueFields: def.unique_fields || [],
    defaultUniqueFields: def.default_unique_fields || def.unique_fields || [],
    extraFields: (def.extra_fields || []) as AssetExtraField[]
  }));
});

const fieldOptionsForType = (typeKey: string): string[] => {
  const def = assetTypes.value.find((t) => t.key === typeKey);
  if (!def) return [];
  const source = def.fields && def.fields.length ? def.fields : def.unique_fields || [];
  const set = new Set<string>();
  (source || []).forEach((field) => {
    const value = String(field || '').trim();
    if (value) set.add(value);
  });
  return Array.from(set);
};

const handleAssetUniqueFieldsChange = async (typeKey: string, value: string[]) => {
  const cleaned = (value || []).map((v) => String(v).trim()).filter((v) => v.length > 0);
  if (!cleaned.length) {
    ElMessage.warning('至少需要一个唯一键字段');
    return;
  }
  try {
    const updated = await updateAssetTypeSettings(typeKey, { unique_fields: cleaned });
    assetTypes.value = assetTypes.value.map((item) => (item.key === typeKey ? updated : item));
    ElMessage.success('业务唯一字段已保存');
  } catch (err: any) {
    const message = err?.response?.data?.detail || err?.response?.data?.unique_fields?.[0] || '业务唯一字段保存失败，请稍后重试';
    ElMessage.error(message);
  }
};

const openExtraFieldDialog = (typeKey: string, label: string, extraFields: AssetExtraField[]) => {
  currentExtraTypeKey.value = typeKey;
  currentExtraTypeLabel.value = label;
  extraFieldDrafts.value = (extraFields || []).map((field) => ({
    key: field.key,
    label: field.label,
    type: field.type || 'string',
    optionsText: (field.options || []).join(','),
    required: field.required,
    list_visible: field.list_visible
  }));
  if (!extraFieldDrafts.value.length) {
    extraFieldDrafts.value.push({
      key: '',
      label: '',
      type: 'string'
    });
  }
  extraFieldDialogVisible.value = true;
};

const addExtraField = () => {
  extraFieldDrafts.value.push({
    key: '',
    label: '',
    type: 'string'
  });
};

const removeExtraField = (index: number) => {
  extraFieldDrafts.value.splice(index, 1);
};

const saveExtraFields = async () => {
  const typeKey = currentExtraTypeKey.value;
  if (!typeKey) return;

  const cleaned = extraFieldDrafts.value
    .map((field) => ({
      key: String(field.key || '').trim(),
      label: String(field.label || '').trim(),
      type: String(field.type || 'string').trim() || 'string',
      options: String(field.optionsText || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
      required: Boolean(field.required),
      list_visible: Boolean(field.list_visible)
    }))
    .filter((field) => field.key || field.label);

  const invalid = cleaned.find((field) => !field.key || !field.label || (field.type === 'enum' && !field.options.length));
  if (invalid) {
    ElMessage.warning('请补全管理字段信息；枚举字段必须填写选项');
    return;
  }

  try {
    const updated = await updateAssetTypeSettings(typeKey, {
      extra_fields: cleaned
    });
    assetTypes.value = assetTypes.value.map((item) => (item.key === typeKey ? updated : item));
    extraFieldDialogVisible.value = false;
    ElMessage.success('管理字段已保存');
  } catch (err: any) {
    const message = err?.response?.data?.detail || err?.response?.data?.extra_fields?.[0] || '管理字段保存失败，请稍后重试';
    ElMessage.error(message);
  }
};

const loadAssetTypes = async () => {
  assetTypesLoading.value = true;
  try {
    const data = await fetchAssetTypes();
    assetTypes.value = data || [];
  } catch (err) {
    ElMessage.error('加载资产类型失败，请稍后重试');
  } finally {
    assetTypesLoading.value = false;
  }
};

loadAssetTypes();
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

.asset-field-dialog :deep(.el-dialog__title) {
  font-size: var(--oa-font-heading);
  font-weight: 600;
  color: var(--oa-text-primary);
}

.asset-field-dialog :deep(.el-alert__title) {
  font-size: var(--oa-font-subtitle);
}

.asset-field-dialog :deep(.el-input__inner),
.asset-field-dialog :deep(.el-textarea__inner),
.asset-field-dialog :deep(.el-select__wrapper) {
  font-size: var(--oa-font-base);
}

.asset-table__card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.asset-field-dialog :deep(.el-alert__description) {
  font-size: var(--oa-font-subtitle);
  line-height: 1.6;
}

.asset-field-dialog :deep(.el-table .cell) {
  font-size: var(--oa-font-base);
}

.asset-field-dialog :deep(.el-button--small) {
  font-size: var(--oa-font-base);
}

.asset-field-dialog :deep(.el-select__placeholder),
.asset-field-dialog :deep(.el-input__placeholder),
.asset-field-dialog :deep(.el-textarea__inner::placeholder) {
  font-size: var(--oa-font-base);
}

.asset-settings-loading {
  padding-top: 4px;
}

.asset-settings-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.asset-settings-alert {
  margin-bottom: 8px;
}

.asset-types-el-table {
  width: 100%;
}

.asset-unique-select {
  width: 100%;
}

.asset-unique-hint {
  margin-top: 4px;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-muted);
}

.asset-extra-hint {
  margin-left: 4px;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-muted);
}

.asset-extra-alert {
  margin-bottom: 8px;
}

.asset-field-layout {
  margin-top: 12px;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.9fr);
  gap: 12px;
}

.asset-field-layout__builtin,
.asset-field-layout__extra {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.asset-field-title {
  margin: 0;
  font-size: var(--oa-font-subtitle);
  font-weight: 600;
  color: var(--oa-text-secondary);
}
</style>
