<template>
  <section
    v-loading="loading"
    class="page-wrapper"
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
