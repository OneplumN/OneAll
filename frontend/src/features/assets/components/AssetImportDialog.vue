<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    width="640px"
    @close="emit('close')"
  >
    <div class="import-toolbar">
      <el-button
        size="small"
        @click="emit('downloadTemplate')"
      >
        下载模板
      </el-button>
      <label class="upload-input">
        <input
          type="file"
          :accept="accept"
          @change="emit('fileChange', $event)"
        >
        <span>{{ fileName || emptyLabel }}</span>
      </label>
    </div>

    <p
      v-if="previewRows.length"
      class="import-summary"
    >
      已解析 {{ previewRows.length }} 条记录，准备导入。
    </p>

    <el-table
      v-if="previewRows.length"
      :data="previewRows"
      height="260"
      class="oa-table import-preview"
    >
      <el-table-column
        v-for="column in columns"
        :key="column.key"
        :prop="column.key"
        :label="column.label"
      />
    </el-table>
    <el-empty
      v-else
      description="尚未选择文件"
    />

    <el-alert
      v-if="errors.length"
      type="warning"
      show-icon
      :closable="false"
      class="import-errors"
    >
      <ul>
        <li
          v-for="error in errors"
          :key="error"
        >
          {{ error }}
        </li>
      </ul>
    </el-alert>

    <template #footer>
      <el-button @click="visibleModel = false">
        取消
      </el-button>
      <el-button
        type="primary"
        :loading="loading"
        :disabled="disabled"
        @click="emit('submit')"
      >
        导入
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
type AssetImportColumn = {
  key: string;
  label: string;
};

const visibleModel = defineModel<boolean>('visible', { required: true });

withDefaults(
  defineProps<{
    title?: string;
    columns: AssetImportColumn[];
    previewRows: Record<string, any>[];
    errors: string[];
    fileName?: string;
    loading?: boolean;
    disabled?: boolean;
    accept?: string;
    emptyLabel?: string;
  }>(),
  {
    title: '批量导入',
    fileName: '',
    loading: false,
    disabled: false,
    accept: '.csv,.txt',
    emptyLabel: '选择 CSV 文件',
  }
);

const emit = defineEmits<{
  (event: 'close'): void;
  (event: 'downloadTemplate'): void;
  (event: 'fileChange', value: Event): void;
  (event: 'submit'): void;
}>();
</script>

<style scoped>
.import-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1rem 0;
}

.upload-input {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border: 1px dashed var(--oa-border-light);
  border-radius: 6px;
  color: var(--oa-color-primary);
  cursor: pointer;
}

.upload-input input {
  display: none;
}

.import-summary {
  margin: 8px 0;
  font-size: var(--oa-font-subtitle);
  color: var(--oa-text-secondary);
}

.import-errors {
  margin-top: 1rem;
}

.import-errors ul {
  margin: 0.5rem 0 0;
  padding-left: 1.2rem;
}
</style>
