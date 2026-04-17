<template>
  <div class="overview-charts">
    <el-card
      class="chart-card"
      shadow="never"
    >
      <template #header>
        <span>拨测任务</span>
      </template>
      <el-descriptions
        :column="1"
        border
      >
        <el-descriptions-item label="待处理任务">
          <strong>{{ detection.pending_jobs }}</strong>
        </el-descriptions-item>
        <el-descriptions-item label="近 24 小时执行">
          <strong>{{ detection.last_24h_runs }}</strong>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card
      class="chart-card"
      shadow="never"
    >
      <template #header>
        <span>告警概况</span>
      </template>
      <el-descriptions
        :column="1"
        border
      >
        <el-descriptions-item label="未恢复">
          <strong>{{ incidents.open }}</strong>
        </el-descriptions-item>
        <el-descriptions-item label="已确认">
          <strong>{{ incidents.acknowledged }}</strong>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
interface DetectionMetrics {
  pending_jobs: number;
  last_24h_runs: number;
}

interface IncidentMetrics {
  open: number;
  acknowledged: number;
}

defineProps<{
  detection: DetectionMetrics;
  incidents: IncidentMetrics;
}>();
</script>

<style scoped>
.overview-charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}

.chart-card {
  min-height: 180px;
}
</style>
