<template>
  <PageWrapper :loading="loading">
    <RepositoryPageShell
      root-title="监控与告警"
      section-title="告警事件"
      body-padding="0"
      :panel-bordered="false"
    >
      <template #actions>
        <div class="alerts-header__right">
          <div
            class="refresh-card"
            @click="loadEvents"
          >
            <el-icon
              class="refresh-icon"
              :class="{ spinning: loading }"
            >
              <Refresh />
            </el-icon>
            <span>刷新</span>
          </div>
        </div>
      </template>

      <div class="oa-list-page">
        <div class="page-toolbar page-toolbar--panel">
          <div class="page-toolbar__left" />
          <div class="page-toolbar__right">
            <el-select
              v-model="severityFilter"
              class="pill-input narrow-select"
              placeholder="告警级别"
              clearable
            >
              <el-option
                label="全部级别"
                value="all"
              />
              <el-option
                label="致命 (critical)"
                value="critical"
              />
              <el-option
                label="警告 (warning)"
                value="warning"
              />
              <el-option
                label="提示 (info)"
                value="info"
              />
            </el-select>
            <el-select
              v-model="notificationStatusFilter"
              class="pill-input narrow-select"
              placeholder="通知状态"
              clearable
            >
              <el-option
                label="全部通知状态"
                value="all"
              />
              <el-option
                label="待发送"
                value="pending"
              />
              <el-option
                label="发送中"
                value="sending"
              />
              <el-option
                label="已发送"
                value="sent"
              />
              <el-option
                label="发送失败"
                value="failed"
              />
              <el-option
                label="已抑制"
                value="suppressed"
              />
            </el-select>
            <el-input
              v-model="keyword"
              placeholder="搜索标题 / 关联对象 / 目标"
              clearable
              class="search-input pill-input search-input--compact"
            />
          </div>
        </div>

        <el-alert
          v-if="error"
          type="error"
          :closable="false"
          class="oa-inline-alert"
          show-icon
        >
          {{ error }}
        </el-alert>

        <div class="oa-table-panel">
          <div class="oa-table-panel__card">
            <el-table
              v-loading="loading"
              :data="filteredEvents"
              class="oa-table"
              height="100%"
              stripe
              empty-text="暂无告警事件"
            >
              <el-table-column
                label="关联对象"
                min-width="180"
              >
                <template #default="{ row }">
                  <span class="oa-table-title">{{ row.objectName }}</span>
                </template>
              </el-table-column>

              <el-table-column
                label="目标"
                min-width="220"
              >
                <template #default="{ row }">
                  <span class="oa-table-meta">{{ row.targetText }}</span>
                </template>
              </el-table-column>

              <el-table-column
                prop="severity"
                label="告警级别"
                width="120"
              >
                <template #default="{ row }">
                  <el-tag
                    :type="severityTagType(row.severity)"
                    size="small"
                    effect="plain"
                  >
                    {{ severityLabel(row.severity) }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column
                label="通知对象"
                min-width="180"
              >
                <template #default="{ row }">
                  <span class="oa-table-meta">{{ row.contactsText }}</span>
                </template>
              </el-table-column>

              <el-table-column
                prop="status"
                label="通知状态"
                width="120"
              >
                <template #default="{ row }">
                  <el-tag
                    :type="statusTagType(row.status)"
                    size="small"
                    effect="plain"
                  >
                    {{ statusLabel(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column
                prop="created_at"
                label="告警时间"
                width="200"
              >
                <template #default="{ row }">
                  <span class="oa-table-meta">
                    {{ formatDate(row.created_at) || '—' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                label="操作"
                width="120"
                fixed="right"
              >
                <template #default="{ row }">
                  <el-button
                    text
                    size="small"
                    class="oa-table-action oa-table-action--primary"
                    @click.stop="handleDetail(row)"
                  >
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="oa-panel-footer">
          <div class="oa-panel-footer__left">
            <div class="oa-panel-stats">
              共 {{ filteredEvents.length }} 条（最多展示最近 100 条）
            </div>
          </div>
        </div>
      </template>
    </RepositoryPageShell>
  </PageWrapper>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Refresh } from '@element-plus/icons-vue';

import PageWrapper from '@/shared/components/layout/PageWrapper';
import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';
import type { AlertEventRecord } from '@/features/alerts/api/alertsApi';
import { fetchAlertEvents } from '@/features/alerts/api/alertsApi';

type EventListRow = AlertEventRecord & {
  objectName: string;
  targetText: string;
  contactsText: string;
};

const router = useRouter();
const events = ref<AlertEventRecord[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const keyword = ref('');
const severityFilter = ref<'all' | 'critical' | 'warning' | 'info'>('all');
const notificationStatusFilter = ref<
  'all' | 'pending' | 'sending' | 'sent' | 'failed' | 'suppressed'
>('all');

const loadEvents = async () => {
  loading.value = true;
  error.value = null;
  try {
    events.value = await fetchAlertEvents();
  } catch (err) {
    error.value = '无法加载告警事件，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

const listRows = computed<EventListRow[]>(() =>
  events.value.map((event) => {
    const context = (event.context || {}) as Record<string, unknown>;
    const objectName = pickContextText(
      context,
      ['schedule_name', 'request_title', 'check_name', 'title'],
      '未关联对象',
    );
    const targetText =
      typeof context.target === 'string' && context.target.trim()
        ? context.target
        : '未提供目标';
    const contactsText = Array.isArray(context.alert_contacts)
      ? context.alert_contacts
        .filter((item): item is string => typeof item === 'string' && !!item.trim())
        .join(', ') || '未配置'
      : typeof context.alert_contacts === 'string' && context.alert_contacts.trim()
        ? context.alert_contacts
        : '未配置';

    return {
      ...event,
      objectName,
      targetText,
      contactsText
    };
  })
);

const filteredEvents = computed(() => {
  const k = keyword.value.trim().toLowerCase();
  const sev = severityFilter.value;
  const notificationStatus = notificationStatusFilter.value;

  return listRows.value.filter((event) => {
    if (sev !== 'all' && event.severity.toLowerCase() !== sev) {
      return false;
    }
    if (notificationStatus !== 'all' && event.status.toLowerCase() !== notificationStatus) {
      return false;
    }
    if (!k) return true;
    const haystack =
      `${event.title} ${event.message} ${event.objectName} ${event.targetText} ${event.contactsText}`.toLowerCase();
    return haystack.includes(k);
  });
});

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

const pickContextText = (
  context: Record<string, unknown>,
  keys: string[],
  fallback: string,
) => {
  for (const key of keys) {
    const value = context[key];
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
  }
  return fallback;
};

const handleDetail = (row: AlertEventRecord) => {
  router.push({ name: 'alerts-event-detail', params: { eventId: row.id } });
};

onMounted(loadEvents);
</script>

<style scoped>
.alerts-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
