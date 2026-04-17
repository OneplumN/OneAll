<template>
  <aside
    class="repository-aside"
    :style="{ width: sidebarWidth }"
  >
    <div class="layout__aside-scroll">
      <el-menu
        v-if="directoryGroups.length"
        class="layout__menu layout__menu--local"
        :default-active="selectedDirectoryKey"
        :collapse="collapsedModel"
        :collapse-transition="false"
        @select="handleSelect"
      >
        <el-tooltip
          v-for="group in directoryGroups"
          :key="group.key"
          class="nav-entry__tooltip"
          effect="dark"
          placement="right"
          :content="group.title"
          :disabled="!collapsedModel"
          popper-class="layout__nav-tooltip-popper"
        >
          <el-menu-item
            :index="group.key"
            class="nav-entry"
          >
            <div class="nav-entry__icon">
              <component :is="resolveDirectoryIcon(group.key)" />
            </div>
            <span class="nav-entry__label">{{ group.title }}</span>
          </el-menu-item>
        </el-tooltip>
      </el-menu>
      <div
        v-else
        class="sidebar-placeholder"
      >
        <p>暂无目录，请联系管理员配置</p>
      </div>
    </div>
    <div class="aside__footer layout__aside-footer">
      <el-button
        class="layout__toggle"
        text
        @click="collapsedModel = !collapsedModel"
      >
        <el-icon>
          <component :is="collapsedModel ? Expand : Fold" />
        </el-icon>
      </el-button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue';
import { Expand, Fold } from '@element-plus/icons-vue';

type DirectoryGroup = {
  key: string;
  title: string;
};

defineProps<{
  directoryGroups: DirectoryGroup[];
  selectedDirectoryKey: string;
  resolveDirectoryIcon: (key: string) => Component;
}>();

const emit = defineEmits<{
  (event: 'select', key: string): void;
}>();

const collapsedModel = defineModel<boolean>('collapsed', { required: true });
const sidebarWidth = computed(() => (collapsedModel.value ? '72px' : '240px'));

const handleSelect = (key: string) => {
  emit('select', key);
};
</script>

<style scoped>
.repository-aside {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--oa-bg-surface);
  border-right: 1px solid var(--oa-border-light);
  transition: width 0.2s ease;
  min-height: 0;
  position: sticky;
  top: 0;
  height: calc(100vh - 64px);
  max-height: calc(100vh - 64px);
}

.layout__aside-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 0;
}

.sidebar-placeholder {
  padding: 16px;
  text-align: center;
  color: var(--oa-text-secondary);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
  justify-content: center;
}
</style>
