<template>
  <div class="monitoring-overview-page">
    <HomeOverview />
  </div>
</template>

<script setup lang="ts">
import HomeOverview from './dashboard/HomeOverview.vue';
</script>

<style scoped>
.monitoring-overview-page {
  padding: 1.5rem;
  background: radial-gradient(circle at 20% 20%, rgba(59, 130, 246, 0.08), transparent 45%),
    linear-gradient(135deg, #030712 0%, #050c1c 60%, #01030a 100%);
  border-radius: 28px;
  border: 1px solid rgba(59, 130, 246, 0.15);
  min-height: calc(100vh - 220px);
  box-shadow: 0 35px 65px rgba(2, 6, 23, 0.7);
}

@media (max-width: 1024px) {
  .monitoring-overview-page {
    padding: 1rem;
    border-radius: 20px;
    min-height: calc(100vh - 180px);
  }
}
</style>
