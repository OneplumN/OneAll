<template>
  <div class="asset-table">
    <div :class="['asset-table__card', { 'asset-table__card--x-scroll': allowHorizontalScroll }]">
      <el-table
        v-loading="loading"
        height="100%"
        :data="rows"
        class="oa-table"
        stripe
        @selection-change="emit('selectionChange', $event)"
      >
        <template #empty>
          <div class="table-empty">
            <p>暂无资产数据</p>
          </div>
        </template>
        <el-table-column
          v-if="viewKey === 'workorder-host'"
          type="selection"
          width="48"
          fixed="left"
        />
        <el-table-column
          v-for="column in columns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          :width="column.width"
          :min-width="column.minWidth"
          show-overflow-tooltip
        >
          <template #header>
            <span class="column-header">
              <span
                v-if="column.isUnique"
                class="unique-mark"
              >
                *
              </span>
              {{ column.label }}
            </span>
          </template>
          <template #default="{ row }">
            <el-dropdown
              v-if="viewKey === 'workorder-host' && column.key === 'online_status' && (row.online_status_code || '')"
              trigger="click"
              :disabled="!canManage || statusToggling[row.id]"
              @command="(command: string) => emit('rowStatusCommand', row, command)"
            >
              <el-tag
                size="small"
                effect="plain"
                :type="statusTagType(row[column.key])"
              >
                {{ row[column.key] }}
              </el-tag>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="online">
                    在线
                  </el-dropdown-item>
                  <el-dropdown-item command="maintenance">
                    维护
                  </el-dropdown-item>
                  <el-dropdown-item command="offline">
                    下线
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-tag
              v-else-if="column.type === 'status' && row[column.key] && row[column.key] !== '-'"
              size="small"
              :type="statusTagType(row[column.key])"
              effect="plain"
            >
              {{ row[column.key] }}
            </el-tag>
            <span v-else>{{ row[column.key] || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="180"
          fixed="right"
        >
          <template #default="{ row }">
            <el-space size="small">
              <el-button
                v-if="showEditColumn"
                class="oa-table-action oa-table-action--success"
                text
                size="small"
                :disabled="!canManage"
                @click.stop="emit('edit', row)"
              >
                编辑
              </el-button>
              <el-button
                v-if="row.sync_status === '冲突' || row.sync_status === '需人工检查'"
                class="oa-table-action oa-table-action--warning"
                text
                size="small"
                @click.stop="emit('conflict', row)"
              >
                冲突详情
              </el-button>
              <el-button
                class="oa-table-action oa-table-action--primary"
                text
                size="small"
                @click.stop="emit('detail', row)"
              >
                详情
              </el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>

  <div class="oa-panel-footer">
    <div class="oa-panel-footer__left">
      <div class="oa-panel-stats">
        共 {{ total }} 条
      </div>
      <el-pagination
        class="asset-pagination__sizes"
        :total="total"
        :current-page="page"
        :page-size="pageSize"
        :page-sizes="pageSizeOptions"
        layout="sizes"
        background
        @size-change="emit('pageSizeChange', $event)"
        @current-change="emit('pageChange', $event)"
      />
    </div>
    <div class="oa-panel-footer__right">
      <el-pagination
        class="asset-pagination__pager"
        :total="total"
        :current-page="page"
        :page-size="pageSize"
        layout="prev, pager, next"
        background
        @current-change="emit('pageChange', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AssetColumn, AssetRow, AssetViewKey } from '@/features/assets/types/assetCenter';

defineProps<{
  viewKey: AssetViewKey;
  canManage: boolean;
  showEditColumn: boolean;
  allowHorizontalScroll: boolean;
  loading: boolean;
  rows: AssetRow[];
  columns: AssetColumn[];
  statusToggling: Record<string, boolean>;
  total: number;
  page: number;
  pageSize: number;
  pageSizeOptions: number[];
  statusTagType: (status: string) => string;
}>();

const emit = defineEmits<{
  (event: 'selectionChange', rows: Array<{ id: string }>): void;
  (event: 'rowStatusCommand', row: AssetRow, command: string): void;
  (event: 'edit', row: AssetRow): void;
  (event: 'conflict', row: AssetRow): void;
  (event: 'detail', row: AssetRow): void;
  (event: 'pageChange', page: number): void;
  (event: 'pageSizeChange', size: number): void;
}>();
</script>

<style scoped>
.asset-table {
  padding-left: 16px;
  padding-right: 16px;
  background: var(--oa-bg-panel);
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
  padding-top: 0;
  padding-bottom: 12px;
}

.asset-table__card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: none;
  border-radius: 0;
  overflow: hidden;
}

.asset-table__card :deep(.el-table) {
  flex: 1;
  overflow-x: hidden;
}

.asset-table__card :deep(.el-table__header-wrapper) {
  overflow-x: hidden;
}

.asset-table__card :deep(.el-table__body-wrapper),
.asset-table__card :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

.asset-table__card--x-scroll :deep(.el-table__body-wrapper),
.asset-table__card--x-scroll :deep(.el-scrollbar__wrap) {
  overflow-x: auto;
}

.asset-table__card :deep(.el-table__inner-wrapper) {
  border-left: none !important;
  border-right: none !important;
}

.column-header {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.unique-mark {
  color: var(--oa-color-danger);
}

.table-empty {
  padding: 2rem;
  text-align: center;
  color: var(--oa-text-secondary);
}

.asset-pagination__sizes,
.asset-pagination__pager {
  margin-top: 4px;
}
</style>
