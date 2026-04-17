<template>
  <el-drawer
    v-model="visibleModel"
    title="绑定角色模板"
    size="520px"
    append-to-body
    destroy-on-close
  >
    <div
      v-if="user"
      class="oa-drawer-body"
    >
      <div class="oa-drawer-card">
        <div class="oa-drawer-section__title">
          基本信息
        </div>
        <el-descriptions
          :column="2"
          border
          size="small"
        >
          <el-descriptions-item label="账号">
            {{ user.username }}
          </el-descriptions-item>
          <el-descriptions-item label="邮箱">
            {{ user.email || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="认证来源">
            {{ user.auth_source || 'local' }}
          </el-descriptions-item>
          <el-descriptions-item label="LDAP 同步时间">
            {{ user.external_synced_at ? formatSyncTime(user.external_synced_at) : '—' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="oa-drawer-card">
        <div class="oa-drawer-section__title">
          角色模板
        </div>
        <div class="oa-drawer-section__meta">
          每个用户仅可绑定一个角色模板，保存后立即生效。
        </div>
        <el-radio-group
          v-model="roleIdModel"
          class="role-list"
        >
          <el-radio
            :label="''"
            class="role-option"
          >
            <div class="role-option__content">
              <div class="role-option__name">
                未分配
              </div>
              <div class="role-option__desc">
                不授予任何权限
              </div>
            </div>
          </el-radio>
          <el-radio
            v-for="role in roles"
            :key="role.id"
            :label="role.id"
            class="role-option"
          >
            <div class="role-option__content">
              <div class="role-option__name">
                {{ role.name }}
              </div>
              <div class="role-option__desc">
                {{ role.description || '未提供描述' }}
              </div>
            </div>
          </el-radio>
        </el-radio-group>
      </div>
    </div>

    <template #footer>
      <div class="oa-drawer-footer">
        <span
          v-if="dirty"
          class="dirty-hint"
        >未保存更改</span>
        <el-button @click="emit('cancel')">
          取消
        </el-button>
        <el-button
          type="primary"
          :disabled="!dirty"
          :loading="saving"
          @click="emit('save')"
        >
          保存
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import type { RolePayload, UserRoleRecord } from '@/features/settings/api/settingsApi';

const visibleModel = defineModel<boolean>('visible', { required: true });
const roleIdModel = defineModel<string>('roleId', { required: true });

defineProps<{
  user: UserRoleRecord | null;
  roles: RolePayload[];
  dirty: boolean;
  saving: boolean;
  formatSyncTime: (value?: string | null) => string;
}>();

const emit = defineEmits<{
  (event: 'cancel'): void;
  (event: 'save'): void;
}>();
</script>

<style scoped>
.dirty-hint {
  margin-right: auto;
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-meta);
}

.role-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-option {
  width: 100%;
  margin-right: 0;
  border: 1px solid var(--oa-border-light);
  border-radius: 10px;
  padding: 12px 12px;
  background: rgba(255, 255, 255, 0.7);
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.role-option:hover {
  border-color: rgba(64, 158, 255, 0.35);
  background: rgba(64, 158, 255, 0.05);
}

.role-option :deep(.el-radio__label) {
  width: 100%;
}

.role-option__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.role-option__name {
  font-weight: 600;
  color: var(--oa-text-primary);
  font-size: var(--oa-font-base);
}

.role-option__desc {
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}
</style>
