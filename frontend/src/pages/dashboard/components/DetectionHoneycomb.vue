<template>
  <div class="honeycomb-svg-wrapper">
    <svg
      v-if="positions.length"
      :viewBox="`0 0 ${viewBox.width} ${viewBox.height}`"
      class="honeycomb-svg"
    >
      <defs>
        <filter id="hex-glow">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <g
        v-for="item in positions"
        :key="item.cell.id"
        class="hex-group"
        :transform="`translate(${item.x}, ${item.y})`"
        @click="$emit('select', item.cell)"
      >
        <path
          :d="hexPath"
          :fill="statusColors[item.cell.status].fill"
          :stroke="statusColors[item.cell.status].stroke"
          stroke-width="1"
          filter="url(#hex-glow)"
        />
        <text class="hex-text label" x="0" y="-4">
          {{ item.cell.label }}
        </text>
        <text class="hex-text value" x="0" y="10">
          {{ item.cell.value }}
        </text>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

export interface HoneycombCell {
  id: string;
  label: string;
  value: string;
  status: 'success' | 'warning' | 'danger' | 'idle';
  payload?: unknown;
}

const props = defineProps<{ cells: HoneycombCell[]; columns?: number; size?: number }>();
defineEmits<{ (e: 'select', cell: HoneycombCell): void }>();

const hexSize = computed(() => props.size ?? 30);
const cols = computed(() => props.columns ?? 10);

const hexPath = computed(() => generateHexagonPath(hexSize.value));
const viewBox = computed(() => {
  const width = hexSize.value * Math.sqrt(3);
  const height = hexSize.value * 2;
  const hSpacing = width;
  const vSpacing = height * 0.75;
  const rows = Math.ceil(props.cells.length / cols.value);
  return {
    width: cols.value * hSpacing + hexSize.value * 4,
    height: rows * vSpacing + hexSize.value * 4
  };
});

const positions = computed(() =>
  props.cells.map((cell, index) => {
    const row = Math.floor(index / cols.value);
    const col = index % cols.value;
    const { x, y } = calculateHexPosition(row, col, hexSize.value);
    return {
      cell,
      x: x + hexSize.value * 2,
      y: y + hexSize.value * 2
    };
  })
);

function generateHexagonPath(size: number) {
  const points: string[] = [];
  for (let i = 0; i < 6; i += 1) {
    const angle = (Math.PI / 3) * i - Math.PI / 2;
    const x = size * Math.cos(angle);
    const y = size * Math.sin(angle);
    points.push(`${x},${y}`);
  }
  return `M ${points.join(' L ')} Z`;
}

function calculateHexPosition(row: number, col: number, size: number) {
  const width = size * Math.sqrt(3);
  const height = size * 2;
  const hSpacing = width;
  const vSpacing = height * 0.75;
  const offset = row % 2 === 1 ? hSpacing / 2 : 0;
  return {
    x: col * hSpacing + offset,
    y: row * vSpacing
  };
}

const statusColors = {
  success: { fill: '#67C23A', stroke: '#529B2E' },
  warning: { fill: '#E6A23C', stroke: '#CF9236' },
  danger: { fill: '#F56C6C', stroke: '#DD6161' },
  idle: { fill: '#909399', stroke: '#73767A' }
};
</script>

<style scoped>
.honeycomb-svg-wrapper {
  width: 100%;
  overflow-x: auto;
}

.honeycomb-svg {
  width: 100%;
  min-height: 460px;
}

.hex-group {
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.hex-group:hover {
  opacity: 0.85;
}

.hex-text {
  fill: #fff;
  text-anchor: middle;
  pointer-events: none;
}

.hex-text.label {
  font-size: 9px;
  font-weight: 600;
}

.hex-text.value {
  font-size: 10px;
  font-weight: 400;
}
</style>
