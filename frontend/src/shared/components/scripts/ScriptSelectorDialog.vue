<template>
  <el-dialog
    v-model="visible"
    title="选择脚本"
    width="760px"
    class="script-dialog"
    :close-on-click-modal="false"
  >
    <div class="script-selector">
      <div class="page-toolbar script-selector__toolbar">
        <div class="page-toolbar__left">
          <el-select
            v-model="directoryFilter"
            placeholder="全部目录"
            clearable
            class="pill-input narrow-select"
          >
            <el-option
              v-for="directory in directories"
              :key="directory.key"
              :label="directory.title"
              :value="directory.key"
            />
          </el-select>
        </div>
        <div class="page-toolbar__right">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索脚本名称、标签"
            clearable
            class="search-input pill-input search-input--compact"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <div
            class="refresh-card"
            @click="fetchData(true)"
          >
            <el-icon
              class="refresh-icon"
              :class="{ spinning: loading }"
            >
              <Refresh />
            </el-icon>
            <span>{{ loading ? '刷新中' : '刷新' }}</span>
          </div>
        </div>
      </div>

      <div class="script-selector__summary">
        共 {{ filteredRepositories.length }} 条脚本
      </div>

      <el-table
        v-loading="loading"
        :data="filteredRepositories"
        class="oa-table script-table"
        empty-text="暂无脚本，可前往脚本仓库新增"
        height="420"
      >
        <el-table-column
          prop="name"
          label="名称"
          min-width="180"
        >
          <template #default="{ row }">
            <div class="script-name">
              <strong>{{ row.name }}</strong>
              <span class="script-lang">{{ row.language }}</span>
            </div>
            <div
              v-if="row.tags?.length"
              class="script-tags"
            >
              <el-tag
                v-for="tag in row.tags"
                :key="tag"
                size="small"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          prop="directory"
          label="目录"
          width="160"
        >
          <template #default="{ row }">
            {{ directoryMap[row.directory || ''] || row.directory || '未分组' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="latest_version"
          label="最新版本"
          width="120"
        >
          <template #default="{ row }">
            {{ row.latest_version || '未发布' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="updated_at"
          label="更新时间"
          width="180"
        >
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-button
              size="small"
              link
              :class="row.id === selectedId ? 'oa-table-action oa-table-action--success' : 'oa-table-action oa-table-action--primary'"
              :disabled="row.id === selectedId"
              @click="selectScript(row)"
            >
              {{ row.id === selectedId ? '已选择' : '选择' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Refresh, Search } from '@element-plus/icons-vue';

import {
  listCodeDirectories,
  listRepositories,
  type CodeDirectory,
  type ScriptRepository,
} from '@/features/tools/api/codeRepositoryApi';

interface Props {
  modelValue: boolean;
  selectedId?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void;
  (event: 'select', repository: ScriptRepository): void;
}>();

const visible = ref(props.modelValue);
const repositories = ref<ScriptRepository[]>([]);
const directories = ref<CodeDirectory[]>([]);
const loading = ref(false);
const initialized = ref(false);
const searchKeyword = ref('');
const directoryFilter = ref<string>();

const directoryMap = computed<Record<string, string>>(() =>
  directories.value.reduce((map, directory) => {
    map[directory.key] = directory.title;
    return map;
  }, {} as Record<string, string>)
);

watch(
  () => props.modelValue,
  (value) => {
    visible.value = value;
    if (value && !initialized.value) {
      fetchData();
    }
  }
);

watch(visible, (value) => {
  emit('update:modelValue', value);
});

const filteredRepositories = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  return repositories.value.filter((repo) => {
    if (directoryFilter.value && repo.directory !== directoryFilter.value) return false;
    if (!keyword) return true;
    return (
      repo.name.toLowerCase().includes(keyword) ||
      repo.tags?.some((tag) => tag.toLowerCase().includes(keyword))
    );
  });
});

const fetchData = async (force = false) => {
  if (loading.value) return;
  loading.value = true;
  try {
    if (force || directories.value.length === 0) {
      directories.value = await listCodeDirectories();
    }
    repositories.value = await listRepositories();
    initialized.value = true;
  } catch {
    ElMessage.error('加载脚本列表失败，请稍后再试');
  } finally {
    loading.value = false;
  }
};

const selectScript = (repository: ScriptRepository) => {
  emit('select', repository);
  visible.value = false;
};

const formatTime = (ts?: string) => {
  if (!ts) return '—';
  return new Date(ts).toLocaleString();
};

onMounted(() => {
  if (visible.value) {
    fetchData();
  }
});

const selectedId = computed(() => props.selectedId);
</script>

<style scoped>
.script-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.script-selector__toolbar {
  margin-bottom: 0;
  padding: 0;
}

.script-selector__summary {
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-subtitle);
}

.script-table {
  --el-table-border-color: #f1f3f9;
}

.script-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.script-lang {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.script-tags {
  margin-top: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
