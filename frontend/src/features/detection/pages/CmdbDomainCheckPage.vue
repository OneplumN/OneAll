<template>
  <DetectionPageBase
    title="CMDB 域名检测"
    :error="submissionError"
    config-title="查询条件"
    refreshable
    :refreshing="headerRefreshing"
    refresh-text="刷新"
    @refresh="handleHeaderRefresh"
  >
    <template #header-left>
      <div class="single-combo">
        <el-input
          v-model="form.target"
          class="single-combo__input"
          size="large"
          placeholder="例如 example.com"
          :disabled="submitting"
          clearable
          @keyup.enter="handleSubmit"
        />
      </div>
    </template>

    <template #config-footer>
      <div class="submit-row">
        <el-button
          type="primary"
          size="large"
          class="submit-row__action"
          :loading="submitting"
          :disabled="submitting"
          @click="handleSubmit"
        >
          查询
        </el-button>
      </div>
    </template>

    <template #content>
      <DetectionResults
        title="查询结果"
        :data="recordEntries"
        :loading="submitting"
        empty-text="暂无资产信息"
        :can-clear="canClearResult"
        @clear="clearResult"
      >
        <template
          v-if="!currentTarget && !submitting"
          #title-extra
        >
          输入域名后查询 CMDB 资产信息；本页不发起拨测，仅用于确认资产是否收录与字段详情
        </template>

        <template
          v-if="cmdbNoticeText"
          #notice
        >
          <el-alert
            type="warning"
            :closable="false"
            show-icon
          >
            {{ cmdbNoticeText }}
          </el-alert>
        </template>

        <template #actions>
          <el-tag
            :type="summaryTagType"
            effect="plain"
            size="small"
            class="status-tag"
          >
            {{ summaryStatusText }}
          </el-tag>
          <el-button
            text
            size="small"
            :disabled="!resultRecord"
            @click="copyRecord"
          >
            复制 JSON
          </el-button>
          <el-button
            text
            size="small"
            :disabled="!currentTarget && !resultRecord"
            @click="clearResult"
          >
            清空
          </el-button>
        </template>

        <template #description>
          <el-descriptions
            :column="2"
            size="small"
            class="cmdb-summary"
          >
            <el-descriptions-item label="当前查询">
              {{
                requestedTarget || currentTarget || '-'
              }}
            </el-descriptions-item>
            <el-descriptions-item label="最近查询">
              {{ lastQueriedAtText }}
            </el-descriptions-item>
            <el-descriptions-item label="结果来源">
              {{ resultSourceText }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              {{ summaryStatusText }}
            </el-descriptions-item>
            <el-descriptions-item label="提示信息">
              {{ resultMessage || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </template>

        <template #columns>
          <el-table-column
            prop="label"
            label="字段"
            min-width="200"
          />
          <el-table-column
            prop="value"
            label="值"
            min-width="320"
            show-overflow-tooltip
          />
        </template>
      </DetectionResults>
    </template>
  </DetectionPageBase>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { computed, nextTick, reactive, ref, watch } from 'vue';

import { validateDomainWithCMDB } from '@/features/detection/api/detectionApi';
import DetectionPageBase from '../components/DetectionPageBase.vue';
import DetectionResults from '../components/DetectionResults.vue';
import {
  type CmdbRecord,
  CMDB_FIELD_LABELS,
  getStatusTagType,
  getStatusText,
  formatDate
} from '../mappers/detectionUtils';

const CMDB_KEY_PRIORITY = ['domain', 'system', 'internet_type', 'owner', 'contacts'];
const cmdbKeyPriorityMap = new Map(CMDB_KEY_PRIORITY.map((key, index) => [key, index]));

const form = reactive({
  target: ''
});

const submitting = ref(false);
const headerRefreshing = ref(false);
const submissionError = ref<string | null>(null);
const resultStatus = ref<'ok' | 'not_found' | 'error' | null>(null);
const resultMessage = ref<string | null>(null);
const resultRecord = ref<CmdbRecord | null>(null);
const currentTarget = ref<string | null>(null);
const requestedTarget = ref<string | null>(null);
const lastQueriedAt = ref<string | null>(null);
const staleResult = ref(false);

const recordEntries = computed(() => {
  if (!resultRecord.value) return [];
  return Object.entries(resultRecord.value)
    .sort(([leftKey], [rightKey]) => {
      const leftPriority = cmdbKeyPriorityMap.get(leftKey);
      const rightPriority = cmdbKeyPriorityMap.get(rightKey);
      if (leftPriority !== undefined && rightPriority !== undefined)
        return leftPriority - rightPriority;
      if (leftPriority !== undefined) return -1;
      if (rightPriority !== undefined) return 1;
      return leftKey.localeCompare(rightKey);
    })
    .map(([key, value]) => ({
      key,
      label: CMDB_FIELD_LABELS[key] ?? key,
      value: value == null ? '-' : typeof value === 'object' ? JSON.stringify(value) : String(value)
    }));
});

const summaryTagType = computed(() => {
  if (submitting.value) return 'info';
  return getStatusTagType(resultStatus.value ?? 'pending');
});

const summaryStatusText = computed(() => {
  if (submitting.value) return '查询中';
  return getStatusText(resultStatus.value ?? 'pending');
});

const lastQueriedAtText = computed(() => {
  if (submitting.value) return '查询中...';
  if (!lastQueriedAt.value) return '-';
  return formatDate(lastQueriedAt.value);
});

const resultSourceText = computed(() => {
  if (!resultRecord.value) return '-';
  if (staleResult.value && currentTarget.value) {
    return `上一条成功结果（${currentTarget.value}）`;
  }
  return currentTarget.value || '-';
});

const cmdbNoticeText = computed(() => {
  if (!staleResult.value || !resultRecord.value) return null;
  if (requestedTarget.value && currentTarget.value && requestedTarget.value !== currentTarget.value) {
    return `当前查询 ${requestedTarget.value} 失败，以下仍显示 ${currentTarget.value} 的上一条成功结果。`;
  }
  return '当前查询失败，以下仍显示上一条成功结果。';
});

const canClearResult = computed(() =>
  Boolean(requestedTarget.value || currentTarget.value || resultRecord.value || resultMessage.value)
);

watch(
  () => form.target,
  () => {
    submissionError.value = null;
  }
);

function clearResult() {
  resultStatus.value = null;
  resultMessage.value = null;
  resultRecord.value = null;
  currentTarget.value = null;
  requestedTarget.value = null;
  lastQueriedAt.value = null;
  staleResult.value = false;
  submissionError.value = null;
}

async function copyRecord() {
  if (!resultRecord.value) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(resultRecord.value, null, 2));
    ElMessage.success('已复制资产 JSON');
  } catch {
    ElMessage.error('复制失败，请手动复制。');
  }
}

async function runCmdbQuery(domain: string, options?: { silent?: boolean }) {
  const silent = options?.silent ?? false;
  const previousRecord = resultRecord.value;
  const previousTarget = currentTarget.value;
  const previousQueriedAt = lastQueriedAt.value;

  requestedTarget.value = domain;
  if (!domain) {
    submissionError.value = '请输入域名';
    return;
  }

  submitting.value = true;
  submissionError.value = null;

  try {
    const resp = await validateDomainWithCMDB(domain);
    resultStatus.value = resp.status;
    resultMessage.value = resp.message ?? null;
    lastQueriedAt.value = new Date().toISOString();
    staleResult.value = false;

    if (resp.status === 'ok') {
      resultRecord.value = resp.record ?? null;
      currentTarget.value = domain;
    } else if (resp.status === 'not_found') {
      resultRecord.value = null;
      currentTarget.value = domain;
    } else if (previousRecord) {
      resultRecord.value = previousRecord;
      currentTarget.value = previousTarget;
      lastQueriedAt.value = previousQueriedAt;
      staleResult.value = true;
    } else {
      resultRecord.value = null;
      currentTarget.value = domain;
    }

    if (silent) return;

    if (resp.status === 'not_found') {
      ElMessage.warning('CMDB 中没有找到该域名');
    } else if (resp.status === 'ok') {
      ElMessage.success('查询成功，已获取资产信息');
    } else {
      ElMessage.error(resp.message ?? '查询失败');
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '查询失败，请稍后再试。';
    resultStatus.value = 'error';
    resultMessage.value = message;
    if (previousRecord) {
      resultRecord.value = previousRecord;
      currentTarget.value = previousTarget;
      lastQueriedAt.value = previousQueriedAt;
      staleResult.value = true;
    } else {
      resultRecord.value = null;
      currentTarget.value = domain;
      lastQueriedAt.value = new Date().toISOString();
      staleResult.value = false;
      submissionError.value = message;
    }
  } finally {
    submitting.value = false;
  }
}

async function handleSubmit() {
  await runCmdbQuery(form.target.trim());
}

async function handleHeaderRefresh() {
  if (headerRefreshing.value) return;
  headerRefreshing.value = true;
  try {
    submissionError.value = null;
    await nextTick();
    const domain = requestedTarget.value || currentTarget.value;
    if (domain) {
      await runCmdbQuery(domain, { silent: true });
    }
    ElMessage.success('页面状态已刷新');
  } finally {
    headerRefreshing.value = false;
  }
}
</script>

<style scoped>
@import '../styles/detection-common.scss';

.cmdb-summary {
  :deep(.el-descriptions__label) {
    color: var(--oa-text-secondary);
    width: 90px;
  }

  :deep(.el-descriptions__content) {
    color: var(--oa-text-primary);
  }
}

.single-combo {
  display: flex;
  align-items: stretch;
  flex: 1;
  width: 100%;
  min-width: min(520px, 100%);
  border-radius: var(--oa-radius-md);
  background: var(--oa-bg-panel);
  box-shadow: 0 0 0 1px var(--oa-border-color) inset;
  transition: box-shadow 0.2s ease;
  overflow: hidden;
}

.single-combo:hover {
  box-shadow: 0 0 0 1px var(--oa-text-muted) inset;
}

.single-combo:focus-within {
  box-shadow: 0 0 0 2px var(--oa-color-primary-light) inset;
}

.single-combo__input {
  flex: 1;
  min-width: 0;
}

.single-combo :deep(.single-combo__input .el-input__wrapper),
.single-combo :deep(.single-combo__input .el-input__wrapper:hover),
.single-combo :deep(.single-combo__input .el-input__wrapper.is-focus) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: var(--oa-radius-md);
  min-height: 44px;
}

.submit-row {
  display: flex;
  justify-content: center;
  width: 100%;
}

.submit-row__action {
  min-height: 44px;
  min-width: 140px;
}

@media (max-width: 768px) {
  .single-combo {
    min-width: auto;
    width: 100%;
  }

  :deep(.el-descriptions) {
    :deep(.el-descriptions__body) {
      :deep(.el-descriptions__table) {
        :deep(.el-descriptions__cell) {
          padding: 8px 12px;
        }
      }
    }
  }
}
</style>
