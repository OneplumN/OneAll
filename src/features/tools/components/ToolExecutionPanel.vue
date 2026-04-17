<template>
  <el-card
    shadow="never"
    class="card execution-card"
    :body-style="{ padding: '0' }"
  >
    <template #header>
      <div class="card-head">
        <div>
          <div class="card-title">
            执行中心
          </div>
          <div class="card-subtitle">
            仅展示本次同步的状态、run_id 与实时日志。
          </div>
        </div>
        <div class="card-meta">
          <el-tag
            v-if="currentExecution"
            size="small"
            effect="plain"
            :type="statusTagType(currentExecution.status)"
          >
            本次：{{ statusText(currentExecution.status) }}
          </el-tag>
          <el-tag
            v-else-if="currentRunId"
            size="small"
            effect="plain"
            type="info"
          >
            本次：已触发
          </el-tag>
          <el-button
            size="small"
            text
            :disabled="!currentRunId"
            :loading="executionsLoading"
            @click="emit('refresh')"
          >
            刷新日志
          </el-button>
        </div>
      </div>
    </template>

    <div class="execution-live">
      <template v-if="currentRunId">
        <template v-if="currentExecution">
          <div class="execution-head">
            <div class="execution-head__meta">
              <el-tag
                size="small"
                effect="plain"
                :type="statusTagType(currentExecution.status)"
              >
                {{ statusText(currentExecution.status) }}
              </el-tag>
              <span class="mono">run_id: {{ currentExecution.run_id }}</span>
              <span class="muted">{{ formatTime(currentExecution.finished_at || currentExecution.created_at || '') }}</span>
            </div>
            <el-button
              text
              :icon="DocumentCopy"
              @click="emit('copyRunId', String(currentExecution.run_id))"
            >
              复制 run_id
            </el-button>
          </div>
          <el-alert
            v-if="currentExecution.error_message"
            type="error"
            show-icon
            :closable="false"
            class="mt-12"
          >
            {{ currentExecution.error_message }}
          </el-alert>
          <el-divider />
          <div class="terminal">
            <div class="terminal__toolbar">
              <div class="terminal__toolbar-left">
                <span class="terminal__title">执行日志</span>
                <span
                  v-if="isRunningStatus(currentExecution.status)"
                  class="terminal__badge terminal__badge--running"
                >实时</span>
                <span
                  v-else
                  class="terminal__badge"
                >本次</span>
              </div>
              <div class="terminal__toolbar-actions">
                <el-button
                  text
                  size="small"
                  :type="logAutoFollow ? 'primary' : 'info'"
                  @click="emit('toggleFollow')"
                >
                  跟随
                </el-button>
                <el-button
                  text
                  size="small"
                  :type="logWrap ? 'primary' : 'info'"
                  @click="emit('toggleWrap')"
                >
                  换行
                </el-button>
                <el-button
                  text
                  size="small"
                  :icon="DocumentCopy"
                  @click="emit('copyLog', visibleLogOutput)"
                >
                  复制
                </el-button>
                <el-button
                  text
                  size="small"
                  :icon="Download"
                  @click="emit('downloadLog')"
                >
                  下载
                </el-button>
                <el-button
                  text
                  size="small"
                  type="danger"
                  @click="emit('clearLog')"
                >
                  清空
                </el-button>
              </div>
            </div>
            <el-scrollbar
              ref="localScrollbarRef"
              class="terminal__body"
              @scroll="emit('scroll')"
            >
              <pre
                v-if="visibleLogOutput"
                class="terminal__output mono"
                :class="{ 'terminal__output--wrap': logWrap }"
              >{{ visibleLogOutput }}</pre>
              <div
                v-else
                class="terminal__empty"
              >
                无输出
              </div>
            </el-scrollbar>
          </div>
        </template>
        <el-empty
          v-else
          description="任务已触发，正在等待执行记录创建…"
        />
      </template>
      <el-empty
        v-else
        description="点击“立即同步”开始"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { DocumentCopy, Download } from '@element-plus/icons-vue';
import { ref, watchEffect } from 'vue';

type ExecutionRecord = {
  id: string | number;
  run_id: string | number;
  status: string;
  created_at?: string;
  finished_at?: string | null;
  error_message?: string | null;
};

defineProps<{
  currentExecution: ExecutionRecord | null;
  currentRunId: string | null;
  executionsLoading: boolean;
  statusTagType: (status: string) => string;
  statusText: (status: string) => string;
  formatTime: (value: string) => string;
  isRunningStatus: (status?: string) => boolean;
  logAutoFollow: boolean;
  logWrap: boolean;
  visibleLogOutput: string;
}>();

const scrollbarRefModel = defineModel<unknown>('scrollbarRef');
const localScrollbarRef = ref<unknown>(null);

const emit = defineEmits<{
  (event: 'refresh'): void;
  (event: 'copyRunId', value: string): void;
  (event: 'toggleFollow'): void;
  (event: 'toggleWrap'): void;
  (event: 'copyLog', value: string): void;
  (event: 'downloadLog'): void;
  (event: 'clearLog'): void;
  (event: 'scroll'): void;
}>();

watchEffect(() => {
  scrollbarRefModel.value = localScrollbarRef.value;
});
</script>

<style scoped>
.card {
  border-radius: 16px;
  border: 1px solid var(--oa-border-light);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.card-title {
  font-weight: 700;
  color: var(--oa-text-primary);
}

.card-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.execution-card :deep(.el-card__body) {
  height: 100%;
}

.execution-live {
  min-width: 0;
  padding: 12px 12px 12px 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 520px;
}

.mono {
  font-family: 'JetBrains Mono', Consolas, 'Courier New', monospace;
}

.execution-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.execution-head__meta {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.muted {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.mt-12 {
  margin-top: 12px;
}

.terminal {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: #1e1e1e;
}

.terminal__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(255, 255, 255, 0.03);
}

.terminal__toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.terminal__title {
  font-size: 12px;
  font-weight: 600;
  color: rgba(226, 232, 240, 0.92);
}

.terminal__badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.14);
  color: rgba(226, 232, 240, 0.75);
}

.terminal__badge--running {
  background: rgba(34, 197, 94, 0.18);
  color: rgba(134, 239, 172, 0.95);
}

.terminal__toolbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.terminal__toolbar-actions :deep(.el-button) {
  padding: 0 8px;
  height: 28px;
}

.terminal__body {
  flex: 1;
  min-height: 0;
  padding: 10px 12px;
}

.terminal__output {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: rgba(226, 232, 240, 0.92);
  white-space: pre;
  word-break: normal;
}

.terminal__output--wrap {
  white-space: pre-wrap;
  word-break: break-word;
}

.terminal__empty {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.85);
}
</style>
