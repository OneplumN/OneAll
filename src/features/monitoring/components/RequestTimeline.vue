<template>
  <component
    :is="embedded ? 'section' : 'el-card'"
    v-bind="embedded ? {} : { shadow: 'never' }"
  >
    <template
      v-if="!embedded"
      #header
    >
      <div class="timeline-header">
        <span>审批进程</span>
        <el-tag
          v-if="!requests.length"
          type="info"
        >
          暂无申请
        </el-tag>
      </div>
    </template>

    <div
      v-if="embedded && !requests.length"
      class="timeline-empty"
    >
      <el-empty
        description="暂无申请记录"
        :image-size="60"
      />
    </div>

    <el-timeline v-else>
      <el-timeline-item
        v-for="request in requests"
        :key="request.id"
        :timestamp="formatTime(request.created_at)"
        :type="statusType(request.status)"
      >
        <div class="timeline-item__title">
          {{ request.title }} - {{ request.target }}
        </div>
        <div class="timeline-item__meta">
          协议：{{ request.protocol }}，频率：{{ request.frequency_minutes }} 分钟
        </div>
        <div class="timeline-item__status">
          <el-tag
            size="small"
            :type="statusTagType(request.status)"
          >
            {{ statusText(request.status) }}
          </el-tag>
          <span
            v-if="request.status === 'pending'"
            class="ticket"
          >等待管理员审批</span>
          <span
            v-else-if="request.status === 'approved'"
            class="ticket"
          >已生效（可直接编辑，保存后立即生效）</span>
          <span
            v-else-if="request.status === 'rejected'"
            class="ticket"
          >已驳回（可修改后重新提交）</span>
        </div>

        <div
          v-if="request.status === 'rejected' && rejectReason(request)"
          class="timeline-item__reason"
        >
          驳回原因：{{ rejectReason(request) }}
        </div>

        <div
          v-if="actionButtonsVisible(request)"
          class="timeline-item__actions"
        >
          <template v-if="request.status === 'pending' && isAdmin">
            <el-button
              size="small"
              type="primary"
              :loading="busyId === request.id"
              @click="handleApprove(request)"
            >
              通过
            </el-button>
            <el-button
              size="small"
              :loading="busyId === request.id"
              @click="handleReject(request)"
            >
              驳回
            </el-button>
          </template>

          <template v-else-if="request.status === 'approved' && canEdit(request)">
            <el-button
              size="small"
              @click="$emit('edit', request)"
            >
              编辑
            </el-button>
          </template>

          <template v-else-if="request.status === 'rejected' && canEdit(request)">
            <el-button
              size="small"
              @click="$emit('edit', request)"
            >
              修改
            </el-button>
            <el-button
              size="small"
              type="primary"
              :loading="busyId === request.id"
              @click="handleResubmit(request)"
            >
              重新提交
            </el-button>
          </template>
        </div>
      </el-timeline-item>
    </el-timeline>
  </component>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { computed, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

import type { MonitoringRequestRecord } from '@/features/monitoring/api/monitoringApi';
import { approveMonitoringRequest, rejectMonitoringRequest, resubmitMonitoringRequest } from '@/features/monitoring/api/monitoringApi';

const props = withDefaults(
  defineProps<{
    requests: MonitoringRequestRecord[];
    embedded?: boolean;
    currentUserId?: string | null;
    isAdmin?: boolean;
  }>(),
  {
    embedded: false,
    currentUserId: null
  }
);

const emit = defineEmits<{
  (e: 'refresh'): void;
  (e: 'edit', request: MonitoringRequestRecord): void;
}>();

const busyId = ref<string | null>(null);
const isAdmin = computed(() => Boolean(props.isAdmin));

function formatTime(value?: string) {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '';
}

function statusType(status: string) {
  if (status === 'approved') return 'success';
  if (status === 'rejected') return 'danger';
  return 'info';
}

function statusTagType(status: string) {
  if (status === 'approved') return 'success';
  if (status === 'rejected') return 'danger';
  if (status === 'pending') return 'warning';
  return 'info';
}

function statusText(status: string) {
  if (status === 'pending') return '待审批';
  if (status === 'approved') return '已通过';
  if (status === 'rejected') return '已驳回';
  if (status === 'cancelled') return '已取消';
  return status;
}

function rejectReason(request: MonitoringRequestRecord) {
  const meta = request.metadata || {};
  const reason = meta.reject_reason;
  if (!reason) return '';
  return String(reason);
}

function canEdit(request: MonitoringRequestRecord) {
  if (isAdmin.value) return true;
  if (!props.currentUserId) return false;
  return Boolean(request.created_by_id && request.created_by_id === props.currentUserId);
}

function actionButtonsVisible(request: MonitoringRequestRecord) {
  if (request.status === 'pending') return isAdmin.value;
  if (request.status === 'approved') return canEdit(request);
  if (request.status === 'rejected') return canEdit(request);
  return false;
}

async function handleApprove(request: MonitoringRequestRecord) {
  if (busyId.value) return;
  busyId.value = request.id;
  try {
    await approveMonitoringRequest(request.id);
    ElMessage.success('已通过并生效');
    busyId.value = null;
    emit('refresh');
  } catch (error) {
    ElMessage.error('审批失败');
    busyId.value = null;
  }
}

async function handleReject(request: MonitoringRequestRecord) {
  if (busyId.value) return;
  const { value, action } = await ElMessageBox.prompt('请输入驳回原因', '驳回申请', {
    confirmButtonText: '驳回',
    cancelButtonText: '取消',
    inputPlaceholder: '例如：探针选择不合理/目标不规范/信息不完整'
  }).catch(() => ({ value: '', action: 'cancel' as const }));
  if (action !== 'confirm') return;

  busyId.value = request.id;
  try {
    await rejectMonitoringRequest(request.id, value);
    ElMessage.success('已驳回');
    busyId.value = null;
    emit('refresh');
  } catch (error) {
    ElMessage.error('驳回失败');
    busyId.value = null;
  }
}

async function handleResubmit(request: MonitoringRequestRecord) {
  if (busyId.value) return;
  busyId.value = request.id;
  try {
    await resubmitMonitoringRequest(request.id);
    ElMessage.success('已重新提交，等待审批');
    busyId.value = null;
    emit('refresh');
  } catch (error) {
    ElMessage.error('重新提交失败');
    busyId.value = null;
  }
}
</script>

<style scoped>
.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.timeline-empty {
  padding: 12px 0;
}

.timeline-item__title {
  font-weight: 600;
  color: var(--oa-text-primary);
  margin-bottom: 4px;
}

.timeline-item__meta {
  color: var(--oa-text-secondary);
  font-size: 13px;
  margin-bottom: 8px;
}

.timeline-item__status {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ticket {
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.timeline-item__reason {
  margin-top: 8px;
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.timeline-item__actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
