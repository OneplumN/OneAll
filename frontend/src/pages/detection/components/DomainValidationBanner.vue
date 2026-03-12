<template>
  <div v-if="visible" :data-test="testId">
    <el-alert :type="alertType" :closable="false" show-icon>
      {{ displayMessage }}
    </el-alert>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  status: 'ok' | 'not_found' | 'error' | null;
  message?: string | null;
  loading?: boolean;
}>();

const visible = computed(() => !props.loading && props.status && props.status !== 'ok');

const alertType = computed(() => (props.status === 'error' ? 'error' : 'warning'));

const displayMessage = computed(() => {
  if (props.status === 'not_found') {
    return props.message || '该域名未在 CMDB 中登记，请确认资产信息。';
  }
  if (props.status === 'error') {
    return props.message || 'CMDB 校验失败，请稍后重试。';
  }
  return '';
});

const testId = computed(() => (props.status === 'not_found' ? 'cmdb-warning-banner' : 'cmdb-error-banner'));
</script>
