<template>
  <div class="honeycomb-svg-wrapper">
    <svg
      v-if="positions.length"
      :viewBox="`0 0 ${viewBox.width} ${viewBox.height}`"
      :class="['honeycomb-svg', { 'honeycomb-svg--compact': compactMode }]"
      :style="{ minHeight: `${svgHeight}px` }"
      preserveAspectRatio="xMidYMin meet"
    >
      <defs>
        <filter
          id="hex-shadow"
          x="-20%"
          y="-20%"
          width="140%"
          height="160%"
        >
          <feDropShadow
            dx="0"
            dy="8"
            stdDeviation="8"
            flood-color="#94a3b8"
            flood-opacity="0.18"
          />
        </filter>
      </defs>

      <g
        v-for="item in positions"
        :key="item.cell.id"
        class="hex-group"
        :class="[
          `hex-group--${item.cell.status}`,
          { 'hex-group--unmanaged': item.cell.category === 'unmanaged' },
          { 'hex-group--selected': item.cell.id === selectedId },
        ]"
        :style="hexStyle(item.cell.status)"
        :transform="`translate(${item.x}, ${item.y})`"
        tabindex="0"
        role="button"
        :aria-label="formatTooltip(item)"
        @click="$emit('select', item.cell)"
        @keydown.enter.prevent="$emit('select', item.cell)"
        @keydown.space.prevent="$emit('select', item.cell)"
      >
        <title>{{ formatTooltip(item) }}</title>
        <path
          :d="hexPath"
          class="hex-surface"
          filter="url(#hex-shadow)"
        />
        <path
          v-if="item.cell.status === 'danger'"
          :d="hexPath"
          class="hex-attention-ring"
        />
        <path
          :d="hexPath"
          class="hex-hover-ring"
        />
        <path
          v-if="item.cell.id === selectedId"
          :d="hexPath"
          class="hex-selected-ring"
        />
        <circle
          class="hex-status-dot"
          cx="0"
          :cy="denseMode ? -8 : compactMode ? -12 : -18"
          :r="denseMode ? 2.2 : compactMode ? 3.6 : 4.5"
        />

        <g
          v-if="item.cell.badge"
          class="hex-badge"
        >
          <rect
            class="hex-badge__bg"
            :x="compactMode ? 6 : 10"
            :y="compactMode ? -22 : -28"
            :width="compactMode ? 18 : 24"
            :height="compactMode ? 12 : 14"
            :rx="compactMode ? 6 : 7"
            :ry="compactMode ? 6 : 7"
          />
          <text
            class="hex-badge__text"
            :x="compactMode ? 15 : 22"
            :y="compactMode ? -13.5 : -18"
          >
            {{ item.cell.badge }}
          </text>
        </g>

        <text
          v-if="!denseMode"
          class="hex-text label"
          x="0"
          :y="compactMode ? 2 : -2"
        >
          <tspan
            v-for="(line, index) in item.labelLines"
            :key="`${item.cell.id}-${line}`"
            x="0"
            :dy="index === 0 ? 0 : compactMode ? 10 : 12"
          >
            {{ line }}
          </tspan>
        </text>

        <text
          v-if="showCellValue(item.cell)"
          class="hex-text value"
          x="0"
          :y="denseMode ? 4 : compactMode ? 14 : 20"
        >
          {{ item.cell.value }}
        </text>

        <text
          v-if="item.cell.caption && !compactMode"
          class="hex-text caption"
          x="0"
          y="31"
        >
          {{ item.cell.caption }}
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
  badge?: string;
  caption?: string;
  category?: 'default' | 'unmanaged';
  shortLabel?: string;
  description?: string;
  meta?: string[];
  payload?: unknown;
}

const props = defineProps<{
  cells: HoneycombCell[];
  columns?: number;
  size?: number;
  selectedId?: string | null;
  compact?: boolean;
}>();

defineEmits<{ (e: 'select', cell: HoneycombCell): void }>();

const selectedId = computed(() => props.selectedId ?? null);
const hexSize = computed(() => props.size ?? 42);
const cols = computed(() => props.columns ?? 6);
const compactMode = computed(() => props.compact ?? hexSize.value <= 32);
const denseMode = computed(() => hexSize.value <= 18);

const hexPath = computed(() => generateHexagonPath(hexSize.value));
const viewBox = computed(() => {
  const width = hexSize.value * Math.sqrt(3);
  const height = hexSize.value * 2;
  const hSpacing = width;
  const vSpacing = height * 0.76;
  const rows = Math.ceil(props.cells.length / cols.value);

  return {
    width: cols.value * hSpacing + hexSize.value * 4,
    height: rows * vSpacing + hexSize.value * 4.4,
  };
});

const svgHeight = computed(() => {
  const rows = Math.ceil(props.cells.length / cols.value) || 1;
  return Math.max(220, Math.round(rows * hexSize.value * 1.22 + hexSize.value * 2.2));
});

const positions = computed(() =>
  props.cells.map((cell, index) => {
    const row = Math.floor(index / cols.value);
    const col = index % cols.value;
    const { x, y } = calculateHexPosition(row, col, hexSize.value);

    return {
      cell,
      x: x + hexSize.value * 2,
      y: y + hexSize.value * 2.1,
      labelLines: splitLabel(cell.shortLabel || cell.label, compactMode.value),
    };
  }),
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
  const vSpacing = height * 0.76;
  const offset = row % 2 === 1 ? hSpacing / 2 : 0;

  return {
    x: col * hSpacing + offset,
    y: row * vSpacing,
  };
}

function splitLabel(label: string, compact: boolean): string[] {
  const normalized = label.trim();
  if (!normalized) {
    return ['未命名'];
  }
  if (compact) {
    return [normalized.slice(0, 4)];
  }
  if (normalized.length <= 5) {
    return [normalized];
  }
  if (normalized.length <= 10) {
    const midpoint = Math.ceil(normalized.length / 2);
    return [normalized.slice(0, midpoint), normalized.slice(midpoint)];
  }
  return [normalized.slice(0, 5), `${normalized.slice(5, 9)}…`];
}

function hexStyle(status: HoneycombCell['status']) {
  const palette = statusColors[status];
  return {
    '--hex-fill': palette.fill,
    '--hex-stroke': palette.stroke,
    '--hex-accent': palette.accent,
    '--hex-text': palette.text,
  };
}

function showCellValue(cell: HoneycombCell) {
  return Boolean(cell.value);
}

function formatTooltip(item: { cell: HoneycombCell }) {
  const lines = [item.cell.label];
  if (item.cell.description) {
    lines.push(item.cell.description);
  }
  if (item.cell.meta?.length) {
    lines.push(...item.cell.meta);
  }
  return lines.join('\n');
}

const statusColors = {
  success: { fill: '#eaf8ef', stroke: '#bfdcc8', accent: '#059669', text: '#14532d' },
  warning: { fill: '#fff3e6', stroke: '#f0cfaa', accent: '#d97706', text: '#9a5200' },
  danger: { fill: '#fdecec', stroke: '#f1c0c0', accent: '#dc2626', text: '#991b1b' },
  idle: { fill: '#f4f5f7', stroke: '#d7dce4', accent: '#6b7280', text: '#374151' },
};
</script>

<style scoped>
.honeycomb-svg-wrapper {
  width: 100%;
  overflow-x: auto;
  padding: 0;
  border: none;
  background: transparent;
}

.honeycomb-svg {
  width: 100%;
  display: block;
}

.hex-group {
  cursor: pointer;
  outline: none;
}

.hex-surface {
  fill: var(--hex-fill);
  stroke: var(--hex-stroke);
  stroke-width: 1.2;
  transition: fill 0.18s ease, stroke 0.18s ease, opacity 0.18s ease;
  vector-effect: non-scaling-stroke;
}

.hex-hover-ring,
.hex-attention-ring,
.hex-selected-ring {
  fill: none;
  pointer-events: none;
  vector-effect: non-scaling-stroke;
}

.hex-hover-ring {
  stroke: var(--hex-accent);
  stroke-width: 1.6;
  opacity: 0;
  transition: opacity 0.18s ease;
}

.hex-selected-ring {
  stroke: var(--hex-accent);
  stroke-width: 2.6;
}

.hex-attention-ring {
  stroke: #f97316;
  stroke-width: 2;
  opacity: 0.26;
  animation: dangerPulse 1.8s ease-in-out infinite;
}

.hex-group:hover .hex-hover-ring,
.hex-group:focus-visible .hex-hover-ring {
  opacity: 1;
}

.hex-group:hover .hex-surface,
.hex-group:focus-visible .hex-surface {
  opacity: 0.94;
}

.hex-group--selected .hex-surface {
  stroke: var(--hex-accent);
}

.hex-group--unmanaged .hex-surface {
  stroke-dasharray: 4 3;
}

.hex-status-dot {
  fill: var(--hex-accent);
  pointer-events: none;
  vector-effect: non-scaling-stroke;
}

.hex-text {
  pointer-events: none;
  text-anchor: middle;
}

.hex-text.label {
  fill: var(--hex-text);
  font-size: 10px;
  font-weight: 600;
}

.hex-text.value {
  fill: var(--hex-accent);
  font-size: 12px;
  font-weight: 700;
}

.hex-text.caption {
  fill: color-mix(in srgb, var(--hex-text) 78%, white);
  font-size: 8px;
  font-weight: 600;
}

.hex-badge__bg {
  fill: color-mix(in srgb, var(--hex-accent) 16%, white);
  stroke: color-mix(in srgb, var(--hex-accent) 45%, white);
  stroke-width: 0.8;
  vector-effect: non-scaling-stroke;
}

.hex-badge__text {
  fill: var(--hex-accent);
  font-size: 8px;
  font-weight: 800;
  text-anchor: middle;
  dominant-baseline: middle;
  pointer-events: none;
}

.honeycomb-svg--compact .hex-text.label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.honeycomb-svg--compact .hex-text.value {
  font-size: 10px;
}

.honeycomb-svg--compact .hex-text.caption {
  font-size: 7px;
}

.honeycomb-svg--compact .hex-status-dot {
  opacity: 0.9;
}

.honeycomb-svg--compact .hex-badge__text {
  font-size: 7px;
}

.honeycomb-svg--compact .hex-group {
  transform-origin: center;
}

@keyframes dangerPulse {
  0%,
  100% {
    opacity: 0.16;
  }

  50% {
    opacity: 0.56;
  }
}
</style>
