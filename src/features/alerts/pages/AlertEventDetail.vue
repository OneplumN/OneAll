<template>
  <RepositoryPageShell
    root-title="告警事件"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <el-button
        class="toolbar-button"
        @click="goBack"
      >
        返回列表
      </el-button>
    </template>

    <el-alert
      v-if="error"
      type="error"
      :closable="false"
      class="oa-inline-alert"
      show-icon
    >
      {{ error }}
    </el-alert>

    <div
      v-if="event"
      class="oa-detail-page"
    >
      <div class="oa-detail-header">
        <div class="oa-detail-header__left">
          <div class="oa-detail-title">
            {{ event.title || '告警事件' }}
          </div>
          <div class="oa-detail-meta">
            <span>{{ contextObjectName }}</span>
            <span class="sep">·</span>
            <span>{{ contextTarget }}</span>
            <span class="sep">·</span>
            <span>{{ createdAtText }}</span>
          </div>
        </div>
        <div class="oa-detail-header__actions">
          <el-tag
            :type="severityTagType(event.severity)"
            size="small"
            effect="plain"
          >
            {{ severityLabel(event.severity) }}
          </el-tag>
          <el-tag
            :type="statusTagType(event.status)"
            size="small"
            effect="plain"
          >
            {{ statusLabel(event.status) }}
          </el-tag>
        </div>
      </div>

      <div class="oa-detail-scroll">
        <div class="event-sheet">
          <section class="detail-section">
            <h2 class="oa-section-title detail-section__title">
              告警信息
            </h2>
            <div class="detail-grid">
              <div class="detail-line detail-line--full detail-line--framed">
                <div class="detail-item detail-item--full detail-item--headline">
                  <span class="detail-item__label">告警标题：</span>
                  <span class="detail-item__value detail-item__value--title">
                    {{ event.title || '-' }}
                  </span>
                </div>
              </div>

              <div class="detail-line detail-line--full detail-line--framed">
                <div class="detail-item detail-item--full detail-item--multiline">
                  <span class="detail-item__label">告警内容：</span>
                  <span class="detail-item__value detail-item__value--message">
                    {{ displayMessage }}
                  </span>
                </div>
              </div>

              <div class="detail-line detail-line--framed">
                <div class="detail-item">
                  <span class="detail-item__label">告警级别：</span>
                  <span class="detail-item__value">
                    <el-tag
                      :type="severityTagType(event.severity)"
                      size="small"
                      effect="plain"
                    >
                      {{ severityLabel(event.severity) }}
                    </el-tag>
                  </span>
                </div>
                <div class="detail-item">
                  <span class="detail-item__label">通知状态：</span>
                  <span class="detail-item__value">
                    <el-tag
                      :type="statusTagType(event.status)"
                      size="small"
                      effect="plain"
                    >
                      {{ statusLabel(event.status) }}
                    </el-tag>
                  </span>
                </div>
              </div>

              <div class="detail-line detail-line--framed">
                <div class="detail-item">
                  <span class="detail-item__label">告警时间：</span>
                  <span class="detail-item__value detail-item__value--time">{{ createdAtText }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-item__label">通知发送时间：</span>
                  <span class="detail-item__value detail-item__value--time">{{ sentAtText }}</span>
                </div>
              </div>
            </div>
          </section>

          <section class="detail-section">
            <h2 class="oa-section-title detail-section__title">
              对象信息
            </h2>
            <div class="detail-grid">
              <div class="detail-line detail-line--framed">
                <div class="detail-item">
                  <span class="detail-item__label">目标：</span>
                  <span class="detail-item__value">{{ contextTarget }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-item__label">状态码：</span>
                  <span class="detail-item__value detail-item__value--metric">{{ contextStatusCode }}</span>
                </div>
              </div>

              <div class="detail-line detail-line--framed">
                <div class="detail-item">
                  <span class="detail-item__label">关联对象：</span>
                  <span class="detail-item__value">{{ contextObjectName }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-item__label">关联探针：</span>
                  <span class="detail-item__value">{{ contextProbeName }}</span>
                </div>
              </div>

              <div class="detail-line detail-line--framed">
                <div class="detail-item">
                  <span class="detail-item__label">连续失败次数：</span>
                  <span class="detail-item__value detail-item__value--metric">{{ contextThreshold }}</span>
                </div>
                <div class="detail-item detail-item--empty" />
              </div>
            </div>
          </section>

          <section class="detail-section">
            <h2 class="oa-section-title detail-section__title">
              通知信息
            </h2>
            <div class="detail-grid">
              <div class="detail-line detail-line--framed">
                <div class="detail-item">
                  <span class="detail-item__label">通知对象：</span>
                  <span class="detail-item__value">{{ contextContacts }}</span>
                </div>
                <div class="detail-item detail-item--empty" />
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import type { AlertEventRecord } from '@/features/alerts/api/alertsApi';
import { fetchAlertEvents } from '@/features/alerts/api/alertsApi';

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const error = ref<string | null>(null);
const event = ref<AlertEventRecord | null>(null);

const goBack = () => {
  router.push({ name: 'alerts-events' });
};

const loadDetail = async () => {
  loading.value = true;
  error.value = null;
  try {
    const eventId = route.params.eventId as string;
    const list = await fetchAlertEvents();
    const found = list.find((item) => item.id === eventId) || null;
    if (!found) {
      error.value = '未找到该告警事件，可能已过期或被清理。';
      ElMessage.error(error.value);
      return;
    }
    event.value = found;
  } catch (err) {
    error.value = '无法加载告警详情，请稍后重试。';
    ElMessage.error(error.value);
  } finally {
    loading.value = false;
  }
};

const formatDate = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

const severityTagType = (severity: string) => {
  const s = severity.toLowerCase();
  if (s === 'critical') return 'danger';
  if (s === 'warning') return 'warning';
  if (s === 'info') return 'info';
  return '';
};

const severityLabel = (severity: string) => {
  const s = severity.toLowerCase();
  if (s === 'critical') return '致命';
  if (s === 'warning') return '警告';
  if (s === 'info') return '提示';
  return severity || '未知';
};

const statusTagType = (status: string) => {
  const s = status.toLowerCase();
  if (s === 'pending' || s === 'sending') return 'warning';
  if (s === 'sent') return 'success';
  if (s === 'failed') return 'danger';
  if (s === 'suppressed') return 'info';
  return '';
};

const statusLabel = (status: string) => {
  const s = status.toLowerCase();
  if (s === 'pending') return '待发送';
  if (s === 'sending') return '发送中';
  if (s === 'sent') return '已发送';
  if (s === 'failed') return '发送失败';
  if (s === 'suppressed') return '已抑制';
  return status || '未知';
};

const rawContext = computed<Record<string, any>>(
  () => ((event.value && (event.value.context as Record<string, any>)) || {}) as Record<string, any>,
);

const readContextString = (key: string, fallback: string) => {
  const value = rawContext.value[key];
  return typeof value === 'string' && value.trim() ? value : fallback;
};

const readContextStringByKeys = (keys: string[], fallback: string) => {
  for (const key of keys) {
    const value = rawContext.value[key];
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
  }
  return fallback;
};

const simplifyAlertMessage = (message: string, target: string) => {
  const text = message.trim();
  if (!text) return '-';

  const pickPrimaryLine = (value: string) => {
    const primary = value
      .split('\n')
      .map((line) => line.trim())
      .find(Boolean);
    return primary || value;
  };

  if (target && target !== '未提供目标') {
    const quotedPrefixPattern = new RegExp(`^[A-Za-z]+\\s+"${escapeRegExp(target)}":\\s*`);
    if (quotedPrefixPattern.test(text)) {
      return pickPrimaryLine(text.replace(quotedPrefixPattern, '').trim()) || text;
    }

    const plainPrefix = `${target}:`;
    if (text.startsWith(plainPrefix)) {
      return pickPrimaryLine(text.slice(plainPrefix.length).trim()) || text;
    }
  }

  const genericQuotedPrefixPattern = /^[A-Za-z]+\s+"[^"]+":\s*/;
  if (genericQuotedPrefixPattern.test(text)) {
    return pickPrimaryLine(text.replace(genericQuotedPrefixPattern, '').trim()) || text;
  }

  return pickPrimaryLine(text);
};

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const contextObjectName = computed(() =>
  readContextStringByKeys(['schedule_name', 'request_title', 'check_name', 'title'], '未关联对象'),
);
const contextProbeName = computed(() => readContextString('probe_name', '未关联探针'));
const contextTarget = computed(() => readContextString('target', '未提供目标'));
const contextThreshold = computed(() => {
  const value = rawContext.value.threshold;
  return typeof value === 'number' && Number.isFinite(value) ? value : 1;
});
const contextStatusCode = computed(
  () =>
    (rawContext.value.status_code as string | number | undefined) ??
      (rawContext.value.response_status as string | number | undefined) ??
      '-',
);
const contextContacts = computed(() => {
  const value = rawContext.value.alert_contacts;
  if (Array.isArray(value)) {
    return value.length ? value.join(', ') : '未配置';
  }
  if (typeof value === 'string') {
    return value.trim() || '未配置';
  }
  return '未配置';
});

const createdAtText = computed(() => formatDate(event.value?.created_at) || '-');
const sentAtText = computed(() =>
  event.value?.sent_at ? formatDate(event.value.sent_at) || '-' : '-'
);
const displayMessage = computed(() =>
  simplifyAlertMessage(event.value?.message || '', contextTarget.value)
);

onMounted(loadDetail);
</script>

<style scoped>
.event-sheet {
  width: 100%;
  max-width: 1024px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 8px 0 14px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-section__title {
  padding-left: 10px;
  border-left: 4px solid var(--oa-color-primary-light);
}

.detail-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
  border-top: 1px solid var(--oa-border-light);
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.detail-line {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 40px;
}

.detail-line--full {
  grid-template-columns: 1fr;
}

.detail-line--framed {
  padding: 16px 0;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.detail-line--framed:first-child {
  border-top: none;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
  font-size: var(--oa-font-base);
  line-height: 1.7;
}

.detail-item--full {
  width: 100%;
}

.detail-item--headline {
  padding-bottom: 2px;
}

.detail-item--multiline {
  align-items: flex-start;
}

.detail-item--empty {
  visibility: hidden;
}

.detail-item__label {
  flex: 0 0 128px;
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-base);
  font-weight: 500;
  line-height: 1.7;
  letter-spacing: 0.02em;
}

.detail-item__value {
  min-width: 0;
  color: var(--oa-text-primary);
  flex: 1 1 auto;
  font-size: var(--oa-font-base);
  line-height: 1.7;
  word-break: break-word;
}

.detail-item__value--title {
  font-size: var(--oa-font-section-title);
  font-weight: 600;
  line-height: 1.55;
}

.detail-item__value--message {
  line-height: 1.75;
  white-space: pre-wrap;
  font-size: var(--oa-font-base);
}

.detail-item__value--metric {
  font-weight: 600;
  color: var(--oa-text-primary);
}

.detail-item__value--time {
  color: var(--oa-text-secondary);
}

.sep {
  color: var(--oa-text-muted);
}

@media (max-width: 900px) {
  .detail-line {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .detail-line--framed {
    padding: 12px 0;
  }

  .detail-item__label {
    flex-basis: 112px;
    font-size: var(--oa-font-base);
  }

  .detail-item__value {
    font-size: var(--oa-font-base);
  }
}
</style>
