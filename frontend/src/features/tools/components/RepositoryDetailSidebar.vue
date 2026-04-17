<template>
  <div class="detail-sidebar">
    <div class="detail-card">
      <div class="detail-card__header">
        <h4>基本信息</h4>
      </div>
      <el-form
        label-width="80px"
        class="detail-form"
      >
        <el-form-item label="名称">
          <el-input
            v-model="repository.name"
            @change="emit('dirty')"
          />
        </el-form-item>
        <el-form-item label="语言">
          <el-select
            v-model="repository.language"
            @change="emit('dirty')"
          >
            <el-option
              v-for="option in languageOptions"
              :key="option"
              :label="option"
              :value="option"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目录">
          <el-select
            v-model="repository.directory"
            @change="emit('dirty')"
          >
            <el-option
              v-for="dir in directoryOptions"
              :key="dir.key"
              :label="dir.title"
              :value="dir.key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="repository.tags"
            multiple
            allow-create
            filterable
            @change="emit('dirty')"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="repository.description"
            type="textarea"
            :rows="3"
            @change="emit('dirty')"
          />
        </el-form-item>
      </el-form>
    </div>

    <div class="detail-card">
      <div class="detail-card__header">
        <h4>当前版本</h4>
      </div>
      <div class="version-summary">
        <el-tag
          v-if="repository.latest_version"
          type="info"
          size="small"
        >
          当前：{{ repository.latest_version }}
        </el-tag>
        <p
          v-else
          class="oa-table-meta"
        >
          暂未生成版本号
        </p>
      </div>
    </div>

    <div class="detail-card danger">
      <div class="detail-card__header">
        <h4>危险操作</h4>
      </div>
      <el-button
        type="danger"
        plain
        :disabled="!canManage"
        @click="emit('delete')"
      >
        删除脚本
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ScriptRepository } from '@/features/tools/api/codeRepositoryApi';

type DirectoryOption = {
  key: string;
  title: string;
};

defineProps<{
  directoryOptions: DirectoryOption[];
  languageOptions: string[];
  canManage: boolean;
}>();

const emit = defineEmits<{
  (event: 'dirty'): void;
  (event: 'delete'): void;
}>();

const repository = defineModel<ScriptRepository>('repository', { required: true });
</script>

<style scoped>
.detail-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-card {
  background: var(--oa-bg-panel);
  border: 1px solid var(--oa-border-color);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.detail-card.danger {
  border-color: rgba(220, 38, 38, 0.25);
  background: rgba(220, 38, 38, 0.06);
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

.version-summary {
  display: flex;
  align-items: center;
  min-height: 40px;
}
</style>
