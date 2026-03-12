<template>
  <el-drawer v-model="visible" size="40%" title="策略详情">
    <div v-if="policy" class="detail-drawer">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="策略名称">{{ policy.name }}</el-descriptions-item>
        <el-descriptions-item label="调度来源">{{ policy.source_display }}</el-descriptions-item>
        <el-descriptions-item label="目标">{{ policy.target }}</el-descriptions-item>
        <el-descriptions-item label="协议">{{ policy.protocol }}</el-descriptions-item>
        <el-descriptions-item label="频率">
          {{ policy.frequency_minutes }} 分钟
        </el-descriptions-item>
        <el-descriptions-item label="时间窗口">
          <span v-if="policy.start_at">{{ formatDate(policy.start_at) }}</span>
          <span v-else>立即生效</span>
          <template v-if="policy.end_at">
            <span> - {{ formatDate(policy.end_at) }}</span>
          </template>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTag(policy.status)" size="small">{{ policy.status_display }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="告警阈值">
          {{ policy.alert_threshold ?? '默认 1 次失败' }}
        </el-descriptions-item>
        <el-descriptions-item label="联系人">
          <el-space wrap>
            <el-tag
              v-for="contact in policy.alert_contacts || []"
              :key="contact"
              type="success"
              size="small"
            >
              {{ contact }}
            </el-tag>
            <span v-if="!policy.alert_contacts?.length" class="text-muted">未配置</span>
          </el-space>
        </el-descriptions-item>
        <el-descriptions-item label="期望状态码">
          {{ policy.expected_status_codes?.join(', ') || '200' }}
        </el-descriptions-item>
        <el-descriptions-item label="请求超时">
          {{ policy.timeout_seconds ? `${policy.timeout_seconds} 秒` : '默认 30 秒' }}
        </el-descriptions-item>
        <el-descriptions-item label="上下次执行">
          <div class="runtime-text">
            <p>上次：{{ formatDate(policy.last_run_at) }}</p>
            <p>下次：{{ formatDate(policy.next_run_at) }}</p>
          </div>
        </el-descriptions-item>
      </el-descriptions>
      <section class="detail-section">
        <h4>绑定探针</h4>
        <el-space wrap>
          <el-tag v-for="probe in policy.probes" :key="probe.id" size="small">
            {{ probe.name }}
          </el-tag>
          <span v-if="!policy.probes.length" class="text-muted">未绑定</span>
        </el-space>
      </section>
      <section class="detail-section">
        <h4>备注</h4>
        <p>{{ policy.description || '无' }}</p>
      </section>
      <section class="detail-section">
        <div class="recent-headline">
          <h4>最近执行</h4>
          <small>最多展示 10 条</small>
        </div>
        <el-skeleton v-if="executionsLoading" :rows="3" animated />
        <template v-else>
          <el-table
            v-if="recentExecutions.length"
            :data="recentExecutions"
            border
            size="small"
            class="execution-table"
          >
            <el-table-column label="调度时间" min-width="160">
              <template #default="{ row }">
                <div class="execution-times">
                  <span>调度：{{ formatDate(row.scheduled_at) }}</span>
                  <span v-if="row.finished_at">完成：{{ formatDate(row.finished_at) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="executionStatusTag(row.status)" size="small">
                  {{ executionStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="探针" min-width="140">
              <template #default="{ row }">
                {{ row.probe?.name ?? '—' }}
              </template>
            </el-table-column>
            <el-table-column label="耗时" width="100">
              <template #default="{ row }">
                {{ row.response_time_ms != null ? `${row.response_time_ms} ms` : '—' }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无执行记录" />
        </template>
      </section>
    </div>
    <el-empty v-else description="暂无数据" />
  </el-drawer>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { computed, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';

import type { ProbeScheduleRecord } from '@/services/probeScheduleApi';
import {
  fetchScheduleExecutionsBySchedule,
  type ProbeScheduleExecutionRecord
} from '@/services/probeScheduleExecutionApi';

const props = defineProps<{ modelValue: boolean; policy: ProbeScheduleRecord | null }>();
const emit = defineEmits<{ (event: 'update:modelValue', value: boolean): void }>();

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
});

const executionsLoading = ref(false);
const recentExecutions = ref<ProbeScheduleExecutionRecord[]>([]);

const loadExecutions = async () => {
  if (!props.policy) return;
  executionsLoading.value = true;
  try {
    const response = await fetchScheduleExecutionsBySchedule(props.policy.id, { page_size: 10 });
    recentExecutions.value = response.items ?? [];
  } catch (error) {
    ElMessage.error('加载执行记录失败');
  } finally {
    executionsLoading.value = false;
  }
};

watch(
  () => props.modelValue,
  (value) => {
    if (value && props.policy) {
      loadExecutions();
    } else if (!value) {
      recentExecutions.value = [];
    }
  }
);

watch(
  () => props.policy?.id,
  (value, previous) => {
    if (props.modelValue && value && value !== previous) {
      loadExecutions();
    }
  }
);

const formatDate = (value?: string | null) => {
  if (!value) return '—';
  return dayjs(value).format('YYYY-MM-DD HH:mm');
};

const statusTag = (status: string) => {
  if (status === 'active') return 'success';
  if (status === 'paused') return 'warning';
  if (status === 'archived') return 'info';
  return '';
};

const executionStatusTag = (status: string) => {
  switch (status) {
    case 'succeeded':
      return 'success';
    case 'failed':
    case 'missed':
      return 'danger';
    case 'running':
      return 'info';
    case 'scheduled':
      return 'warning';
    default:
      return '';
  }
};

const executionStatusLabel = (status: string) => {
  switch (status) {
    case 'succeeded':
      return '成功';
    case 'failed':
      return '失败';
    case 'missed':
      return '错过执行';
    case 'running':
      return '执行中';
    case 'scheduled':
      return '待执行';
    default:
      return status;
  }
};
</script>

<style scoped>
.detail-drawer {
  padding-right: 1rem;
}

.detail-section {
  margin-top: 1.25rem;
}

.detail-section h4 {
  margin-bottom: 0.5rem;
}

.runtime-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.text-muted {
  color: #c0c4cc;
}

.recent-headline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #909399;
}

.execution-table {
  margin-top: 0.5rem;
}

.execution-times {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
</style>
