<template>
  <PageWrapper :loading="loadingChecks">
    <RepositoryPageShell
      root-title="监控与告警"
      section-title="监控策略"
      body-padding="0"
      :panel-bordered="false"
    >
      <template #actions>
        <div class="alerts-header__right">
          <div
            class="refresh-card"
            @click="loadChecks"
          >
            <el-icon
              class="refresh-icon"
              :class="{ spinning: loadingChecks }"
            >
              <Refresh />
            </el-icon>
            <span>刷新</span>
          </div>
        </div>
      </template>

      <div class="oa-list-page">
        <div class="page-toolbar page-toolbar--panel">
          <div class="page-toolbar__left">
            <el-button
              class="toolbar-button toolbar-button--primary"
              type="primary"
              plain
              @click="handleCreate"
            >
              新建
            </el-button>
          </div>
          <div class="page-toolbar__right">
            <el-input
              v-model="keyword"
              placeholder="搜索名称 / 目标 / 协议"
              clearable
              class="search-input pill-input search-input--compact"
            />
          </div>
        </div>

        <el-alert
          v-if="error"
          type="error"
          :closable="false"
          class="oa-inline-alert"
          show-icon
        >
          {{ error }}
        </el-alert>

        <div class="oa-table-panel">
          <div class="oa-table-panel__card checks-panel">
            <el-table
              v-loading="loadingChecks"
              :data="filteredChecks"
              class="oa-table"
              height="100%"
              stripe
              empty-text="暂无监控策略"
              highlight-current-row
            >
              <el-table-column
                prop="name"
                label="策略名称"
                min-width="220"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <div class="title-cell">
                    <strong class="oa-table-title">{{ row.name }}</strong>
                  </div>
                </template>
              </el-table-column>

              <el-table-column
                prop="metadata"
                label="通知对象"
                min-width="200"
              >
                <template #default="{ row }">
                  <span class="oa-table-meta">{{ formatContacts(row) }}</span>
                </template>
              </el-table-column>

              <el-table-column
                prop="is_active"
                label="策略启停"
                width="120"
              >
                <template #default="{ row }">
                  <el-switch
                    :model-value="row.is_active"
                    size="small"
                    @click.stop
                    @change="(val: boolean) => handleToggleActive(row, val)"
                  />
                </template>
              </el-table-column>

              <el-table-column
                prop="created_at"
                label="创建时间"
                width="200"
              >
                <template #default="{ row }">
                  <span class="oa-table-meta">{{ formatDate(row.created_at) }}</span>
                </template>
              </el-table-column>

              <el-table-column
                prop="updated_at"
                label="更新时间"
                width="200"
              >
                <template #default="{ row }">
                  <span class="oa-table-meta">{{ formatDate(row.updated_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                label="操作"
                width="200"
                fixed="right"
              >
                <template #default="{ row }">
                  <el-space size="small">
                    <el-button
                      text
                      size="small"
                      class="oa-table-action oa-table-action--success"
                      @click.stop="handleEdit(row)"
                    >
                      编辑
                    </el-button>
                    <el-button
                      text
                      size="small"
                      class="oa-table-action oa-table-action--primary"
                      @click.stop="handleClone(row)"
                    >
                      克隆
                    </el-button>
                    <el-button
                      text
                      size="small"
                      class="oa-table-action oa-table-action--danger"
                      @click.stop="handleDelete(row)"
                    >
                      删除
                    </el-button>
                  </el-space>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </RepositoryPageShell>
  </PageWrapper>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';

import PageWrapper from '@/shared/components/layout/PageWrapper';
import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import type { AlertCheckSummary } from '@/features/alerts/api/alertsApi';
import {
  deleteAlertCheck,
  fetchAlertChecks,
  updateAlertCheck,
} from '@/features/alerts/api/alertsApi';

const router = useRouter();

const loadingChecks = ref(false);
const error = ref<string | null>(null);

const checks = ref<AlertCheckSummary[]>([]);

const keyword = ref('');

const loadChecks = async () => {
  loadingChecks.value = true;
  error.value = null;
  try {
    checks.value = await fetchAlertChecks();
  } catch (err) {
    error.value = '无法加载监控策略列表，请稍后重试。';
  } finally {
    loadingChecks.value = false;
  }
};

const filteredChecks = computed(() => {
  const k = keyword.value.trim().toLowerCase();
  return checks.value.filter((check) => {
    if (!k) return true;
    const meta = (check as any).metadata || {};
    const contacts: string[] = meta.alert_contacts || [];
    const haystack = `${check.name} ${contacts.join(',')}`.toLowerCase();
    return haystack.includes(k);
  });
});

const formatDate = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

const formatContacts = (check: AlertCheckSummary) => {
  const meta = (check as any).metadata || {};
  const contacts: string[] = meta.alert_contacts || [];
  if (!contacts.length) return '未配置';
  if (contacts.length === 1) return contacts[0];
  if (contacts.length === 2) return `${contacts[0]}、${contacts[1]}`;
  return `${contacts[0]} 等 ${contacts.length} 人`;
};

onMounted(async () => {
  await loadChecks();
});

const handleToggleActive = async (row: AlertCheckSummary, next: boolean) => {
  try {
    const updated = await updateAlertCheck(row.id, { is_active: next });
    // 更新本地行数据
    row.is_active = updated.is_active;
    row.updated_at = updated.updated_at;
    ElMessage.success(`策略「${row.name}」已${next ? '启用' : '停用'}`);
  } catch (err) {
    ElMessage.error('更新策略启停状态失败，请稍后重试');
  }
};

const handleCreate = () => {
  router.push({ name: 'alerts-check-detail', params: { checkId: 'new' } });
};

const handleEdit = (row: AlertCheckSummary) => {
  router.push({ name: 'alerts-check-detail', params: { checkId: row.id } });
};

const handleClone = (row: AlertCheckSummary) => {
  router.push({
    name: 'alerts-check-detail',
    params: { checkId: 'new' },
    query: { cloneFrom: row.id },
  });
};

const handleDelete = async (row: AlertCheckSummary) => {
  if (row.source_type !== 'probe_schedule' || !row.source_id) {
    ElMessage.warning('该策略来自监控申请，当前不支持直接删除，请先回到对应来源停用或归档。');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确认删除策略「${row.name}」吗？删除后将一并移除对应的手工调度配置。`,
      '删除策略',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      },
    );
  } catch {
    return;
  }

  try {
    await deleteAlertCheck(row.id);
    checks.value = checks.value.filter((item) => item.id !== row.id);
    ElMessage.success(`策略「${row.name}」已删除`);
  } catch {
    ElMessage.error('删除策略失败，请稍后重试。');
  }
};
</script>

<style scoped>
.alerts-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.panel-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: var(--oa-font-base);
  font-weight: 600;
  margin: 12px 12px 8px;
}

.panel-subtitle {
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.title-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
