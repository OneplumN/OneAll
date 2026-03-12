<template>
  <div class="probe-schedules">
    <header class="page-header">
      <div class="page-title">
        <span class="header__title">探针调度</span>
      </div>
      <div class="header-actions">
        <div class="refresh-card" @click="loadSchedules">
          <el-icon class="refresh-icon" :class="{ spinning: loading }"><Refresh /></el-icon>
          <span>刷新</span>
        </div>
      </div>
    </header>

    <div class="page-body">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" :disabled="loading" @click="openCreateDialog">新建调度</el-button>
        </div>
        <div class="toolbar-right">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索名称 / 目标"
            clearable
            class="search-input pill-input search-input--compact"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <div class="table-section">
        <div class="table-wrapper">
          <el-card shadow="never" class="table-card" :body-style="{ padding: '0', height: '100%' }">
            <el-table
              :data="pagedSchedules"
              v-loading="loading"
              stripe
              class="schedule-table"
              empty-text="暂无调度计划"
              :header-cell-style="tableHeaderStyle"
              :cell-style="tableCellStyle"
              height="100%"
            >
              <el-table-column prop="name" label="策略名称" min-width="240" show-overflow-tooltip>
                <template #default="{ row }">
                  <div class="schedule-name">
                    <span class="schedule-name__link" @click="openDetail(row)">{{ row.name }}</span>
                    <small v-if="row.description" class="description">{{ row.description }}</small>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="120" align="center">
                <template #default="{ row }">
                  <el-tag :type="statusTag(row.status)" effect="plain" size="small">{{ row.status_display }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="启停" width="100" align="center">
                <template #default="{ row }">
                  <el-switch
                    :model-value="row.status === 'active'"
                    :disabled="loading || togglingId === row.id"
                    active-text=""
                    inactive-text=""
                    @change="toggleSchedule(row, $event)"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="target" label="目标" min-width="220" />
              <el-table-column label="频率" width="120" align="center">
                <template #default="{ row }">{{ row.frequency_minutes }} 分钟</template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right" align="center">
                <template #default="{ row }">
                  <el-button text type="primary" size="small" @click="editSchedule(row)">编辑</el-button>
                  <el-button
                    v-if="row.source_type === 'manual'"
                    text
                    type="danger"
                    size="small"
                    @click="removeSchedule(row)"
                  >删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>

        <div v-if="loading" class="table-skeleton">
          <el-skeleton v-for="n in 5" :key="n" animated :rows="3" />
        </div>

        <el-empty v-if="!loading && !schedules.length" description="暂无调度计划" class="mt-3" />
      </div>
    </div>

    <div class="page-footer" v-if="!loading">
      <div class="footer-left">
        <div class="table-total">共 {{ filteredTotal }} 条</div>
        <el-pagination
          class="pager-sizes"
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredTotal"
          :page-sizes="[10, 20, 50]"
          layout="sizes"
          background
        />
      </div>
      <div class="footer-right">
        <el-pagination
          class="pager-main"
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="filteredTotal"
          layout="prev, pager, next"
          background
        />
      </div>
    </div>

    <el-dialog v-model="editor.visible" :title="editor.isEdit ? '编辑调度' : '新建调度'" width="560px">
      <el-form label-width="100px" :model="editor.form" class="schedule-form">
        <el-form-item label="名称" required>
          <el-input v-model="editor.form.name" placeholder="请输入调度名称" />
        </el-form-item>
        <el-form-item label="目标" required>
          <el-input v-model="editor.form.target" placeholder="例如：https://example.com" />
        </el-form-item>
        <el-form-item label="协议">
          <el-select v-model="editor.form.protocol">
            <el-option label="HTTP" value="HTTP" />
            <el-option label="HTTPS" value="HTTPS" />
            <el-option label="Telnet" value="Telnet" />
            <el-option label="WSS" value="WSS" />
            <el-option label="CERTIFICATE" value="CERTIFICATE" />
          </el-select>
        </el-form-item>
        <el-form-item label="频率 (分钟)">
          <el-input-number v-model="editor.form.frequency_minutes" :min="1" />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="editor.form.start_at"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            placeholder="默认立即生效"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="editor.form.end_at"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            placeholder="可选"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="调度探针" required>
          <div class="probe-selector">
            <el-skeleton v-if="probesLoading" :rows="2" animated style="width: 100%" />
            <template v-else>
              <el-alert
                v-if="!probeOptions.length"
                type="warning"
                show-icon
                :closable="false"
                title="暂无可用探针，请先在“探针节点”页创建"
              />
              <el-select
                v-else
                v-model="editor.form.probe_ids"
                multiple
                filterable
                placeholder="选择探针"
                style="width: 100%"
              >
                <el-option
                  v-for="probe in probeOptions"
                  :key="probe.id"
                  :label="`${probe.name} (${probe.location})`"
                  :value="probe.id"
                />
              </el-select>
            </template>
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editor.form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-divider>执行参数</el-divider>
        <el-form-item label="请求超时 (秒)">
          <el-input-number v-model="editor.form.timeout_seconds" :min="1" :max="600" />
        </el-form-item>
        <el-form-item label="期望状态码">
          <el-input
            v-model="expectedStatusInput"
            placeholder="例如 200,204"
            clearable
            @blur="expectedStatusInput = expectedStatusCodes.join(', ')"
          />
          <div class="status-tag-list" v-if="expectedStatusCodes.length">
            <el-tag v-for="code in expectedStatusCodes" :key="code" round size="small">
              {{ code }}
            </el-tag>
          </div>
        </el-form-item>
        <el-divider>告警策略</el-divider>
        <el-form-item label="告警阈值">
          <el-input-number v-model="editor.form.alert_threshold" :min="1" :max="10" />
          <span class="hint-text">连续失败次数触发</span>
        </el-form-item>
        <el-form-item label="告警联系人">
          <el-input
            v-model="alertContactsText"
            placeholder="工号或邮箱，逗号分隔"
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editor.visible = false">取消</el-button>
        <el-button type="primary" :loading="editor.submitting" @click="submitSchedule">
          {{ editor.isEdit ? '保存修改' : '创建调度' }}
        </el-button>
      </template>
    </el-dialog>
    <StrategyDetailDrawer v-model="detailVisible" :policy="currentSchedule" />
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { ElMessage, ElMessageBox } from 'element-plus';
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { Refresh, DataBoard, CircleCheck, Tools, WarningFilled } from '@element-plus/icons-vue';

import apiClient from '@/services/apiClient';
import {
  archiveProbeSchedule,
  createProbeSchedule,
  deleteProbeSchedule,
  listProbeSchedules,
  pauseProbeSchedule,
  resumeProbeSchedule,
  updateProbeSchedule,
  type CreateProbeSchedulePayload,
  type ProbeScheduleRecord
} from '@/services/probeScheduleApi';
import StrategyDetailDrawer from './components/StrategyDetailDrawer.vue';

interface ProbeNodeSummary {
  id: string;
  name: string;
  location: string;
  network_type: string;
  status: string;
}

const schedules = ref<ProbeScheduleRecord[]>([]);
const loading = ref(false);
const togglingId = ref<string | null>(null);
const searchKeyword = ref('');
const probeOptions = ref<ProbeNodeSummary[]>([]);
const probesLoading = ref(false);

const editor = reactive({
  visible: false,
  isEdit: false,
  submitting: false,
  form: {
    id: '' as string | null,
    name: '',
    target: '',
    protocol: 'HTTPS',
    frequency_minutes: 5,
    probe_ids: [] as string[],
    description: '',
    start_at: '' as string | null,
    end_at: '' as string | null,
    timeout_seconds: 30,
    expected_status_codes: [200] as number[],
    alert_threshold: 1,
    alert_contacts: [] as string[]
  }
});

const detailVisible = ref(false);
const currentSchedule = ref<ProbeScheduleRecord | null>(null);

const expectedStatusInput = ref('200');
const expectedStatusCodes = computed(() => parseStatusCodes(expectedStatusInput.value));
const alertContactsText = ref('');

const displayedSchedules = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return schedules.value;
  return schedules.value.filter((item) => {
    const nameMatch = item.name.toLowerCase().includes(keyword);
    const targetMatch = (item.target || '').toLowerCase().includes(keyword);
    return nameMatch || targetMatch;
  });
});

const filteredTotal = computed(() => displayedSchedules.value.length);
const currentPage = ref(1);
const pageSize = ref(10);

const pagedSchedules = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return displayedSchedules.value.slice(start, start + pageSize.value);
});

const tableHeaderStyle = () => ({
  background: 'var(--oa-bg-muted)',
  fontWeight: 600,
  color: 'var(--oa-text-secondary)',
  height: '44px'
});

const tableCellStyle = () => ({
  height: '44px',
  padding: '8px 10px'
});

const formatDate = (value?: string | null) => {
  if (!value) return '-';
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss');
};

const statusTag = (status: string) => {
  switch (status) {
    case 'active':
      return 'success';
    case 'paused':
      return 'warning';
    case 'archived':
      return 'info';
    default:
      return 'info';
  }
};

const fetchProbeOptions = async () => {
  probesLoading.value = true;
  try {
    const { data } = await apiClient.get<ProbeNodeSummary[]>('/probes/nodes/');
    probeOptions.value = data;
  } catch (error) {
    ElMessage.error('加载探针节点失败');
  } finally {
    probesLoading.value = false;
  }
};

const loadSchedules = async () => {
  loading.value = true;
  try {
    schedules.value = await listProbeSchedules({});
  } catch (error) {
    ElMessage.error('加载调度数据失败');
  } finally {
    loading.value = false;
  }
};

const toggleSchedule = async (schedule: ProbeScheduleRecord, nextActive: boolean) => {
  if (togglingId.value) return;
  togglingId.value = schedule.id;
  try {
    if (nextActive) {
      await resumeProbeSchedule(schedule.id);
      ElMessage.success('已启用');
    } else {
      const { value, action } = await ElMessageBox.prompt('请输入暂停原因（可选）', '暂停调度', {
        confirmButtonText: '暂停',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：临时维护/目标下线/变更窗口'
      }).catch(() => ({ value: '', action: 'cancel' as const }));
      if (action !== 'confirm') {
        await loadSchedules();
        togglingId.value = null;
        return;
      }
      await pauseProbeSchedule(schedule.id, value || undefined);
      ElMessage.success('已暂停');
    }
    await loadSchedules();
  } catch (error) {
    ElMessage.error('操作失败，请稍后重试');
    await loadSchedules();
  } finally {
    togglingId.value = null;
  }
};

const openCreateDialog = () => {
  editor.visible = true;
  editor.isEdit = false;
  editor.form = {
    id: null,
    name: '',
    target: '',
    protocol: 'HTTPS',
    frequency_minutes: 5,
    probe_ids: [],
    description: '',
    start_at: '',
    end_at: '',
    timeout_seconds: 30,
    expected_status_codes: [200],
    alert_threshold: 1,
    alert_contacts: []
  };
  expectedStatusInput.value = '200';
  alertContactsText.value = '';
  if (!probeOptions.value.length) {
    fetchProbeOptions();
  }
};

const editSchedule = (schedule: ProbeScheduleRecord) => {
  if (schedule.source_type !== 'manual' && schedule.source_type !== 'monitoring_request') {
    ElMessage.warning('该调度来源不支持编辑');
    return;
  }
  if (schedule.source_type === 'monitoring_request') {
    ElMessage.info('该调度来自拨测申请，保存后会同步回申请并立即生效');
  }
  editor.visible = true;
  editor.isEdit = true;
  editor.form = {
    id: schedule.id,
    name: schedule.name,
    target: schedule.target,
    protocol: schedule.protocol,
    frequency_minutes: schedule.frequency_minutes,
    probe_ids: schedule.probes.map((probe) => probe.id),
    description: schedule.description || '',
    start_at: schedule.start_at || '',
    end_at: schedule.end_at || '',
    timeout_seconds: schedule.timeout_seconds || 30,
    expected_status_codes: schedule.expected_status_codes?.length ? [...schedule.expected_status_codes] : [200],
    alert_threshold: schedule.alert_threshold || 1,
    alert_contacts: schedule.alert_contacts?.length ? [...schedule.alert_contacts] : []
  };
  expectedStatusInput.value = editor.form.expected_status_codes.join(', ');
  alertContactsText.value = editor.form.alert_contacts.join(', ');
  if (!probeOptions.value.length) {
    fetchProbeOptions();
  }
};

const openDetail = (schedule: ProbeScheduleRecord) => {
  currentSchedule.value = schedule;
  detailVisible.value = true;
};

const submitSchedule = async () => {
  if (!editor.form.name || !editor.form.target) {
    ElMessage.error('名称和目标不能为空');
    return;
  }
  if (!editor.form.probe_ids.length) {
    ElMessage.error('至少选择一个探针节点');
    return;
  }
  editor.submitting = true;
  try {
    const contacts = parseContacts(alertContactsText.value);
    editor.form.alert_contacts = contacts;
    const statusCodes = expectedStatusCodes.value.length ? expectedStatusCodes.value : [200];
    editor.form.expected_status_codes = statusCodes;
    const payload: CreateProbeSchedulePayload = {
      name: editor.form.name,
      target: editor.form.target,
      protocol: editor.form.protocol,
      frequency_minutes: editor.form.frequency_minutes,
      probe_ids: editor.form.probe_ids,
      description: editor.form.description || undefined,
      start_at: editor.form.start_at || undefined,
      end_at: editor.form.end_at || undefined,
      timeout_seconds: editor.form.timeout_seconds || undefined,
      expected_status_codes: statusCodes,
      alert_threshold: editor.form.alert_threshold || undefined,
      alert_contacts: contacts.length ? contacts : undefined
    };
    if (editor.isEdit && editor.form.id) {
      await updateProbeSchedule(editor.form.id, payload);
      ElMessage.success('调度已更新');
    } else {
      await createProbeSchedule(payload);
      ElMessage.success('调度创建成功');
    }
    editor.visible = false;
    await loadSchedules();
  } catch (error) {
    ElMessage.error('保存失败，请稍后重试');
  } finally {
    editor.submitting = false;
  }
};

const removeSchedule = async (schedule: ProbeScheduleRecord) => {
  try {
    await ElMessageBox.confirm('删除后将无法恢复该调度计划，确定删除？', '删除调度', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'error'
    });
    await deleteProbeSchedule(schedule.id);
    ElMessage.success('调度已删除');
    await loadSchedules();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败，请稍后重试');
    }
  }
};

function parseContacts(input: string): string[] {
  return input
    .split(/[,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseStatusCodes(input: string): number[] {
  if (!input) return [];
  const normalized = input
    .split(/[,，\s]+/)
    .map((value) => Number(value))
    .filter((code) => Number.isInteger(code) && code >= 100 && code <= 599);
  return Array.from(new Set(normalized));
}

onMounted(async () => {
  await Promise.all([fetchProbeOptions(), loadSchedules()]);
});
</script>

<style scoped>
.probe-schedules {
  padding: 0 16px 0;
  display: flex;
  flex-direction: column;
  /* gap: 12px; */
  flex: 1;
  min-height: 0;·
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--oa-border-light);
  gap:12px;
  margin: 0px
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--oa-text-primary);
}

.table-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  min-height: 540px;
}

.page-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  gap: 12px;
  position: relative;
}

.table-card {
  border: none;
  box-shadow: none;
  background: var(--oa-bg-panel);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.table-card :deep(.el-card__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.table-card :deep(.el-table__inner-wrapper) {
  border-left: none !important;
  border-right: none !important;
}

.schedule-table {
  flex: 1;
  min-height: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--oa-border-light);
  border-radius: 8px;
  background: var(--oa-bg-panel);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
  box-shadow: var(--oa-shadow-sm);
}

.refresh-card:hover {
  border-color: var(--oa-color-primary-light);
  box-shadow: 0 10px 18px rgba(64, 158, 255, 0.08);
  transform: translateY(-1px);
}

.refresh-icon.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 8px;
}

.toolbar-left {
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-select {
  width: 160px;
}

.schedule-table {
  background: var(--oa-bg-panel);
}

.search-input {
  flex: 1;
  min-width: 380px;
}

.search-input--compact {
  max-width: 320px;
}

.pill-input :deep(.el-input__wrapper) {
  border-radius: 999px;
  padding-left: 0.85rem;
  background: var(--oa-filter-control-bg);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.pill-input :deep(.el-input__wrapper:hover) {
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.4);
}

.schedule-table :deep(.el-table__cell) {
  padding: 8px 10px;
}

.table-skeleton {
  padding: 12px 0;
  display: grid;
  gap: 12px;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-right {
  display: flex;
  align-items: center;
  margin-left: auto;
}

.schedule-name .description {
  display: block;
  color: var(--oa-text-muted);
  font-weight: normal;
}

.pager-sizes :deep(.el-input__wrapper) {
  padding: 0 10px;
}

.pager-main {
  display: flex;
  align-items: center;
}

.pager-main :deep(.el-pagination__sizes) {
  display: none;
}

.page-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 16px 12px;
  color: var(--oa-text-secondary);
  flex-wrap: wrap;
  border-top: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
  position: sticky;
  bottom: 0;
}

.schedule-name__link {
  color: var(--oa-color-primary);
  cursor: pointer;
}

.schedule-name__link:hover {
  text-decoration: underline;
}

.text-muted {
  color: var(--oa-text-muted);
}

.schedule-form {
  padding-right: 1rem;
}

.muted {
  color: var(--oa-text-secondary);
}
.probe-selector {
  width: 100%;
}

.status-tag-list {
  margin-top: 0.5rem;
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.hint-text {
  margin-left: 0.5rem;
  color: #909399;
}

.mt-3 {
  margin-top: 1.5rem;
}
</style>
