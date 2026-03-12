<template>
  <el-card shadow="never" class="detection-card config-card">
    <div class="card-title">
      <el-icon><component :is="icon" /></el-icon>
      <span>{{ title }}</span>
    </div>

    <slot />
  </el-card>
</template>

<script setup lang="ts">
import { Setting } from '@element-plus/icons-vue';
import type { Component } from 'vue';

interface Props {
  title?: string;
  icon?: Component;
}

withDefaults(defineProps<Props>(), {
  title: '检测配置',
  icon: Setting
});
</script>

<style scoped>
@import '../styles/detection-common.scss';
</style>
