<template>
  <DetectionPageBase
    root-title="工单申请"
    title="拨测监控申请"
    :error="error"
    config-title="申请配置"
    refreshable
    :refreshing="headerRefreshing"
    refresh-text="刷新"
    @refresh="handleHeaderRefresh"
  >
    <template #intro>
      <el-alert
        v-if="success"
        type="success"
        :closable="false"
        show-icon
        class="mb-4"
      >
        申请已提交：{{ success }}
      </el-alert>
      <el-alert
        v-if="editingRequestId"
        type="warning"
        show-icon
        class="mb-4"
        :closable="false"
      >
        <template v-if="editingRequestStatus === 'approved'">
          正在修改已通过并已生效的申请（ID：{{ editingRequestId }}）。保存修改后立即生效，无需重新提交。
        </template>
        <template v-else>
          正在修改已驳回的申请（ID：{{ editingRequestId }}）。保存修改后需要“重新提交”才会进入审批。
        </template>
      </el-alert>
    </template>

    <template #header-left>
      <div class="protocol-combo">
        <el-select
          v-model="form.protocol"
          class="protocol-combo__select"
          size="large"
          :disabled="submitting"
        >
          <el-option
            v-for="option in protocolOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
        <el-input
          v-model="form.target"
          class="protocol-combo__input"
          size="large"
          data-test="monitoring-target"
          :placeholder="targetPlaceholder"
          :disabled="submitting"
          clearable
          @keyup.enter="handleSubmit"
        />
      </div>
    </template>

    <template #config>
      <div class="detection-grid">
        <div class="request-left">
          <DetectionConfig
            title="基础信息"
            embedded
          >
            <template #config-items>
              <div class="config-item config-item--column">
                <div class="config-item__header">
                  <span class="config-item__label">拨测标题</span>
                </div>
                <el-input
                  v-model="form.title"
                  data-test="monitoring-title"
                />
              </div>

              <div class="config-item config-item--column">
                <div class="config-item__header">
                  <span class="config-item__label">所属系统</span>
                </div>
                <el-select
                  v-model="form.system_name"
                  data-test="monitoring-system-name"
                  filterable
                  allow-create
                  :loading="systemsLoading"
                  placeholder="请选择或输入系统名称"
                >
                  <el-option
                    v-for="option in systemOptions"
                    :key="option"
                    :label="option"
                    :value="option"
                  />
                </el-select>
              </div>

              <div class="config-item config-item--row">
                <span class="config-item__label">网络类型</span>
                <el-select
                  v-model="form.network_type"
                  class="narrow-select"
                >
                  <el-option
                    label="内网域名"
                    value="internal"
                  />
                  <el-option
                    label="互联网域名"
                    value="internet"
                  />
                </el-select>
              </div>

              <div class="config-item config-item--column">
                <div class="config-item__header">
                  <span class="config-item__label">负责人</span>
                </div>
                <el-input
                  v-model="form.owner_name"
                  placeholder="请输入负责人姓名"
                />
              </div>

              <div class="config-item config-item--column">
                <div class="config-item__header">
                  <span class="config-item__label">告警联系人</span>
                </div>
                <el-input
                  v-model="alertContactsText"
                  placeholder="示例：000123,000456"
                />
                <span class="hint-text hint-text--block">多个工号请用英文逗号分隔</span>
              </div>
            </template>
          </DetectionConfig>

          <ProbeNodeSelector
            v-model="form.probe_ids"
            :nodes="probes"
            :loading="probesLoading"
            embedded
            hint="可多选节点，将依次在各节点执行拨测。"
            @refresh="loadProbes"
          />
        </div>

        <DetectionConfig
          title="拨测配置"
          embedded
        >
          <template #config-items>
            <div class="config-item config-item--column">
              <div class="config-item__header">
                <span class="config-item__label">频率（分钟）</span>
              </div>
              <el-select
                v-model="form.frequency_minutes"
                :disabled="isCertificateProtocol"
                data-test="monitoring-frequency"
              >
                <el-option
                  v-for="option in frequencyOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
              <span
                v-if="isCertificateProtocol"
                class="hint-text hint-text--block"
              >证书检测默认每天执行一次。</span>
            </div>

            <div class="config-item config-item--row">
              <span class="config-item__label">告警阈值</span>
              <div class="inline-field">
                <el-input-number
                  v-model="form.alert_threshold"
                  :min="1"
                  :max="10"
                />
                <span class="hint-text inline-hint">连续失败次数</span>
              </div>
            </div>

            <div class="config-item config-item--column">
              <div class="config-item__header">
                <span class="config-item__label">期望状态码</span>
              </div>
              <el-input
                v-model="expectedStatusInput"
                placeholder="例如 200,202"
                clearable
                @blur="normalizeExpectedStatusInput"
              />
              <span class="hint-text hint-text--block">
                支持多个状态码，用逗号或空格分隔；留空默认 200。
              </span>
              <div
                v-if="expectedStatusCodes.length"
                class="status-tags"
              >
                <el-tag
                  v-for="code in expectedStatusCodes"
                  :key="code"
                  round
                  size="small"
                >
                  {{
                    code
                  }}
                </el-tag>
              </div>
            </div>
          </template>
        </DetectionConfig>
      </div>
    </template>

    <template #config-footer>
      <div class="submit-row">
        <el-button
          v-if="editingRequestId"
          size="large"
          @click="cancelEditing"
        >
          取消编辑
        </el-button>
        <el-button
          type="primary"
          size="large"
          :loading="submitting"
          :disabled="!canSubmit"
          @click="editingRequestId ? handleUpdate() : handleSubmit()"
        >
          {{ editingRequestId ? '保存修改' : '提交申请' }}
        </el-button>
      </div>
    </template>

    <template #content>
      <ResultsCard title="申请记录">
        <template #actions>
          <el-button
            text
            size="small"
            :loading="headerRefreshing"
            :disabled="headerRefreshing"
            @click="handleHeaderRefresh"
          >
            刷新
          </el-button>
        </template>

        <RequestTimeline
          :requests="requests"
          :current-user-id="sessionStore.user?.id"
          :is-admin="Boolean(sessionStore.user?.is_admin)"
          embedded
          @refresh="loadRequests"
          @edit="startEditing"
        />
      </ResultsCard>
    </template>
  </DetectionPageBase>
</template>

<script setup lang="ts">
import DetectionPageBase from '@/features/detection/components/DetectionPageBase.vue';
import DetectionConfig from '@/features/detection/components/DetectionConfig.vue';
import ProbeNodeSelector from '@/features/detection/components/ProbeNodeSelector.vue';
import ResultsCard from '@/features/detection/components/ResultsCard.vue';
import RequestTimeline from '../components/RequestTimeline.vue';
import { useMonitoringRequestPage } from '@/features/monitoring/composables/useMonitoringRequestPage';

const {
  alertContactsText,
  canSubmit,
  cancelEditing,
  editingRequestId,
  editingRequestStatus,
  error,
  expectedStatusCodes,
  expectedStatusInput,
  form,
  frequencyOptions,
  handleHeaderRefresh,
  loadRequests,
  handleSubmit,
  handleUpdate,
  headerRefreshing,
  isCertificateProtocol,
  loadProbes,
  normalizeExpectedStatusInput,
  probes,
  probesLoading,
  protocolOptions,
  requests,
  sessionStore,
  startEditing,
  submitting,
  success,
  systemOptions,
  systemsLoading,
  targetPlaceholder,
} = useMonitoringRequestPage();
</script>

<style scoped>
@import '../../detection/styles/detection-common.scss';

.mb-4 {
  margin-bottom: 16px;
}

.request-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.protocol-combo {
  display: flex;
  align-items: stretch;
  flex: 1;
  min-width: min(520px, 100%);
  border-radius: var(--oa-radius-md);
  background: var(--oa-bg-panel);
  box-shadow: 0 0 0 1px var(--oa-border-color) inset;
  transition: box-shadow 0.2s ease;
  overflow: hidden;
}

.protocol-combo:hover {
  box-shadow: 0 0 0 1px var(--oa-text-muted) inset;
}

.protocol-combo:focus-within {
  box-shadow: 0 0 0 2px var(--oa-color-primary-light) inset;
}

.protocol-combo__select {
  width: 140px;
  flex: 0 0 auto;
}

.protocol-combo :deep(.protocol-combo__select .el-select__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: var(--oa-radius-md) 0 0 var(--oa-radius-md);
  border-right: 1px solid var(--oa-border-color);
  min-height: 44px;
}

.protocol-combo__input {
  flex: 1;
  min-width: 0;
}

.protocol-combo :deep(.protocol-combo__input .el-input__wrapper),
.protocol-combo :deep(.protocol-combo__input .el-input__wrapper:hover),
.protocol-combo :deep(.protocol-combo__input .el-input__wrapper.is-focus) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 var(--oa-radius-md) var(--oa-radius-md) 0;
  min-height: 44px;
}

.hint-text--block {
  display: block;
  margin-left: 0;
  margin-top: 8px;
}

.inline-field {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.submit-row {
  display: flex;
  justify-content: center;
  width: 100%;
}
</style>
