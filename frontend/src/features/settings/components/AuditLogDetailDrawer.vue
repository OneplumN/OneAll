<template>
  <el-drawer
    v-model="visibleModel"
    title="日志详情"
    size="560px"
    append-to-body
    destroy-on-close
  >
    <div
      v-if="log"
      class="oa-drawer-body"
    >
      <el-descriptions
        :column="1"
        border
        size="small"
      >
        <el-descriptions-item label="时间">
          {{ formatDate(log.occurred_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="操作者">
          <span v-if="log.actor">
            {{ log.actor.display_name || log.actor.username }}
            <span
              v-if="log.actor.username && log.actor.display_name"
              class="oa-table-meta"
            >
              （{{ log.actor.username }}）
            </span>
          </span>
          <span v-else>系统</span>
        </el-descriptions-item>
        <el-descriptions-item label="操作">
          {{ log.action }}
        </el-descriptions-item>
        <el-descriptions-item label="目标">
          {{ log.target_type || '—' }}{{ log.target_id ? ` / ${log.target_id}` : '' }}
        </el-descriptions-item>
        <el-descriptions-item label="结果">
          <el-tag
            :type="tagType(log.result)"
            size="small"
          >
            {{ log.result }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div class="oa-drawer-section">
        <div class="oa-drawer-section__title">
          操作上下文
        </div>
        <p class="settings-detail-drawer-note">
          用于记录该次操作的原始上下文信息，便于审计和排查。
        </p>
        <pre class="oa-code-block">{{ formatJson(log.metadata) }}</pre>
      </div>
    </div>
    <template #footer>
      <div class="oa-drawer-footer">
        <el-button @click="visibleModel = false">
          关闭
        </el-button>
        <el-button
          type="primary"
          plain
          :disabled="!log"
          @click="emit('copy')"
        >
          复制详情
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import type { AuditLogEntry } from '@/features/settings/api/settingsApi';

const visibleModel = defineModel<boolean>('visible', { required: true });

defineProps<{
  log: AuditLogEntry | null;
  formatDate: (value: string) => string;
  tagType: (result: string) => string;
  formatJson: (value: unknown) => string;
}>();

const emit = defineEmits<{
  (event: 'copy'): void;
}>();
</script>
