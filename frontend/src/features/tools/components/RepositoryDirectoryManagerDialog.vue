<template>
  <el-dialog
    v-model="visibleModel"
    title="管理目录"
    width="720px"
    class="dialog-shell"
    destroy-on-close
  >
    <el-form
      :ref="formRef"
      :model="formModel"
      label-width="100px"
      :rules="formRules"
    >
      <el-form-item
        label="目录名称"
        prop="title"
      >
        <el-input
          v-model="formModel.title"
          placeholder="请输入目录名称"
        />
      </el-form-item>
      <el-form-item label="关键词">
        <el-input
          v-model="formModel.keywordsInput"
          placeholder="用逗号分隔的关键词，例如: 资产, CMDB"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="directory-manager__actions">
        <div class="left-actions">
          <el-button @click="emit('reset')">
            重置
          </el-button>
        </div>
        <div class="right-actions">
          <el-button @click="visibleModel = false">
            取消
          </el-button>
          <el-button
            type="primary"
            :loading="directoryManaging"
            @click="emit('save')"
          >
            {{ editingDirectoryKey ? '保存修改' : '新增目录' }}
          </el-button>
        </div>
      </div>
    </template>
    <el-table
      :data="availableDirectories"
      class="oa-table"
      style="margin-top: 12px"
    >
      <el-table-column
        prop="title"
        label="名称"
        min-width="160"
      />
      <el-table-column
        label="关键词"
        min-width="200"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <el-space wrap>
            <el-tag
              v-for="kw in row.keywords"
              :key="kw"
              size="small"
            >
              {{ kw }}
            </el-tag>
          </el-space>
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        width="160"
      >
        <template #default="{ row }">
          <el-space size="small">
            <el-button
              text
              size="small"
              :disabled="!canManage"
              @click="emit('edit', row)"
            >
              编辑
            </el-button>
            <el-button
              text
              type="danger"
              size="small"
              :disabled="!canManage || row.builtin"
              @click="emit('delete', row)"
            >
              删除
            </el-button>
          </el-space>
        </template>
      </el-table-column>
    </el-table>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';

import type { DirectoryPreset } from '@/features/tools/stores/codeDirectories';

defineProps<{
  formRules: FormRules;
  directoryManaging: boolean;
  editingDirectoryKey: string | null;
  availableDirectories: DirectoryPreset[];
  canManage: boolean;
}>();

const emit = defineEmits<{
  (event: 'edit', directory: DirectoryPreset): void;
  (event: 'delete', directory: DirectoryPreset): void;
  (event: 'reset'): void;
  (event: 'save'): void;
}>();

const visibleModel = defineModel<boolean>('visible', { required: true });
const formModel = defineModel<{ title: string; keywordsInput: string }>('form', { required: true });
const formRef = ref<FormInstance>();

defineExpose({
  formRef,
});
</script>

<style scoped>
.directory-manager__actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dialog-shell :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.15);
}

.dialog-shell :deep(.el-dialog__body) {
  background: var(--oa-bg-muted);
  padding: 1.2rem 1.5rem;
}

.dialog-shell :deep(.el-dialog__header) {
  padding: 1.2rem 1.5rem 0.5rem;
  border-bottom: 1px solid var(--oa-border-light);
  margin-right: 0;
}

.dialog-shell :deep(.el-dialog__footer) {
  border-top: 1px solid var(--oa-border-light);
  padding: 0.75rem 1.5rem;
}
</style>
