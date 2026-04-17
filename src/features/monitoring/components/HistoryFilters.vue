<template>
  <el-card
    shadow="never"
    class="filters-card"
  >
    <el-form
      :model="localFilters"
      label-width="100px"
      inline
      class="filters-form"
    >
      <el-form-item label="目标">
        <el-input
          v-model="localFilters.target"
          placeholder="输入域名或关键字"
          clearable
          @keyup.enter="emitFilters"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-select
          v-model="localFilters.status"
          placeholder="全部状态"
          clearable
        >
          <el-option
            v-for="option in statusOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="协议">
        <el-select
          v-model="localFilters.protocol"
          placeholder="全部协议"
          clearable
        >
          <el-option
            v-for="option in protocolOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="探针节点">
        <el-input
          v-model="localFilters.probe_id"
          placeholder="粘贴探针 UUID"
          clearable
        />
      </el-form-item>
      <el-form-item label="执行时间">
        <el-date-picker
          v-model="timeRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DDTHH:mm:ss[Z]"
          :shortcuts="dateShortcuts"
          unlink-panels
        />
      </el-form-item>
      <el-form-item>
        <el-space>
          <el-button
            type="primary"
            @click="emitFilters"
          >
            查询
          </el-button>
          <el-button @click="resetFilters">
            重置
          </el-button>
        </el-space>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import { computed, reactive, ref, watch } from 'vue';

import type { ProbeScheduleExecutionFilters } from '@/features/monitoring/api/probeScheduleExecutionApi';

dayjs.extend(utc);

const props = defineProps<{
  modelValue: ProbeScheduleExecutionFilters;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: ProbeScheduleExecutionFilters): void;
  (e: 'submit', value: ProbeScheduleExecutionFilters): void;
}>();

const statusOptions = [
  { value: 'scheduled', label: '待执行' },
  { value: 'running', label: '执行中' },
  { value: 'succeeded', label: '成功' },
  { value: 'failed', label: '失败' },
  { value: 'missed', label: '错过执行' }
];

const protocolOptions = [
  { value: 'HTTP', label: 'HTTP' },
  { value: 'HTTPS', label: 'HTTPS' },
  { value: 'Telnet', label: 'Telnet' },
  { value: 'WSS', label: 'WebSocket Secure' },
  { value: 'TCP', label: 'TCP' },
  { value: 'CERTIFICATE', label: '证书检测' }
];

const localFilters = reactive<ProbeScheduleExecutionFilters>({
  target: props.modelValue.target ?? '',
  status: props.modelValue.status,
  protocol: props.modelValue.protocol,
  probe_id: props.modelValue.probe_id,
  page_size: props.modelValue.page_size ?? 20
});

const timeRange = ref<string[] | null>(
  props.modelValue.started_after && props.modelValue.started_before
    ? [props.modelValue.started_after, props.modelValue.started_before]
    : null
);

watch(
  () => props.modelValue,
  (value) => {
    localFilters.target = value.target ?? '';
    localFilters.status = value.status;
    localFilters.protocol = value.protocol;
    localFilters.probe_id = value.probe_id;
    localFilters.page_size = value.page_size ?? 20;
    timeRange.value =
      value.started_after && value.started_before
        ? [value.started_after, value.started_before]
        : null;
  },
  { deep: true }
);

const dateShortcuts = computed(() => [
  {
    text: '最近 24 小时',
    value: () => {
      const end = dayjs();
      const start = end.subtract(1, 'day');
      return [
        start.utc().format('YYYY-MM-DDTHH:mm:ss[Z]'),
        end.utc().format('YYYY-MM-DDTHH:mm:ss[Z]')
      ];
    }
  },
  {
    text: '最近 7 天',
    value: () => {
      const end = dayjs();
      const start = end.subtract(7, 'day');
      return [
        start.utc().format('YYYY-MM-DDTHH:mm:ss[Z]'),
        end.utc().format('YYYY-MM-DDTHH:mm:ss[Z]')
      ];
    }
  }
]);

function emitFilters() {
  const payload: ProbeScheduleExecutionFilters = {
    target: localFilters.target?.trim() || undefined,
    status: localFilters.status,
    protocol: localFilters.protocol,
    probe_id: localFilters.probe_id?.trim() || undefined,
    page_size: localFilters.page_size ?? 20,
    page: 1
  };

  if (timeRange.value && timeRange.value.length === 2) {
    payload.started_after = timeRange.value[0];
    payload.started_before = timeRange.value[1];
  } else {
    payload.started_after = undefined;
    payload.started_before = undefined;
  }

  emit('update:modelValue', payload);
  emit('submit', payload);
}

function resetFilters() {
  timeRange.value = null;
  localFilters.target = '';
  localFilters.status = undefined;
  localFilters.protocol = undefined;
  localFilters.probe_id = undefined;
  localFilters.page_size = 20;
  const defaults: ProbeScheduleExecutionFilters = {
    page: 1,
    page_size: 20
  };
  emit('update:modelValue', defaults);
  emit('submit', defaults);
}
</script>

<style scoped>
.filters-card {
  margin-bottom: 1rem;
}

.filters-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  align-items: center;
}
</style>
