<template>
  <div class="detail-card">
    <div class="detail-card__header">
      <h4>基本信息</h4>
    </div>
    <el-form
      :ref="formRef"
      :model="model"
      :rules="rules"
      label-width="80px"
      class="detail-form"
    >
      <el-form-item
        label="名称"
        prop="name"
      >
        <el-input
          v-model="model.name"
          placeholder="脚本名称或业务标识"
        />
      </el-form-item>
      <el-form-item
        label="语言"
        prop="language"
      >
        <el-select
          v-model="model.language"
          placeholder="选择语言"
        >
          <el-option
            v-for="option in languageOptions"
            :key="option"
            :label="option"
            :value="option"
          />
        </el-select>
      </el-form-item>
      <el-form-item
        label="目录"
        prop="directory"
      >
        <el-select
          v-model="model.directory"
          placeholder="选择目录"
        >
          <el-option
            v-for="dir in directoryOptions"
            :key="dir.key"
            :label="dir.title"
            :value="dir.key"
          />
        </el-select>
      </el-form-item>
      <el-form-item
        label="标签"
        prop="tags"
      >
        <el-select
          v-model="model.tags"
          multiple
          allow-create
          filterable
          placeholder="添加标签用于目录分类"
        />
      </el-form-item>
      <el-form-item label="描述">
        <el-input
          v-model="model.description"
          type="textarea"
          :rows="3"
          placeholder="描述脚本用途、依赖和注意事项"
        />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';

import type { CreateRepositoryPayload } from '@/features/tools/api/codeRepositoryApi';

type DirectoryOption = {
  key: string;
  title: string;
};

defineProps<{
  rules: FormRules<CreateRepositoryPayload>;
  directoryOptions: DirectoryOption[];
  languageOptions: string[];
}>();

const model = defineModel<CreateRepositoryPayload>({ required: true });
const formRef = ref<FormInstance>();

defineExpose({
  formRef,
});
</script>

<style scoped>
.detail-card {
  background: var(--oa-bg-panel);
  border: 1px solid var(--oa-border-color);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.detail-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.detail-form :deep(.el-input__wrapper),
.detail-form :deep(.el-textarea__inner),
.detail-form :deep(.el-select__wrapper) {
  width: 100%;
}
</style>
