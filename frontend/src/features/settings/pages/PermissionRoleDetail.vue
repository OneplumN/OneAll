<template>
  <div class="permission-role-detail-view settings-detail-view">
    <SettingsPageShell
      section-title="用户与权限"
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
            :class="{ spinning: loading }"
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

      <div class="oa-detail-page">
        <div class="oa-detail-header">
          <div class="oa-detail-header__left">
            <div class="oa-detail-title">
              {{ isCreate ? '新增角色模板' : originalRole?.name || '角色模板' }}
            </div>
            <div class="oa-detail-meta">
              <span v-if="!isCreate">用户数 {{ originalRole?.user_count ?? 0 }}</span>
              <span
                v-if="!isCreate"
                class="sep"
              >·</span>
              <span>保存后立即生效</span>
              <span
                v-if="dirty"
                class="sep"
              >·</span>
              <span
                v-if="dirty"
                class="dirty-hint"
              >未保存更改</span>
            </div>
          </div>
        </div>

        <div class="oa-detail-scroll">
          <div class="detail-grid settings-detail-grid">
            <el-card
              shadow="never"
              class="card oa-detail-card settings-detail-card"
            >
              <div class="oa-section-title">
                基本信息
              </div>
              <div class="oa-section-subtitle">
                用于展示与检索角色模板。
              </div>
              <el-form
                label-position="top"
                class="role-basic-form settings-detail-form"
              >
                <el-form-item
                  label="名称"
                  required
                >
                  <el-input
                    v-model="form.name"
                    placeholder="例如：运维管理员"
                  />
                </el-form-item>
                <el-form-item label="描述">
                  <el-input
                    v-model="form.description"
                    placeholder="可选"
                  />
                </el-form-item>
              </el-form>
            </el-card>

            <el-card
              shadow="never"
              class="card oa-detail-card settings-detail-card"
            >
              <div class="perm-head">
                <div>
                  <div class="oa-section-title">
                    功能权限
                  </div>
                  <div class="oa-section-subtitle">
                    模块可全选、全清，支持搜索与展开折叠。
                  </div>
                </div>
                <div class="perm-head__right">
                  <el-input
                    v-model="search"
                    placeholder="搜索模块或动作"
                    clearable
                    class="oa-input-lg"
                    @input="handleSearchInput"
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                </div>
              </div>

              <div class="perm-toolbar oa-soft-panel">
                <div class="toolbar-left">
                  <strong>权限目录</strong>
                </div>
                <div class="toolbar-actions">
                  <el-button
                    size="small"
                    text
                    @click="setAllModulesExpansion(true)"
                  >
                    全部展开
                  </el-button>
                  <el-divider direction="vertical" />
                  <el-button
                    size="small"
                    text
                    @click="setAllModulesExpansion(false)"
                  >
                    全部折叠
                  </el-button>
                </div>
              </div>

              <el-tree
                :key="treeRenderKey"
                class="perm-tree oa-soft-panel"
                :data="filteredTreeData"
                :props="treeProps"
                node-key="id"
                :default-expanded-keys="expandedKeys"
                :expand-on-click-node="false"
              >
                <template #default="{ data }">
                  <div
                    class="node-row"
                    :class="{ 'is-leaf': data.actions }"
                  >
                    <template v-if="!data.actions">
                      <strong class="module-title">{{ data.label }}</strong>
                      <div class="module-actions">
                        <el-button
                          text
                          size="small"
                          @click.stop="toggleModule(data.moduleKey, true)"
                        >
                          全选
                        </el-button>
                        <el-button
                          text
                          size="small"
                          @click.stop="toggleModule(data.moduleKey, false)"
                        >
                          全清
                        </el-button>
                      </div>
                    </template>
                    <template v-else>
                      <span class="child-label">{{ data.label }}</span>
                      <div class="action-group">
                        <el-checkbox
                          v-for="action in data.actions"
                          :key="action"
                          :label="formatActionLabel(action)"
                          :model-value="isChecked(data.moduleKey, data.childKey, action)"
                          @change="handleCheckboxChange(data.moduleKey, data.childKey, action, $event as boolean)"
                        />
                      </div>
                    </template>
                  </div>
                </template>
              </el-tree>
            </el-card>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="oa-detail-footer">
          <el-button
            v-if="!isCreate && originalRole"
            :disabled="saving || !dirty"
            @click="handleReset"
          >
            重置
          </el-button>
          <el-button
            v-if="!isCreate && originalRole"
            type="danger"
            plain
            :loading="deleting"
            @click="handleDelete"
          >
            删除
          </el-button>
          <el-button
            type="primary"
            :disabled="!dirty"
            :loading="saving"
            @click="handleSave"
          >
            保存
          </el-button>
        </div>
      </template>
    </SettingsPageShell>
  </div>
</template>

<script setup lang="ts">
import { Refresh, Search } from '@element-plus/icons-vue';
import SettingsPageShell from '@/features/settings/components/SettingsPageShell.vue';
import { usePermissionRoleDetailPage } from '@/features/settings/composables/usePermissionRoleDetailPage';

const {
  isCreate,
  loading,
  saving,
  deleting,
  error,
  originalRole,
  form,
  treeRenderKey,
  expandedKeys,
  search,
  treeProps,
  breadcrumb,
  dirty,
  filteredTreeData,
  formatActionLabel,
  handleSearchInput,
  setAllModulesExpansion,
  toggleModule,
  isChecked,
  handleCheckboxChange,
  reloadAll,
  goBack,
  handleReset,
  handleSave,
  handleDelete,
} = usePermissionRoleDetailPage();
</script>

<style scoped>
@import '../styles/settings-detail.scss';

.permission-role-detail-view {
  height: 100%;
  min-height: 0;
}

.dirty-hint {
  color: var(--el-color-warning);
}

.role-basic-form {
  margin-top: -2px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

@media (max-width: 1100px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}

.card {
  height: fit-content;
}

.perm-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.perm-head__right {
  min-width: 240px;
  max-width: 420px;
  width: 100%;
}

.perm-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  margin-bottom: 12px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.perm-tree {
  padding: 10px 14px;
}

.perm-tree :deep(.el-tree-node__content) {
  height: auto !important;
  align-items: flex-start !important;
  padding: 6px 0 !important;
}

.node-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  flex-wrap: wrap;
}

.node-row.is-leaf {
  align-items: flex-start;
  gap: 8px;
}

.module-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: var(--oa-font-base);
}

.module-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

.child-label {
  flex: 0 0 140px;
  font-weight: 500;
  color: var(--el-text-color-regular);
  font-size: var(--oa-font-base);
  word-break: break-all;
}

.action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  flex: 1;
}

.sep {
  color: var(--oa-text-muted);
}

</style>
