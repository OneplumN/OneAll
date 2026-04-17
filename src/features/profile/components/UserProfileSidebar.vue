<template>
  <el-card
    shadow="never"
    class="profile-sidebar"
  >
    <div class="profile-hero profile-hero--sidebar">
      <el-avatar
        :size="52"
        class="profile-avatar"
      >
        {{ avatarText }}
      </el-avatar>
      <div class="profile-hero__main">
        <div class="profile-name">
          {{ profileDisplayName }}
        </div>
        <div class="profile-sub">
          <span v-if="profile?.username">账号：{{ profile.username }}</span>
          <span class="dot">·</span>
          <el-tag
            size="small"
            effect="plain"
          >
            {{ authSourceLabel }}
          </el-tag>
        </div>
        <div class="profile-role">
          <div class="meta-label">
            当前角色
          </div>
          <el-tag
            size="small"
            effect="plain"
            type="info"
          >
            {{ primaryRoleName }}
          </el-tag>
        </div>
      </div>
    </div>

    <el-divider />

    <div class="profile-quick profile-quick--stack">
      <div class="quick-item">
        <div class="quick-label">
          显示名称
        </div>
        <div class="quick-value">
          {{ profile?.display_name || '-' }}
        </div>
      </div>
      <div class="quick-item">
        <div class="quick-label">
          邮箱
        </div>
        <div class="quick-value">
          {{ profile?.email || '-' }}
        </div>
      </div>
      <div class="quick-item">
        <div class="quick-label">
          手机号
        </div>
        <div class="quick-value">
          {{ profile?.phone || '-' }}
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { ProfileRecord } from '@/features/profile/api/profileApi';

defineProps<{
  profile: ProfileRecord | null;
  avatarText: string;
  profileDisplayName: string;
  authSourceLabel: string;
  primaryRoleName: string;
}>();
</script>

<style scoped>
.profile-sidebar :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-hero {
  display: flex;
  align-items: center;
  gap: 14px;
}

.profile-hero--sidebar {
  align-items: flex-start;
}

.profile-avatar {
  background: color-mix(in srgb, var(--oa-color-primary) 20%, var(--oa-bg-panel));
  color: var(--oa-color-primary);
  font-weight: 700;
}

.profile-hero__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.profile-name {
  font-size: var(--oa-font-heading);
  font-weight: 700;
  color: var(--oa-text-primary);
}

.profile-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--oa-text-secondary);
  flex-wrap: wrap;
}

.profile-sub .dot {
  color: var(--oa-text-muted);
}

.profile-role {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-label {
  font-size: var(--oa-font-meta);
  color: var(--oa-text-muted);
}

.profile-quick {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.profile-quick--stack {
  grid-template-columns: 1fr;
}

.quick-item {
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  padding: 10px 12px;
  background: var(--oa-bg-muted);
  min-height: 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.quick-label {
  font-size: var(--oa-font-meta);
  color: var(--oa-text-muted);
}

.quick-value {
  font-weight: 600;
  color: var(--oa-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
