<template>
  <svg
    class="login-illustration"
    viewBox="0 0 720 520"
    role="img"
    aria-label="平台能力示意图"
  >
    <defs>
      <linearGradient id="oa-grad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="var(--oa-color-primary)" stop-opacity="0.95" />
        <stop offset="1" stop-color="var(--oa-color-primary-light)" stop-opacity="0.65" />
      </linearGradient>
      <linearGradient id="oa-glow" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="var(--illus-accent)" stop-opacity="0.16" />
        <stop offset="1" stop-color="var(--illus-accent)" stop-opacity="0.04" />
      </linearGradient>
      <filter id="oa-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#0b1220" flood-opacity="0.18" />
      </filter>
    </defs>

    <!-- Ground -->
    <path
      d="M110 390 C 220 460, 520 460, 610 390 C 520 330, 220 330, 110 390 Z"
      fill="url(#oa-glow)"
      stroke="var(--illus-ink-soft)"
      stroke-opacity="1"
    />

    <!-- Central hub -->
    <g filter="url(#oa-shadow)">
      <circle
        cx="360"
        cy="270"
        r="78"
        fill="var(--illus-panel)"
        stroke="var(--illus-panel-border)"
        stroke-opacity="1"
      />
      <circle
        cx="360"
        cy="270"
        r="52"
        fill="var(--illus-panel-soft)"
        stroke="var(--illus-panel-border)"
        stroke-opacity="1"
      />
      <circle cx="360" cy="270" r="26" fill="url(#oa-grad)" />
      <path
        d="M350 270 l8 10 l16 -22"
        fill="none"
        stroke="var(--illus-on-accent)"
        stroke-width="7"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </g>

    <!-- Orbit nodes -->
    <g stroke="var(--illus-ink-soft)" stroke-opacity="1" stroke-width="2" fill="none">
      <path d="M196 270 C 270 190, 450 190, 524 270" />
      <path d="M206 308 C 292 382, 428 382, 514 308" />
    </g>

    <!-- Left node: 探针 -->
    <g transform="translate(146 228)">
      <rect
        x="0"
        y="0"
        width="128"
        height="92"
        rx="14"
        fill="var(--illus-panel)"
        stroke="var(--illus-panel-border)"
      />
      <text x="18" y="34" fill="var(--illus-text)" font-size="14" font-weight="700">探针</text>
      <path d="M18 58 H110" stroke="var(--illus-ink-soft)" stroke-opacity="1" />
      <circle cx="30" cy="70" r="6" fill="var(--illus-ink)" fill-opacity="1" />
      <circle cx="58" cy="70" r="6" fill="var(--illus-ink)" fill-opacity="0.6" />
      <circle cx="86" cy="70" r="6" fill="var(--illus-ink)" fill-opacity="0.35" />
    </g>

    <!-- Right node: 监控 -->
    <g transform="translate(446 224)">
      <rect
        x="0"
        y="0"
        width="128"
        height="92"
        rx="14"
        fill="var(--illus-panel)"
        stroke="var(--illus-panel-border)"
      />
      <text x="18" y="34" fill="var(--illus-text)" font-size="14" font-weight="700">监控</text>
      <path
        d="M18 70 L42 56 L62 68 L82 44 L110 60"
        stroke="var(--illus-ink)"
        stroke-opacity="1"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </g>

    <!-- Bottom node: 工单 -->
    <g transform="translate(294 362)">
      <rect
        x="0"
        y="0"
        width="132"
        height="96"
        rx="14"
        fill="var(--illus-panel)"
        stroke="var(--illus-panel-border)"
      />
      <text x="18" y="34" fill="var(--illus-text)" font-size="14" font-weight="700">工单</text>
      <path d="M18 54 H112" stroke="var(--illus-ink-soft)" stroke-opacity="1" />
      <path d="M18 70 H92" stroke="var(--illus-ink-soft)" stroke-opacity="0.7" />
      <path d="M18 86 H78" stroke="var(--illus-ink-soft)" stroke-opacity="0.55" />
    </g>

    <!-- Connectors -->
    <g stroke="var(--illus-ink-soft)" stroke-opacity="1" stroke-width="2">
      <path d="M274 274 C 308 260, 320 260, 334 268" fill="none" />
      <path d="M446 272 C 412 258, 400 258, 386 268" fill="none" />
      <path d="M360 346 C 360 338, 360 332, 360 324" fill="none" />
    </g>
  </svg>
</template>

<style scoped>
.login-illustration {
  --illus-accent: var(--oa-color-primary);
  --illus-text: var(--oa-text-primary);
  --illus-ink: rgba(29, 78, 216, 0.82);
  --illus-ink-soft: rgba(29, 78, 216, 0.32);
  --illus-panel: rgba(37, 99, 235, 0.08);
  --illus-panel-soft: rgba(37, 99, 235, 0.06);
  --illus-panel-border: rgba(37, 99, 235, 0.22);
  --illus-on-accent: #ffffff;
  width: 100%;
  height: auto;
  max-width: 660px;
}

[data-theme='dark'] .login-illustration {
  --illus-text: rgba(255, 255, 255, 0.92);
  --illus-ink: rgba(255, 255, 255, 0.88);
  --illus-ink-soft: rgba(255, 255, 255, 0.26);
  --illus-panel: rgba(255, 255, 255, 0.10);
  --illus-panel-soft: rgba(255, 255, 255, 0.08);
  --illus-panel-border: rgba(255, 255, 255, 0.18);
}
</style>
