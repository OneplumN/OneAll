<template>
  <RepositoryPageShell
    root-title="运维工具"
    section-title="IP 正则助手"
    body-padding="0"
    :panel-bordered="false"
  >
    <template #actions>
      <el-button
        class="toolbar-button"
        @click="fillSample"
      >
        填入示例
      </el-button>
      <el-button
        class="toolbar-button"
        @click="clearAll"
      >
        清空
      </el-button>
    </template>

    <div class="helper-page">
      <div class="helper-grid">
        <el-card
          shadow="never"
          class="helper-card"
        >
          <template #header>
            <div class="panel-head">
              <div>
                <div class="panel-title">
                  IP → 正则
                </div>
                <div class="panel-desc">
                  每行一个 IPv4；会自动去重并忽略无效项。
                </div>
              </div>
              <div class="panel-head__right">
                <span class="badge">输入 {{ ipLineCount }} 行</span>
                <span class="badge badge--muted">匹配 {{ matchedCount }} 个</span>
              </div>
            </div>
          </template>

          <el-input
            v-model="ipInput"
            type="textarea"
            :rows="8"
            placeholder="每行一个 IP，示例：\n192.168.1.10\n192.168.1.11"
          />
          <div class="panel-actions">
            <el-button
              type="primary"
              :loading="converting"
              @click="handleGenerate"
            >
              生成正则
            </el-button>
            <el-button
              text
              @click="clearIps"
            >
              清空 IP
            </el-button>
            <span class="hint">最多支持 500 行</span>
          </div>
          <el-alert
            v-if="invalidIps.length"
            type="warning"
            show-icon
            :closable="false"
            class="mt-12"
          >
            以下 {{ invalidIps.length }} 个 IP 校验失败：{{ invalidIps.join(', ') }}
          </el-alert>

          <el-divider class="panel-divider" />

          <div class="panel-head">
            <div>
              <div class="panel-title panel-title--sub">
                正则输出
              </div>
              <div class="panel-desc">
                用于精确匹配这批 IP 的正则表达式。
              </div>
            </div>
            <div class="panel-head__right">
              <el-button
                text
                :icon="DocumentCopy"
                :disabled="!regexOutput"
                @click="copyText(regexOutput)"
              >
                复制
              </el-button>
              <el-button
                text
                :disabled="!regexOutput"
                @click="useGeneratedRegex"
              >
                用于反推
              </el-button>
            </div>
          </div>
          <el-input
            v-model="regexOutput"
            type="textarea"
            :rows="8"
            readonly
            placeholder="生成的正则会显示在这里"
          />
        </el-card>

        <el-card
          shadow="never"
          class="helper-card"
        >
          <template #header>
            <div class="panel-head">
              <div>
                <div class="panel-title">
                  正则 → IP
                </div>
                <div class="panel-desc">
                  输入已有的 IP 匹配正则，确认覆盖范围。
                </div>
              </div>
              <div class="panel-head__right">
                <span class="limit-label">最大解析条数</span>
                <el-input-number
                  v-model="reverseLimit"
                  size="small"
                  :min="1"
                  :max="2000"
                />
              </div>
            </div>
          </template>

          <el-input
            v-model="regexInput"
            type="textarea"
            :rows="8"
            placeholder="(192\\.168\\.1\\.1|192\\.168\\.1\\.2)"
          />
          <div class="panel-actions">
            <el-button
              type="primary"
              :loading="expanding"
              @click="handleReverse"
            >
              解析 IP
            </el-button>
            <el-button
              text
              @click="useGeneratedRegex"
            >
              使用左侧正则
            </el-button>
            <el-button
              text
              @click="regexInput = ''"
            >
              清空正则
            </el-button>
          </div>

          <el-divider class="panel-divider" />

          <div class="panel-head">
            <div>
              <div class="panel-title panel-title--sub">
                解析结果
              </div>
              <div class="panel-desc">
                每行一个 IP，可直接复制用于白名单等配置。
              </div>
            </div>
            <div class="panel-head__right">
              <el-button
                text
                :icon="DocumentCopy"
                :disabled="!reverseResult.length"
                @click="copyText(reverseResult.join('\n'))"
              >
                复制
              </el-button>
              <span class="badge badge--muted">共 {{ reverseResult.length }} 个</span>
            </div>
          </div>
          <el-input
            :model-value="reverseResult.join('\n')"
            type="textarea"
            :rows="8"
            readonly
            placeholder="解析结果将显示在此处"
          />
        </el-card>
      </div>
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { DocumentCopy } from '@element-plus/icons-vue';

import { useIpRegexHelperPage } from '@/features/tools/composables/useIpRegexHelperPage';
import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';

const {
  clearAll,
  clearIps,
  converting,
  copyText,
  expanding,
  fillSample,
  handleGenerate,
  handleReverse,
  invalidIps,
  ipInput,
  ipLineCount,
  matchedCount,
  regexInput,
  regexOutput,
  reverseLimit,
  reverseResult,
  useGeneratedRegex,
} = useIpRegexHelperPage();
</script>

<style scoped>
.helper-page {
  padding: var(--oa-spacing-md);
}

.helper-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  align-items: start;
  min-height: 0;
}

.helper-card {
  border-radius: 16px;
  border: 1px solid var(--oa-border-light);
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  min-height: 0;
}

.helper-card :deep(.el-card__header) {
  padding: 12px;
}

.helper-card :deep(.el-card__body) {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.badge {
  background: color-mix(in srgb, var(--oa-color-primary) 10%, var(--oa-bg-panel));
  color: var(--oa-color-primary);
  border-radius: 12px;
  padding: 4px 12px;
  font-size: var(--oa-font-meta);
  white-space: nowrap;
}

.badge--muted {
  background: var(--oa-bg-panel);
  color: var(--oa-text-secondary);
  border: 1px solid var(--oa-border-light);
}

.panel-divider {
  margin: 6px 0 2px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.panel-head__right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.panel-title {
  font-weight: 700;
  color: var(--oa-text-primary);
}

.panel-title--sub {
  font-size: var(--oa-font-subtitle);
}

.panel-desc {
  margin-top: 4px;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.mt-12 {
  margin-top: 12px;
}

.limit-label {
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.hint {
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-meta);
}

@media (max-width: 960px) {
  .helper-page {
    padding: 12px;
  }

  .helper-grid {
    grid-template-columns: 1fr;
  }
}
</style>
