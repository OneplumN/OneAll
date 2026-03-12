<template>
  <div class="tool-library page-container">
    <header class="page-header">
      <div>
        <h1>{{ t('tools.libraryTitle') }}</h1>
        <p class="subtitle">{{ t('tools.librarySubtitle') }}</p>
      </div>
      <el-space>
        <el-button text :loading="loading.table" @click="loadTools">{{ t('common.refresh') }}</el-button>
        <el-button type="primary" :disabled="!canCreate" @click="openCreateDialog">{{ t('tools.createTool') }}</el-button>
      </el-space>
    </header>

    <el-card class="section-card">
      <template #header>
        <el-space wrap>
          <el-input
            v-model="filters.keyword"
            placeholder="搜索名称或描述"
            clearable
            @clear="loadTools"
            @keyup.enter="loadTools"
            style="width: 220px"
          >
            <template #suffix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-select v-model="filters.category" placeholder="全部类别" clearable style="width: 180px">
            <el-option label="全部类别" value="" />
            <el-option
              v-for="category in categoryOptions"
              :key="category"
              :label="category"
              :value="category"
            />
          </el-select>

          <el-select
            v-model="filters.tag"
            placeholder="筛选标签"
            clearable
            filterable
            style="width: 200px"
          >
            <el-option
              v-for="tag in tagOptions"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-space>
      </template>

      <el-table :data="filteredTools" stripe v-loading="loading.table" style="width: 100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="tool-description">
              <p class="tool-description__title">描述</p>
              <p>{{ row.description || '暂无描述' }}</p>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="200">
          <template #default="{ row }">
            <div class="tool-name">
              <strong>{{ row.name }}</strong>
              <span class="muted">版本：{{ row.connector_version || '未标记' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="类别" width="140" />
        <el-table-column prop="tags" label="标签" min-width="220">
          <template #default="{ row }">
            <el-space>
              <el-tag
                v-for="tag in row.tags"
                :key="tag"
                round
                size="small"
              >
                {{ tag }}
              </el-tag>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column label="最近更新" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link :disabled="!canManage" @click="handleExecute(row)">{{ t('tools.execute') }}</el-button>
            <el-button type="info" link @click="openDetails(row)">{{ t('tools.viewDetails') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="createDialogVisible" :title="t('tools.dialogTitle')" width="520px">
      <el-form :model="createForm" label-position="top" :rules="createRules" ref="createFormRef">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="工具名称" />
        </el-form-item>
        <el-form-item label="类别" prop="category">
          <el-input v-model="createForm.category" placeholder="所属类别，例如 脚本 / 数据采集" />
        </el-form-item>
        <el-form-item label="标签" prop="tags">
          <el-select
            v-model="createForm.tags"
            multiple
            allow-create
            filterable
            placeholder="添加标签"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="说明工具用途、注意事项等"
          />
        </el-form-item>
        <el-form-item label="关联脚本 ID">
          <el-input v-model="createForm.script_id" placeholder="可选：关联脚本仓库 ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="loading.creating" @click="submitCreate">
          {{ t('common.save') }}
        </el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailsDrawerVisible" :title="selectedTool?.name" size="40%">
      <div v-if="selectedTool" class="drawer-section">
        <p class="muted">类别：{{ selectedTool.category }}</p>
        <p class="muted">版本：{{ selectedTool.connector_version || '未标记' }}</p>
        <p class="muted">标签：
          <el-tag
            v-for="tag in selectedTool.tags"
            :key="tag"
            round
            size="small"
          >
            {{ tag }}
          </el-tag>
        </p>
        <p>{{ selectedTool.description || '暂无描述' }}</p>
      </div>
      <el-divider />
      <div class="drawer-section">
        <h4>执行记录</h4>
        <el-empty description="后端暂未接入执行历史" />
      </div>
    </el-drawer>

    <el-drawer v-model="executionDrawerVisible" :title="`执行结果 - ${executingTool?.name || ''}`" size="40%">
      <el-skeleton v-if="loading.executing" :rows="5" animated />
      <div v-else-if="executionResult" class="drawer-section">
        <p class="muted">运行 ID：{{ executionResult.run_id }}</p>
        <p class="muted">状态：{{ executionResult.status }}</p>
        <p class="muted">开始时间：{{ formatTime(executionResult.started_at) }}</p>
        <p class="muted">结束时间：{{ formatTime(executionResult.finished_at) }}</p>
        <el-input
          v-if="executionResult.output"
          v-model="executionResult.output"
          type="textarea"
          :rows="8"
          readonly
        />
        <el-empty v-else description="执行成功，但未返回输出" />
      </div>
      <el-empty v-else description="尚未触发执行" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { ElMessage, FormInstance, FormRules } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { Search } from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n';

import {
  createTool,
  executeTool,
  listTools,
  type CreateToolPayload,
  type ToolDefinition,
  type ToolExecutionResult
} from '@/services/toolsApi';
import { usePageTitle } from '@/composables/usePageTitle';
import { useSessionStore } from '@/stores/session';

const sessionStore = useSessionStore();
const canCreate = computed(() => sessionStore.hasPermission('tools.library.create'));
const canManage = computed(() => sessionStore.hasPermission('tools.library.manage'));

const tools = ref<ToolDefinition[]>([]);
const loading = reactive({
  table: false,
  creating: false,
  executing: false
});

const filters = reactive({
  keyword: '',
  category: '',
  tag: ''
});

const createDialogVisible = ref(false);
const detailsDrawerVisible = ref(false);
const executionDrawerVisible = ref(false);
const selectedTool = ref<ToolDefinition | null>(null);
const executingTool = ref<ToolDefinition | null>(null);
const executionResult = ref<ToolExecutionResult | null>(null);

const createForm = reactive<CreateToolPayload>({
  name: '',
  category: '',
  tags: [],
  description: '',
  script_id: ''
});

const createFormRef = ref<FormInstance>();

const createRules: FormRules<CreateToolPayload> = {
  name: [{ required: true, message: '请输入工具名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择类别', trigger: 'blur' }],
  tags: [
    {
      type: 'array',
      required: true,
      message: '至少添加一个标签',
      trigger: 'change'
    }
  ]
};

const categoryOptions = computed(() => {
  const items = new Set<string>();
  tools.value.forEach((tool) => {
    if (tool.category) items.add(tool.category);
  });
  return Array.from(items);
});

const tagOptions = computed(() => {
  const items = new Set<string>();
  tools.value.forEach((tool) => {
    tool.tags?.forEach((tag) => items.add(tag));
  });
  return Array.from(items);
});

const filteredTools = computed(() => {
  return tools.value.filter((tool) => {
    const matchKeyword =
      !filters.keyword ||
      tool.name.toLowerCase().includes(filters.keyword.toLowerCase()) ||
      (tool.description || '').toLowerCase().includes(filters.keyword.toLowerCase());

    const matchCategory = !filters.category || tool.category === filters.category;
    const matchTag = !filters.tag || tool.tags?.includes(filters.tag);

    return matchKeyword && matchCategory && matchTag;
  });
});

const { t } = useI18n();
usePageTitle('tools.libraryTitle');

const loadTools = async () => {
  loading.table = true;
  try {
    tools.value = await listTools();
  } catch (error) {
    console.warn('Failed to load tools.', error);
    ElMessage.error('加载工具列表失败，请稍后重试');
  } finally {
    loading.table = false;
  }
};

const openCreateDialog = () => {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  createDialogVisible.value = true;
};

const resetCreateForm = () => {
  createForm.name = '';
  createForm.category = '';
  createForm.tags = [];
  createForm.description = '';
  createForm.script_id = '';
};

const submitCreate = async () => {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  if (!createFormRef.value) return;
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.creating = true;
    try {
      const tool = await createTool(createForm);
      tools.value = [tool, ...tools.value];
      ElMessage.success(t('tools.toolCreated'));
      createDialogVisible.value = false;
      resetCreateForm();
    } catch (error) {
      console.warn('Failed to create tool.', error);
      ElMessage.error('创建失败，请检查信息或稍后重试');
    } finally {
      loading.creating = false;
    }
  });
};

const openDetails = (tool: ToolDefinition) => {
  selectedTool.value = tool;
  detailsDrawerVisible.value = true;
};

const handleExecute = async (tool: ToolDefinition) => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  executingTool.value = tool;
  executionDrawerVisible.value = true;
  loading.executing = true;
  executionResult.value = null;
  try {
    const result = await executeTool(tool.id, {});
    executionResult.value = result;
    ElMessage.success(t('tools.toolExecuteTriggered'));
  } catch (error) {
    console.warn('Failed to execute tool.', error);
    ElMessage.error('触发执行失败，请稍后重试');
  } finally {
    loading.executing = false;
  }
};

const formatTime = (value?: string) => {
  if (!value) return '未记录';
  return dayjs(value).format('YYYY-MM-DD HH:mm');
};

onMounted(() => {
  loadTools();
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.subtitle {
  margin-top: 0.25rem;
  color: var(--oneall-text-secondary);
}

.tool-name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.muted {
  color: var(--oneall-text-secondary);
  font-size: 0.85rem;
}

.tool-description {
  padding: 1rem 2rem 1rem 3rem;
  line-height: 1.6;
}

.tool-description__title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>
