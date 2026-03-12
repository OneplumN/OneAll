<template>
  <div class="base-chart" :style="{ height: `${height}px` }" ref="chartRef"></div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts';
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

interface Props {
  option: echarts.EChartsOption | null;
  height?: number;
}

const props = withDefaults(defineProps<Props>(), {
  height: 280
});

const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;
let resizeObserver: ResizeObserver | null = null;

const handleResize = () => {
  const hadInstance = !!chartInstance;
  initChartIfNeeded();
  if (!chartInstance) {
    return;
  }
  if (!hadInstance) {
    renderChart();
    return;
  }
  resizeChart();
};

const initChartIfNeeded = () => {
  if (!chartRef.value || chartInstance) {
    return;
  }
  const el = chartRef.value;
  if (!el.clientWidth || !el.clientHeight) {
    return;
  }
  chartInstance = echarts.init(el);
};

const renderChart = () => {
  initChartIfNeeded();
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
  renderChart();
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
  () => renderChart(),
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
