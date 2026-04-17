import dayjs from 'dayjs';
import type { EChartsOption } from 'echarts';

import type { ProbeMetricsHistoryResponse } from '@/features/probes/api/probeNodeApi';

export function buildCpuTrendOption(history: ProbeMetricsHistoryResponse | null): EChartsOption | null {
  if (!history || !history.points.length) return null;
  const times = history.points.map((p) => dayjs(p.timestamp).format('HH:mm'));
  const values = history.points.map((p) => Number(p.cpu_usage ?? 0));
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const item = Array.isArray(params) ? params[0] : params;
        return `${item.axisValue}<br/>CPU：${item.value.toFixed(0)}%`;
      }
    },
    grid: { left: 48, right: 16, top: 24, bottom: 32 },
    xAxis: { type: 'category', data: times, boundaryGap: false },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { formatter: '{value}%' },
      splitLine: { show: true }
    },
    series: [
      {
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: '#409EFF' },
        areaStyle: { color: 'rgba(64, 158, 255, 0.15)' }
      }
    ]
  };
}

export function buildMemoryTrendOption(history: ProbeMetricsHistoryResponse | null): EChartsOption | null {
  if (!history || !history.points.length) return null;
  const times = history.points.map((p) => dayjs(p.timestamp).format('HH:mm'));
  const values = history.points.map((p) => Number(p.memory_usage_mb ?? 0));
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const item = Array.isArray(params) ? params[0] : params;
        const pct = Number(item.value ?? 0);
        return `${item.axisValue}<br/>内存：${pct.toFixed(0)}%`;
      }
    },
    grid: { left: 48, right: 16, top: 24, bottom: 32 },
    xAxis: { type: 'category', data: times, boundaryGap: false },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitLine: { show: true },
      axisLabel: { formatter: (params: any) => `${Number(params).toFixed(0)}%` }
    },
    series: [
      {
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: '#67c23a' },
        areaStyle: { color: 'rgba(103, 194, 58, 0.15)' }
      }
    ]
  };
}

export function buildQueueTrendOption(history: ProbeMetricsHistoryResponse | null): EChartsOption | null {
  if (!history || !history.points.length) return null;
  const times = history.points.map((p) => dayjs(p.timestamp).format('HH:mm'));
  const depths = history.points.map((p) => p.queue_depth ?? 0);
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 16, top: 24, bottom: 32 },
    xAxis: { type: 'category', data: times, boundaryGap: false },
    yAxis: {
      type: 'value',
      name: '队列深度',
      min: 0,
      splitLine: { show: true }
    },
    series: [
      {
        type: 'line',
        data: depths,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: '#67c23a' },
        areaStyle: { color: 'rgba(103, 194, 58, 0.15)' }
      }
    ]
  };
}
