<template>
  <section
    class="page-wrapper"
    v-loading="loading"
    element-loading-text="加载中..."
  >
    <slot />
  </section>
</template>

<script setup lang="ts">
defineProps<{
  loading?: boolean;
}>();
</script>

<style scoped>
.page-wrapper {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
