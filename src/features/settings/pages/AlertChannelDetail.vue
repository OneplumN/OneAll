<template>
  <div class="alert-channel-detail-view settings-detail-view">
    <SettingsPageShell
      section-title="通知管理"
      :breadcrumb="breadcrumb"
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
        <div
          class="refresh-card"
          @click="reloadAll"
        >
          <el-icon
            class="refresh-icon"
            :class="{ spinning: refreshLoading }"
          >
            <Refresh />
          </el-icon>
          <span>刷新</span>
        </div>
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
        v-if="channel"
        class="oa-detail-page"
      >
        <div class="oa-detail-header">
          <div class="oa-detail-header__left">
            <div class="oa-detail-title">
              {{ channel.name }}
            </div>
            <div class="oa-detail-meta">
              <span>{{ channelTypeMap[channel.type] || channel.type }}</span>
              <span class="sep">·</span>
              <span>{{ channel.type }}</span>
              <span
                v-if="channel.last_test_at"
                class="sep"
              >·</span>
              <span v-if="channel.last_test_at">最近测试 {{ formatDate(channel.last_test_at) }}</span>
              <span
                v-if="channel.description"
                class="sep"
              >·</span>
              <span v-if="channel.description">{{ channel.description }}</span>
            </div>
          </div>
          <div class="oa-detail-header__actions">
            <el-tag
              :type="statusTagType(channel)"
              effect="plain"
              size="small"
            >
              {{ statusCopy(channel) }}
            </el-tag>
          </div>
        </div>

        <div class="oa-detail-scroll">
          <el-card
            shadow="never"
            class="oa-detail-card oa-detail-card--narrow settings-detail-card"
          >
            <AlertChannelConfigPanel
              v-model:form="channel.form"
              :disabled="!channel.enabled || saving"
              :is-script-channel="isScriptChannel"
              :template-loading="templateLoading"
              :templates-for-channel="templatesForChannel"
              :config-schema="channel.config_schema"
              :script-repository="scriptRepository"
              :script-versions="scriptVersions"
              :script-versions-loading="scriptVersionsLoading"
              :format-date="formatDate"
              :format-version-label="formatVersionLabel"
              @go-templates="goTemplatesWithFilter"
              @open-script-dialog="openScriptDialog"
              @clear-script-selection="clearScriptSelection"
            />
          </el-card>
        </div>
      </div>

      <div
        v-else
        class="empty-view"
      >
        <el-empty description="未找到通道" />
      </div>

      <template
        v-if="channel"
        #footer
      >
        <div class="channel-footer settings-detail-footer-row">
          <div class="channel-footer__left settings-detail-footer-row__meta">
            <span class="channel-footer__label">启用</span>
            <el-switch
              :loading="enabling"
              :model-value="channel.enabled"
              @update:model-value="toggleEnabled"
            />
          </div>
          <div class="oa-detail-footer">
            <el-button
              :disabled="!channel.enabled"
              :loading="testing"
              @click="handleTest"
            >
              测试
            </el-button>
            <el-button
              type="primary"
              :loading="saving"
              @click="handleSave"
            >
              保存
            </el-button>
          </div>
        </div>
      </template>
    </SettingsPageShell>

    <ScriptSelectorDialog
      v-model="scriptDialogVisible"
      :selected-id="isScriptChannel ? channel?.form.repository_id : undefined"
      @select="handleScriptSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue';

import ScriptSelectorDialog from '@/shared/components/scripts/ScriptSelectorDialog.vue';
import AlertChannelConfigPanel from '@/features/settings/components/AlertChannelConfigPanel.vue';
import { useAlertChannelDetailPage } from '@/features/settings/composables/useAlertChannelDetailPage';
import SettingsPageShell from '@/features/settings/components/SettingsPageShell.vue';
const {
  channelTypeMap,
  channel,
  error,
  saving,
  enabling,
  testing,
  templateLoading,
  scriptDialogVisible,
  scriptRepository,
  scriptVersions,
  scriptVersionsLoading,
  breadcrumb,
  refreshLoading,
  isScriptChannel,
  templatesForChannel,
  reloadAll,
  goBack,
  goTemplatesWithFilter,
  openScriptDialog,
  handleScriptSelected,
  clearScriptSelection,
  formatVersionLabel,
  formatDate,
  statusTagType,
  statusCopy,
  toggleEnabled,
  handleSave,
  handleTest,
} = useAlertChannelDetailPage();
</script>

<style scoped>
@import '../styles/settings-detail.scss';

.alert-channel-detail-view {
  height: 100%;
  min-height: 0;
}

.channel-footer {
  gap: 16px;
}

.channel-footer__label {
  font-size: var(--oa-font-subtitle);
  color: var(--oa-text-secondary);
}

@media (max-width: 960px) {
  .channel-footer__left {
    justify-content: center;
  }
}

.empty-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.sep {
  color: var(--oa-text-muted);
}

</style>
