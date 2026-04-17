<template>
  <el-card
    class="result-panel"
    shadow="never"
  >
    <template #header>
      <div class="header">
        <span>拨测结果</span>
        <el-tag
          :type="statusTagType"
          size="small"
        >
          {{ detection.status }}
        </el-tag>
      </div>
    </template>

    <el-descriptions
      :column="2"
      border
    >
      <el-descriptions-item label="目标地址">
        {{ detection.target }}
      </el-descriptions-item>
      <el-descriptions-item label="协议">
        {{ detection.protocol }}
      </el-descriptions-item>
      <el-descriptions-item label="响应状态">
        {{ detection.status_code ?? '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="耗时 (ms)">
        {{ detection.response_time_ms ?? '-' }}
      </el-descriptions-item>
    </el-descriptions>

    <section
      v-if="certificate"
      class="certificate-section"
    >
      <h4>证书信息</h4>
      <el-descriptions
        :column="1"
        border
      >
        <el-descriptions-item label="状态">
          <el-tag
            :type="certificateTagType"
            size="small"
          >
            {{ certificate.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="剩余有效期 (天)">
          {{ certificate.days_until_expiry ?? '未知' }}
        </el-descriptions-item>
        <el-descriptions-item label="颁发者">
          {{ certificate.issuer ?? '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="主题">
          {{ certificate.subject ?? '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </section>

    <section
      v-if="detection.error_message"
      class="error-section"
    >
      <el-alert
        type="error"
        :closable="false"
        show-icon
      >
        {{ detection.error_message }}
      </el-alert>
    </section>

    <section
      v-if="metadataKeys.length"
      class="metadata-section"
    >
      <h4>元数据</h4>
      <el-descriptions
        :column="1"
        border
      >
        <el-descriptions-item
          v-for="key in metadataKeys"
          :key="key"
          :label="key"
        >
          {{ detection.metadata?.[key] }}
        </el-descriptions-item>
      </el-descriptions>
    </section>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type DetectionResult = {
  status: string;
  target: string;
  protocol: string;
  response_time_ms?: number | null;
  status_code?: number | string | null;
  error_message?: string | null;
  metadata?: Record<string, unknown> | null;
};

type CertificateInfo = {
  status: string;
  days_until_expiry: number | null;
  issuer?: string | null;
  subject?: string | null;
};

const props = defineProps<{
  detection: DetectionResult;
  certificate?: CertificateInfo | null;
}>();

const statusTagType = computed(() => {
  switch (props.detection.status) {
    case 'succeeded':
    case 'success':
      return 'success';
    case 'timeout':
      return 'warning';
    default:
      return 'danger';
  }
});

const certificateTagType = computed(() => {
  const status = props.certificate?.status;
  if (status === 'valid') return 'success';
  if (status === 'expires_soon') return 'warning';
  return 'danger';
});

const metadataKeys = computed(() => Object.keys(props.detection.metadata || {}));
</script>

<style scoped>
.result-panel {
  margin-top: 1.5rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.certificate-section,
.metadata-section,
.error-section {
  margin-top: 1.5rem;
}
</style>
