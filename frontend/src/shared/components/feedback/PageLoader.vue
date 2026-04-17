<template>
  <div class="page-loader">
    <div class="page-loader__header">
      <div class="page-loader__title" />
      <div class="page-loader__actions">
        <div class="page-loader__chip" />
        <div class="page-loader__chip" />
      </div>
    </div>
    <div class="page-loader__table">
      <div
        v-for="row in 5"
        :key="row"
        class="page-loader__row"
      />
    </div>
  </div>
</template>

<style scoped>
.page-loader {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-loader__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-loader__title {
  width: 200px;
  height: 20px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f5f7fa 25%, #eaeef4 37%, #f5f7fa 63%);
  background-size: 400px 100%;
  animation: shimmer 1.5s infinite;
}

.page-loader__actions {
  display: flex;
  gap: 12px;
}

.page-loader__chip {
  width: 100px;
  height: 20px;
  border-radius: 999px;
  background: linear-gradient(90deg, #f5f7fa 25%, #eaeef4 37%, #f5f7fa 63%);
  background-size: 400px 100%;
  animation: shimmer 1.5s infinite;
}

.page-loader__table {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.page-loader__row {
  height: 48px;
  border-radius: 6px;
  background: linear-gradient(90deg, #f5f7fa 25%, #eaeef4 37%, #f5f7fa 63%);
  background-size: 400px 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: 200px 0;
  }
}
</style>
