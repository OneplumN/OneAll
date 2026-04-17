<template>
  <div
    ref="chartRef"
    class="base-chart"
    :style="{ height: `${height}px` }"
  />
</template>

<script setup lang="ts">
import type { EChartsOption } from 'echarts';
import type { EChartsType } from 'echarts/core';
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

interface Props {
  option: EChartsOption | null;
  height?: number;
}

const props = withDefaults(defineProps<Props>(), {
  height: 280
});

const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: EChartsType | null = null;
let resizeObserver: ResizeObserver | null = null;
let echartsModulePromise: Promise<typeof import('@/utils/echarts')> | null = null;
let chartInitPromise: Promise<void> | null = null;

const loadECharts = () => {
  if (!echartsModulePromise) {
    echartsModulePromise = import('@/utils/echarts');
  }
  return echartsModulePromise;
};

const handleResize = () => {
  if (!chartInstance) {
    void renderChart();
    return;
  }
  resizeChart();
};

const initChartIfNeeded = async () => {
  if (!chartRef.value || chartInstance) {
    return;
  }
  const el = chartRef.value;
  if (!el.clientWidth || !el.clientHeight) {
    return;
  }
  if (!chartInitPromise) {
    chartInitPromise = (async () => {
      const echarts = await loadECharts();
      if (!chartRef.value || chartInstance) {
        return;
      }
      const target = chartRef.value;
      if (!target.clientWidth || !target.clientHeight) {
        return;
      }
      chartInstance = echarts.init(target);
    })().finally(() => {
      chartInitPromise = null;
    });
  }
  await chartInitPromise;
};

const renderChart = async () => {
  await initChartIfNeeded();
  if (!chartInstance || !props.option) {
    return;
  }
  chartInstance.setOption(props.option, { notMerge: true, lazyUpdate: true });
  nextTick(() => resizeChart());
};

onMounted(() => {
  if (!chartRef.value) {
    return;
  }
  void renderChart();
  window.addEventListener('resize', handleResize);
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => handleResize());
    resizeObserver.observe(chartRef.value);
  }
});

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize();
  }
};

watch(
  () => props.option,
  () => {
    void renderChart();
  },
  { deep: true }
);

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (resizeObserver && chartRef.value) {
    resizeObserver.unobserve(chartRef.value);
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
</script>

<style scoped>
.base-chart {
  width: 100%;
}
</style>
