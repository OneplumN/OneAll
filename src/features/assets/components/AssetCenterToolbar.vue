<template>
  <div class="asset-filters">
    <div class="filters-left">
      <el-button
        class="toolbar-button toolbar-button--primary"
        type="primary"
        plain
        :disabled="!canCreate"
        @click="emit('openCreate')"
      >
        新增
      </el-button>
      <el-button
        v-if="canImport"
        class="toolbar-button"
        plain
        :disabled="!canCreate"
        @click="emit('openImport')"
      >
        批量导入
      </el-button>
      <el-button
        class="toolbar-button"
        plain
        @click="emit('export')"
      >
        导出 CSV
      </el-button>
      <el-dropdown
        v-if="viewKey === 'workorder-host'"
        trigger="click"
        :disabled="!canManage || !selectedRowCount"
        @command="(command: string) => emit('batchStatusCommand', command)"
      >
        <el-button
          class="toolbar-button"
          plain
          :disabled="!canManage || !selectedRowCount"
        >
          批量状态（{{ selectedRowCount }}）
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="online">
              设为在线
            </el-dropdown-item>
            <el-dropdown-item command="maintenance">
              设为维护
            </el-dropdown-item>
            <el-dropdown-item command="offline">
              设为下线
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    <div class="filters-right">
      <el-select
        v-if="showNetworkTypeFilter"
        v-model="networkFilterModel"
        placeholder="互联网类型"
        clearable
        class="pill-input narrow-select"
      >
        <el-option
          label="全部"
          value=""
        />
        <el-option
          label="内网域名"
          value="internal"
        />
        <el-option
          label="互联网域名"
          value="internet"
        />
      </el-select>

      <el-select
        v-if="showOnlineStatusFilter"
        v-model="onlineStatusFilterModel"
        placeholder="在线状态"
        clearable
        class="pill-input narrow-select"
      >
        <el-option
          label="全部"
          value=""
        />
        <el-option
          label="在线"
          value="online"
        />
        <el-option
          label="维护"
          value="maintenance"
        />
        <el-option
          label="下线"
          value="offline"
        />
      </el-select>

      <el-select
        v-if="showProxyFilter"
        v-model="proxyFilterModel"
        placeholder="Proxy"
        clearable
        filterable
        class="pill-input narrow-select"
      >
        <el-option
          label="全部"
          value=""
        />
        <el-option
          v-for="option in proxyOptions"
          :key="option"
          :label="option"
          :value="option"
        />
      </el-select>

      <el-select
        v-if="showInterfaceAvailableFilter"
        v-model="interfaceAvailableFilterModel"
        placeholder="接口可用性"
        clearable
        filterable
        class="pill-input narrow-select"
      >
        <el-option
          label="全部"
          value=""
        />
        <el-option
          v-for="option in interfaceAvailableOptions"
          :key="option"
          :label="option"
          :value="option"
        />
      </el-select>

      <el-select
        v-if="showAppStatusFilter"
        v-model="appStatusFilterModel"
        placeholder="应用状态"
        clearable
        filterable
        class="pill-input narrow-select"
      >
        <el-option
          label="全部"
          value=""
        />
        <el-option
          v-for="option in appStatusOptions"
          :key="option"
          :label="option"
          :value="option"
        />
      </el-select>

      <el-input
        v-model="keywordModel"
        :placeholder="keywordPlaceholder"
        clearable
        class="pill-input search-input search-input--compact"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AssetViewKey } from '@/features/assets/types/assetCenter';

defineProps<{
  canCreate: boolean;
  canImport: boolean;
  canManage: boolean;
  viewKey: AssetViewKey;
  selectedRowCount: number;
  showNetworkTypeFilter: boolean;
  showOnlineStatusFilter: boolean;
  showProxyFilter: boolean;
  showInterfaceAvailableFilter: boolean;
  showAppStatusFilter: boolean;
  keywordPlaceholder: string;
  proxyOptions: string[];
  interfaceAvailableOptions: string[];
  appStatusOptions: string[];
}>();

const emit = defineEmits<{
  (event: 'openCreate'): void;
  (event: 'openImport'): void;
  (event: 'export'): void;
  (event: 'batchStatusCommand', command: string): void;
}>();

const keywordModel = defineModel<string>('keyword', { required: true });
const networkFilterModel = defineModel<string>('networkFilter', { required: true });
const onlineStatusFilterModel = defineModel<string>('onlineStatusFilter', { required: true });
const proxyFilterModel = defineModel<string>('proxyFilter', { required: true });
const interfaceAvailableFilterModel = defineModel<string>('interfaceAvailableFilter', { required: true });
const appStatusFilterModel = defineModel<string>('appStatusFilter', { required: true });
</script>

<style scoped>
.asset-filters {
  padding-left: 16px;
  padding-right: 16px;
  background: var(--oa-bg-panel);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
  padding-top: 16px;
  padding-bottom: 16px;
  margin: 0;
  border-bottom: 1px solid var(--oa-border-light);
  overflow: hidden;
}

.filters-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
  flex-wrap: nowrap;
  min-width: 0;
}

.filters-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  flex: 1 1 auto;
  flex-wrap: nowrap;
  min-width: 0;
  margin-left: auto;
  justify-content: flex-end;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
}

.filters-right > * {
  flex: 0 0 auto;
}

@media (max-width: 1440px) {
  .asset-filters {
    flex-wrap: wrap;
  }

  .filters-left,
  .filters-right {
    flex-wrap: wrap;
  }

  .filters-right {
    justify-content: flex-start;
    overflow-x: visible;
  }
}
</style>
