<template>
  <div class="oneoff-page">
    <DetectionPageBase
      title="域名拨测"
      :error="submissionError"
      refreshable
      :refreshing="headerRefreshing"
      refresh-text="刷新"
      @refresh="handleHeaderRefresh"
    >
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
            :placeholder="targetPlaceholder"
            :disabled="submitting"
            clearable
            @keyup.enter="handleSubmit"
          />
        </div>
      </template>

      <template #config>
        <div class="detection-grid">
          <ProbeNodeSelector
            v-model="selectedNodeIds"
            :nodes="nodes"
            :loading="nodesLoading"
            embedded
            hint="可多选节点，将依次在各节点执行拨测。"
            @refresh="loadNodes"
          />

          <DetectionConfig
            title="高级配置"
            embedded
          >
            <template #config-items>
              <TimeoutSlider
                v-model="detectionConfig.timeout_seconds"
                :min="1"
                :max="60"
              />

              <div
                v-if="isHttpConfig"
                class="config-item config-item--row"
              >
                <span class="config-item__label">允许重定向</span>
                <el-switch v-model="httpConfig.follow_redirects" />
              </div>
              <div
                v-else
                class="config-item config-item--row"
              >
                <span class="config-item__label">端口</span>
                <el-input-number
                  v-model="tcpConfig.port"
                  :min="1"
                  :max="65535"
                />
              </div>
            </template>
          </DetectionConfig>
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
            立即检测
          </el-button>
        </div>
      </template>

      <template #content>
        <DetectionResults
          title="检测结果"
          :data="logs"
          :loading="submitting && !logs.length"
          :can-clear="logs.length > 0 || pendingTaskList.length > 0"
          @clear="clearLogs"
        >
          <template
            v-if="pendingTaskList.length"
            #description
          >
            <div class="batch-progress">
              <div class="batch-progress__summary">
                <span class="batch-progress__title">{{ batchProgressTitle }}</span>
                <span class="batch-progress__meta">{{ pendingSummaryText }}</span>
              </div>
              <div class="batch-progress__items">
                <div
                  v-for="item in visiblePendingTaskList"
                  :key="item.id"
                  class="batch-progress__item"
                >
                  <span class="batch-progress__node">{{ item.nodeName }}</span>
                  <el-tag
                    :type="getStatusTagType(item.status)"
                    effect="plain"
                    size="small"
                  >
                    {{ getStatusText(item.status) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </template>

          <template
            v-if="pollingError"
            #notice
          >
            <el-alert
              :type="stoppedDueToError ? 'error' : 'warning'"
              :closable="false"
              show-icon
            >
              {{ pollingError }}
            </el-alert>
          </template>

          <template
            v-if="!logs.length && !pendingTaskList.length && !submitting"
            #title-extra
          >
            支持 HTTP(S) / WebSocket / Telnet；可多选节点并行执行，本页仅保留本次批次结果
          </template>

          <template #columns>
            <el-table-column
              prop="executed_at"
              label="时间"
              min-width="160"
            >
              <template #default="{ row }">
                {{ formatDate(row.executed_at) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="target"
              label="域名"
              min-width="220"
              show-overflow-tooltip
            />
            <el-table-column
              prop="protocol"
              label="类型"
              width="140"
            >
              <template #default="{ row }">
                {{ getProtocolLabel(row.protocol) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="nodes"
              label="节点"
              min-width="160"
            >
              <template #default="{ row }">
                <el-tag
                  v-if="row.nodes.length"
                  round
                  size="small"
                >
                  {{ row.nodes[0] }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column
              prop="response_time_ms"
              label="耗时"
              width="120"
            >
              <template #default="{ row }">
                {{ formatResponseTime(row.response_time_ms) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="status"
              label="状态"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  :type="getStatusTagType(row.status)"
                  effect="plain"
                  size="small"
                  class="status-tag"
                >
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-button
                  type="primary"
                  text
                  size="small"
                  @click="openLogDetail(row)"
                >
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </template>
        </DetectionResults>
      </template>
    </DetectionPageBase>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="detailVisible"
      title="拨测详情"
      size="560px"
      destroy-on-close
      append-to-body
      class="detail-drawer"
    >
      <div
        v-if="activeLog"
        class="detail-content"
      >
        <el-descriptions
          :column="1"
          size="small"
          border
        >
          <el-descriptions-item label="域名">
            {{ activeLog.target }}
          </el-descriptions-item>
          <el-descriptions-item label="拨测类型">
            {{
              getProtocolLabel(activeLog.protocol)
            }}
          </el-descriptions-item>
          <el-descriptions-item label="节点">
            {{ activeLog.nodes[0] || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            {{
              getStatusText(activeLog.status)
            }}
          </el-descriptions-item>
          <el-descriptions-item label="状态码">
            {{
              activeLog.status_code ?? '-'
            }}
          </el-descriptions-item>
          <el-descriptions-item label="耗时">
            {{
              formatResponseTime(activeLog.response_time_ms)
            }}
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">
            {{
              formatDate(activeLog.executed_at)
            }}
          </el-descriptions-item>
          <el-descriptions-item label="错误信息">
            {{
              activeLog.error_message || '-'
            }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <h4>拨测配置</h4>
          <el-empty
            v-if="!detailConfigEntries.length"
            description="无配置数据"
            :image-size="60"
          />
          <el-descriptions
            v-else
            :column="1"
            size="small"
          >
            <el-descriptions-item
              v-for="item in detailConfigEntries"
              :key="item.key"
              :label="item.label"
            >
              {{ item.value }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import ProbeNodeSelector from '../components/ProbeNodeSelector.vue';
import DetectionPageBase from '../components/DetectionPageBase.vue';
import DetectionConfig from '../components/DetectionConfig.vue';
import DetectionResults from '../components/DetectionResults.vue';
import TimeoutSlider from '../components/TimeoutSlider.vue';
import { useOneOffDetectionPage } from '../composables/useOneOffDetectionPage';
import {
  formatDate,
  formatResponseTime,
  getProtocolLabel,
  getStatusTagType,
  getStatusText,
} from '../mappers/detectionUtils';
const {
  form,
  protocolOptions,
  detectionConfig,
  submitting,
  headerRefreshing,
  submissionError,
  logs,
  detailVisible,
  activeLog,
  targetPlaceholder,
  selectedNodeIds,
  nodes,
  nodesLoading,
  loadNodes,
  httpConfig,
  tcpConfig,
  isHttpConfig,
  detailConfigEntries,
  pendingTaskList,
  visiblePendingTaskList,
  pollingError,
  stoppedDueToError,
  pendingSummaryText,
  batchProgressTitle,
  clearLogs,
  openLogDetail,
  handleSubmit,
  handleHeaderRefresh,
} = useOneOffDetectionPage();
</script>

<style scoped>
@import '../styles/detection-common.scss';

.protocol-combo {
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

.submit-row {
  display: flex;
  justify-content: center;
  width: 100%;
}

.submit-row__action {
  min-height: 44px;
  min-width: 140px;
}

.batch-progress {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 2px 0 4px;
}

.batch-progress__summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
}

.batch-progress__title {
  font-weight: 600;
  color: var(--oa-text-primary);
}

.batch-progress__meta {
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-meta);
}

.batch-progress__items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.batch-progress__item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--oa-border-light);
  background: var(--oa-bg-muted);
}

.batch-progress__node {
  color: var(--oa-text-primary);
  font-size: var(--oa-font-body);
}

@media (max-width: 768px) {
  .protocol-combo {
    min-width: auto;
    width: 100%;
  }
}
</style>
